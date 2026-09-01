import calendar
from datetime import date, timedelta

import polars as pl
from sqlalchemy import text

from ch.connections import ch_client, mysql_engine
from ch.loading import df_from_ch, insert_df, optimize_partitions
from ch.log import logger
from ch.months import ym
from ch.registry import register

TABLA = "vigentes_vehiculos_dia"
INICIO_HISTORICO = date(2025, 2, 3)
KEYS_VV = ["Fecha", "CodRama", "Poliza", "Supl", "Componente"]


def fechas_ya_cargadas(ch) -> set[date]:
    """Fechas distintas presentes en ClickHouse. Usa df_from_ch para no depender
    de la orientación (filas/columnas) del result_set."""
    df = df_from_ch(ch, f"SELECT DISTINCT Fecha FROM {TABLA}")
    if df.is_empty():
        return set()
    return {f for f in df["Fecha"].to_list() if f is not None}


def filtrar_existentes_del_dia(ch, data: pl.DataFrame, fecha: date) -> pl.DataFrame:
    """Anti-join contra las claves ya cargadas en ClickHouse para esa fecha.
    Evita duplicar filas si una corrida anterior quedó cortada a mitad del día."""
    existentes = df_from_ch(
        ch,
        f"SELECT DISTINCT {', '.join(KEYS_VV)} FROM {TABLA} WHERE Fecha = {{fecha:Date}}",
        parameters={"fecha": fecha},
    )
    if existentes.is_empty():
        return data
    return data.join(existentes, how="anti", on=KEYS_VV)


COLUMNAS = [
    "CodOrganizador",
    "CodProductor",
    "CodRama",
    "Poliza",
    "Supl",
    "Componente",
    "FVigDesde",
    "FVigHasta",
    "NroAsegurado",
    "NomAsegurado",
    "CpAsegurado",
    "CpSufijoAsegurado",
    "CodMarca",
    "CodModelo",
    "CodSubModelo",
    "Marca",
    "Modelo",
    "SubModelo",
    "CvaCapitulo",
    "CvaVariante",
    "CvaDescripcion",
    "AnioVehiculo",
    "CodUsoVehiculo",
    "CodTipoVehiculo",
    "CodCoberturaAut",
    "SumaAsegurada",
    pl.col("NroMotor").str.strip_chars(),
    pl.col("NroChasis").str.strip_chars(),
    "Origen",
    "NroPersonaPagador",
    "NroPersonaTomador",
    "CodCarroceria",
    "NomProductor",
    "DomicilioProductor",
    "CpProductor",
    "CpSufijoProductor",
    "LocalidadProductor",
    "CodProvinciaProductor",
    "ProvinciaProductor",
    "CodProvinciaInderProductor",
    "MatriculoProductor",
    "CodGrupoOrganizador",
    "GrupoOrganizador",
    "TarifaMadreLetra",
    "TarifaHija",
    pl.col("Dominio").str.strip_chars(),
    "Ant",
    "Fecha",
]


def _extraer_dia(cn, engine, fecha: date) -> pl.DataFrame | None:
    existe = cn.execute(
        text("SELECT Poliza FROM vigentes_vehiculos_dia WHERE Fecha = :fecha LIMIT 1"),
        {"fecha": fecha},
    ).fetchone()
    if existe is None:
        return None
    return pl.read_database(
        "SELECT * FROM vigentes_vehiculos_dia WHERE Fecha = :fecha",
        connection=engine,
        execute_options={"parameters": {"fecha": fecha}},
    ).select(COLUMNAS)


@register(
    "fact-vv",
    "hechos",
    "Snapshot diario de vehículos vigentes, incremental por día",
)
def run(
    desde: str | None = None,
    hasta: str | None = None,
    anio: int | None = None,
) -> None:
    engine = mysql_engine()
    if desde is not None:
        inicio = date.fromisoformat(desde)
    elif anio is not None:
        inicio = date(anio, 1, 1)
    else:
        inicio = INICIO_HISTORICO
    fin = date.fromisoformat(hasta) if hasta else date.today()

    with engine.connect() as cn, ch_client() as ch:
        fechas_existentes: set[date] = fechas_ya_cargadas(ch)
        logger.info("vv: %s fechas ya cargadas en ClickHouse", len(fechas_existentes))

        fecha = inicio
        cargados: list[date] = []
        while fecha < fin:
            fecha += timedelta(1)
            if fecha in fechas_existentes:
                continue

            data = _extraer_dia(cn, engine, fecha)
            if data is None:
                logger.warning("vv %s: no existe en MySQL; se saltea", fecha)
                continue
            if data.is_empty():
                continue

            nuevas = filtrar_existentes_del_dia(ch, data, fecha)
            if nuevas.is_empty():
                logger.info("vv %s: ya estaba completo; nada para insertar", fecha)
                continue

            insert_df(ch, TABLA, nuevas)
            cargados.append(fecha)
            logger.info(
                "vv %s: %s filas (%s ya existían)",
                fecha,
                len(nuevas),
                len(data) - len(nuevas),
            )

        if cargados:
            optimize_partitions(ch, TABLA, "Fecha", pl.DataFrame({"Fecha": cargados}))

        resumen = ch.query(
            "SELECT Mes, Minimo, Maximo, Promedio, Gap, Std "
            "FROM v_vv_diaria_resumen_mensual ORDER BY Mes DESC",
            column_oriented=True,
        )
        df_res = pl.from_dict(
            {
                k: v
                for k, v in zip(resumen.column_names, resumen.result_set, strict=False)
            },
            strict=False,
        )
        logger.info("Resumen mensual vv:\n%s", df_res)


@register(
    "fact-vv-reload-mes",
    "hechos",
    "Recarga completa un mes de vehículos vigentes (AAAA-MM)",
)
def run_reload_mes(mes: str) -> None:
    anio, mes_n = (int(x) for x in mes.split("-"))
    engine = mysql_engine()

    with engine.connect() as cn, ch_client() as ch:
        ch.command(f"ALTER TABLE {TABLA} DROP PARTITION {ym(anio, mes_n)}")
        logger.info("vv: partición %s eliminada; recargando...", mes)

        total = 0
        for dia in range(1, calendar.monthrange(anio, mes_n)[1] + 1):
            data = _extraer_dia(cn, engine, date(anio, mes_n, dia))
            if data is None or data.is_empty():
                continue
            insert_df(ch, TABLA, data)
            total += len(data)
            logger.info("vv %s-%02d-%02d: %s filas", anio, mes_n, dia, len(data))

    logger.info("vv %s: recargado completo (%s filas)", mes, total)
