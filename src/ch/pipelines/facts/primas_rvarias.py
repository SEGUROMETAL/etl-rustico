
import polars as pl

from ch.connections import ch_client, mysql_engine
from ch.loading import load_incremental
from ch.log import logger
from ch.months import iter_months, resolve_fin, resolve_inicio
from ch.paths import PRIMAS_RVARIAS_CSV
from ch.registry import register

KEYS = ["Op", "Supl", "Comp", "CodCobertura"]
TABLE = "primas_rvarias"

COLUMNAS_CSV = {
    "FEC_EMI": ("FEmision", pl.Date),
    "VIG_DESDE": ("FVigDesde", pl.Date),
    "VIG_HASTA": ("FVigHasta", str),
    "NUMERO DE OPERACION": ("Op", int),
    "CODIGO DE RAMA DE SEGURO": ("CodRama", int),
    "NUMERO DE LA POLIZA": ("Poliza", int),
    "SUPLEMENTO DE LA OPERACION": ("Supl", int),
    "NUMERO DE COMPONENTE": ("Comp", int),
    "NUMERO DE INTERMEDIARIO": ("CodOrganizador", int),
    "NUMERO DE INTERMEDIARIO_duplicated_0": ("CodProductor", int),
    "CODIGO DE RIESGO": ("CodRiesgo", int),
    "DESCRIPCION DEL RIESGO": ("Riesgo", str),
    "CODIGO DE COBERTURA": ("CodCobertura", int),
    "DESCRIPCION DE LA COBERTURA": ("Cobertura", str),
    "CODIGO DE PROVINCIA": ("CodProvincia", str),
    "SUMA ASEGURADA POR COBERTURA": ("SaCobertura", pl.Float32),
    "PREMIO BRUTO": ("PremioBrutoSuplemento", pl.Float32),
    "% BONIFICACION SOBRE PRIMA": ("BonPrimaPorc", pl.Float32),
    "PORMILAJE DE PRIMA": ("Pormilaje", pl.Float32),
    "PRIMA DE TARIFA": ("PrimaTarifaSuplemento", pl.Float32),
    "PRIMA POR COBERTURA": ("PrimaTarifaCobertura", pl.Float32),
}


@register(
    "fact-primas-rvarias-mysql",
    "hechos",
    "Primas ramas varias desde MySQL, incremental mensual",
)
def run_mysql(
    anio: int | None = None,
    desde: str | None = None,
    hasta: str | None = None,
) -> None:
    engine = mysql_engine()
    inicio = resolve_inicio(desde, anio, default_year=2025)
    fin = resolve_fin(hasta)
    with ch_client() as ch:
        for a, m in iter_months(inicio, fin):
            data = pl.read_database(
                f"SELECT * FROM primas_ramas_varias "
                f"WHERE Year(FEmision) = {a} AND Month(FEmision) = {m}",
                connection=engine,
                schema_overrides={"FVigHasta": pl.String},
            ).select(
                [
                    "FEmision",
                    "FVigDesde",
                    pl.col("FVigHasta").str.to_date("%d/%m/%Y", strict=False),
                    "Op",
                    "CodRama",
                    "Poliza",
                    "Supl",
                    "Comp",
                    "CodOrganizador",
                    "CodProductor",
                    "CodRiesgo",
                    "Riesgo",
                    "CodCobertura",
                    "Cobertura",
                    "CodProvincia",
                    "SaCobertura",
                    pl.col("PremioBrutoSupl").alias("PremioBrutoSuplemento"),
                    "Pormilaje",
                    pl.col("PrimaTarifaSupl").alias("PrimaTarifaSuplemento"),
                    pl.col("PrimaCoberturaEmitida").alias("PrimaTarifaCobertura"),
                    pl.col("PrimaNetaSupl").alias("PrimaNetaSuplemento"),
                    pl.col("PrimaCoberturaNeta").alias("PrimaNetaCobertura"),
                ]
            )
            if data.is_empty():
                continue
            n = load_incremental(ch, TABLE, data, KEYS, "FEmision")
            logger.info("primas_rvarias %s-%02d: %s filas nuevas", a, m, n)


@register(
    "fact-primas-rvarias-csv",
    "hechos",
    "Primas ramas varias desde CSV mainframe (RVariasOpEmTodas.csv)",
)
def run_csv(
    desde: str | None = None,
    hasta: str | None = None,
    anio: int | None = None,
) -> None:
    _ = (anio, desde, hasta)  # compat CLI; el CSV siempre trae su propio rango
    renamecols = {k: v[0] for k, v in COLUMNAS_CSV.items()}
    schema = {k: v[1] for k, v in COLUMNAS_CSV.items()}
    data = (
        pl.read_csv(
            PRIMAS_RVARIAS_CSV,
            separator=";",
            decimal_comma=True,
            encoding="latin1",
            schema_overrides=schema,
        )
        .select([pl.col(k).alias(v) for k, v in renamecols.items()])
        .with_columns(pl.col("FVigHasta").str.to_date("%d/%m/%Y", strict=False))
        .with_columns(
            [
                (pl.col("PrimaTarifaSuplemento") * (100 - pl.col("BonPrimaPorc") / 100)).alias(
                    "PrimaNetaSuplemento"
                ),
                (pl.col("PrimaTarifaCobertura") * (100 - pl.col("BonPrimaPorc") / 100)).alias(
                    "PrimaNetaCobertura"
                ),
            ]
        )
    )
    with ch_client() as ch:
        n = load_incremental(ch, TABLE, data, KEYS, "FEmision")
    logger.info("primas_rvarias (csv): %s filas nuevas en total", n)
