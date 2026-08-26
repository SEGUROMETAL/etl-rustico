from datetime import date, timedelta

import polars as pl

from ch.connections import ch_client
from ch.loading import df_from_ch


def _query(query: str, parameters: dict) -> pl.DataFrame:
    with ch_client() as ch:
        return df_from_ch(ch, query, parameters)


def df_vv(fecha: date) -> pl.DataFrame:
    """Vehículos vigentes en ClickHouse para una fecha."""
    return _query(
        """SELECT
            vvd.TarifaHija as NumTarifa,
            vvd.CodRama,
            vvd.Poliza,
            vvd.Componente as Comp,
            vvd.CodCoberturaAut as CodCobertura,
            vvd.Ant,
            vvd.CvaCapitulo,
            vvd.CvaVariante
        FROM vigentes_vehiculos_dia vvd
        WHERE Fecha = {fecha:Date}
          AND CodCoberturaAut <> 'A2'""",
        {"fecha": fecha},
    )


def df_primas_automotores(fecha: date, dias: int) -> pl.DataFrame:
    """Primas de automotores agrupadas por póliza/componente en una ventana de días."""
    return _query(
        """SELECT
            CodRama,
            Poliza,
            Comp,
            argMax(Cap, Supl) as Cap,
            argMax(Var, Supl) as Var,
            argMax(Air, Supl) as Air,
            argMax(SaComponente, Supl) as Sa,
            sum(PrimaCascoNetaComp) as PrimaNeta
        FROM primas_automotores
        WHERE FEmision BETWEEN {fecha_desde:Date} AND {fecha:Date}
        GROUP BY CodRama, Poliza, Comp""",
        {"fecha_desde": fecha - timedelta(dias), "fecha": fecha},
    )


def df_tasas_automotores() -> pl.DataFrame:
    return _query(
        "SELECT * FROM tasas_aut_x_riesgo WHERE TasaAnual BETWEEN {mi:Float} AND {ma:Float}",
        {"mi": 0.5, "ma": 998.9},
    )


def _resumen_dif(dif: pl.DataFrame, mensaje: str) -> dict[str, object]:
    if dif.is_empty():
        return {"mensaje": mensaje, "sample": ""}
    largo = len(dif)
    sample = dif if largo <= 5 else dif.sample()
    return {"mensaje": f"{mensaje}: {largo}", "sample": str(sample.to_dicts())}


def faltantes_vv_vs_primas(vv: pl.DataFrame, primas: pl.DataFrame) -> dict[str, object]:
    dif = vv.join(primas, how="anti", on=["CodRama", "Poliza", "Comp"])
    return _resumen_dif(dif, "Vehículos vigentes sin primas")


def faltantes_vv_primas_vs_tasas(
    vv_primas: pl.DataFrame, tasas: pl.DataFrame
) -> dict[str, object]:
    dif = vv_primas.join(
        tasas, how="anti", on=["NumTarifa", "Cap", "Air", "CodCobertura"]
    )
    return _resumen_dif(dif, "Primas de vehículos vigentes sin tasas")


def df_vv_primas(fecha: date, dias: int) -> pl.DataFrame:
    vv = df_vv(fecha)
    primas = df_primas_automotores(fecha, dias)
    return vv.join(primas, how="inner", on=["CodRama", "Poliza", "Comp"]).with_columns(
        pl.col("NumTarifa").replace({0: 11})
    )


def df_resultado(vv_primas: pl.DataFrame, tasas: pl.DataFrame) -> pl.DataFrame:
    base = vv_primas.join(
        tasas, how="inner", on=["NumTarifa", "Cap", "Air", "CodCobertura"]
    ).filter(pl.col("Ant").is_between(pl.col("AntMinima"), pl.col("AntMaxima")))
    return (
        base.select(
            [
                "NumTarifa",
                "CodRama",
                "Poliza",
                "Comp",
                "CodCobertura",
                "Ant",
                "Sa",
                "PrimaNeta",
                "TasaAnual",
                (pl.col("TasaRt") * pl.col("PrimaNeta") / pl.col("TasaAnual")).alias("Rt"),
                (pl.col("TasaIt") * pl.col("PrimaNeta") / pl.col("TasaAnual")).alias("It"),
                (pl.col("TasaRp") * pl.col("PrimaNeta") / pl.col("TasaAnual")).alias("Rp"),
                (pl.col("TasaIp") * pl.col("PrimaNeta") / pl.col("TasaAnual")).alias("Ip"),
                (pl.col("TasaAt") * pl.col("PrimaNeta") / pl.col("TasaAnual")).alias("At"),
                (pl.col("TasaAp") * pl.col("PrimaNeta") / pl.col("TasaAnual")).alias("Ap"),
            ]
        )
        .with_columns(
            [
                (pl.col("Rt") + pl.col("It") + pl.col("At")).alias("Total"),
                (pl.col("Rp") + pl.col("Ip") + pl.col("Ap")).alias("Parcial"),
                (pl.col("Rt") + pl.col("Rp")).alias("Robo"),
                (pl.col("It") + pl.col("Ip")).alias("Incendio"),
                (pl.col("At") + pl.col("Ap")).alias("Accidente"),
            ]
        )
    )
