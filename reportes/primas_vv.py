from datetime import date, timedelta


import polars as pl


from db.engines import get_client_ch


def df_from_ch(q: str, parametros: dict) -> pl.DataFrame:
    with get_client_ch() as ch:
        result = ch.query(query=q, parameters=parametros, column_oriented=True)
        return pl.DataFrame(
            {name: col for name, col in zip(result.column_names, result.result_set)}
        )


def df_vv(fecha: date) -> pl.DataFrame:
    """Dataframe de vehículos Vigentes alojado en ClikHouse"""
    q = """SELECT
            vvd.TarifaHija as NumTarifa,
            vvd.CodRama ,
            vvd.Poliza ,
            vvd.Componente as Comp,
            vvd.CodCoberturaAut as CodCobertura ,
            vvd.Ant ,
            vvd.CvaCapitulo,
            vvd.CvaVariante
        FROM
            vigentes_vehiculos_dia vvd
        WHERE
            Fecha = {fecha:Date}
            and CodCoberturaAut <> 'A2'
            ;"""
    parameters = {"fecha": fecha}
    return df_from_ch(q, parameters)


def df_primas_automotores(fecha: date, dias: int) -> pl.DataFrame:
    """Dataframe de Primas de automotores alojado en ClikHouse.

    - Agrupa por Póliza/Componente y trae el último Cap, Var, Air, SumaAsegurada del compoennete.
    - Suma la PrimaCascoNetaComp
    """
    q: str = """Select
                    CodRama,
                    Poliza,
                    Comp,
                    argMax(Cap, Supl) as Cap,
                    argMax(Var, Supl) as Var,
                    argMax(Air, Supl) as Air,
                    argMax(SaComponente, Supl) as Sa,
                    sum(PrimaCascoNetaComp) as PrimaNeta
                from
                    primas_automotores
                Where
                    FEmision between {fecha_desde:Date} and {fecha:Date}
                group by
                    CodRama,
                    Poliza,
                    Comp;"""
    parameters = {"fecha_desde": fecha - timedelta(dias), "fecha": fecha}
    return df_from_ch(q, parameters)


def df_tasas_automotores() -> pl.DataFrame:
    """Dataframe de tasas de automotores alojado en ClikHouse"""
    q = """Select *
        from tasas_aut_x_riesgo
        Where TasaAnual between {mi:Float} and {ma:Float};"""
    parameters: dict = {"mi": 0.5, "ma": 998.9}
    return df_from_ch(q, parameters)


def faltantes_vv_vs_primas(vv: pl.DataFrame, primas: pl.DataFrame) -> dict[str, any]:
    """Vehículos Vigentes no encontrados en Primas"""
    dif = vv.join(primas, how="anti", on=["CodRama", "Poliza", "Comp"])

    if dif.is_empty():
        return {
            "mensaje": "Todos los vehículos con Primas",
            "sample": "",
        }

    largo = len(dif)
    if 0 > largo <= 5:
        return {
            "mensaje": f"Vehículos no encontrados en Primas: {largo}",
            "sample": str(dif.to_dicts()),
        }

    else:
        return {
            "mensaje": f"Vehículos no encontrados en Primas: {largo}",
            "sample": str(dif.sample().to_dicts()),
        }


def df_vv_primas(fecha: date, dias: int) -> pl.DataFrame:
    """Devuelve el inner join entre vv y primas"""
    vv = df_vv(fecha)
    primas = df_primas_automotores(fecha, dias)
    return vv.join(primas, how="inner", on=["CodRama", "Poliza", "Comp"]).with_columns(
        pl.col("NumTarifa").replace(0, 11)
    )


def faltantes_vv_primas_vs_tasas(
    vv_primas: pl.DataFrame,
    tasas: pl.DataFrame,
) -> dict[str, any]:
    """Primas de los vehículos vigentes no encontradas en Tasas."""
    dif = vv_primas.join(
        tasas,
        how="anti",
        on=["NumTarifa", "Cap", "Air", "CodCobertura"],
    )

    if dif.is_empty():
        return {
            "mensaje": "Todos los vehículos con Primas",
            "sample": "",
        }

    largo = len(dif)

    if largo <= 5:
        return {
            "mensaje": f"Vehículos no encontrados en Primas: {largo}",
            "sample": str(dif.to_dicts()),
        }
    else:
        return {
            "mensaje": f"Vehículos no encontrados en Primas: {largo}",
            "sample": str(dif.sample().to_dicts()),
        }


def df_resultado(vv_primas: pl.DataFrame, tasas: pl.DataFrame) -> pl.DataFrame:
    """Resultado de los joins"""
    return (
        vv_primas.join(
            tasas,
            how="inner",
            on=["NumTarifa", "Cap", "Air", "CodCobertura"],
        )
        .filter(pl.col("Ant").is_between(pl.col("AntMinima"), pl.col("AntMaxima")))
        .select(
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
                (pl.col("TasaRt") * pl.col("PrimaNeta") / pl.col("TasaAnual")).alias(
                    "Rt"
                ),
                (pl.col("TasaIt") * pl.col("PrimaNeta") / pl.col("TasaAnual")).alias(
                    "It"
                ),
                (pl.col("TasaRp") * pl.col("PrimaNeta") / pl.col("TasaAnual")).alias(
                    "Rp"
                ),
                (pl.col("TasaIp") * pl.col("PrimaNeta") / pl.col("TasaAnual")).alias(
                    "Ip"
                ),
                (pl.col("TasaAt") * pl.col("PrimaNeta") / pl.col("TasaAnual")).alias(
                    "At"
                ),
                (pl.col("TasaAp") * pl.col("PrimaNeta") / pl.col("TasaAnual")).alias(
                    "Ap"
                ),
            ]
        )
    ).with_columns(
        [
            (pl.col("Rt") + pl.col("It") + pl.col("At")).alias("Total"),
            (pl.col("Rp") + pl.col("Ip") + pl.col("Ap")).alias("Parcial"),
            (pl.col("Rt") + pl.col("Rp")).alias("Robo"),
            (pl.col("It") + pl.col("Ip")).alias("Incendio"),
            (pl.col("At") + pl.col("Ap")).alias("Accidente"),
        ]
    )
