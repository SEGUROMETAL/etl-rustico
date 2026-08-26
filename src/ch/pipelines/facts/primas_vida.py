from datetime import date

import polars as pl

from ch.connections import ch_client
from ch.loading import load_incremental
from ch.log import logger
from ch.months import iter_months
from ch.paths import PRIMAS_VIDA_CSV
from ch.registry import register

KEYS = ["Op", "Suplemento", "Componente", "CodCobertura"]
TABLE = "primas_vida"

COLUMNAS_CSV = {
    "NUMERO DE OPERACION": ("Op", pl.Int64),
    "CODIGO DE RAMA DE SEGURO": ("CodRama", pl.Int64),
    "NUMERO DE LA POLIZA": ("Poliza", pl.Int64),
    "SUPLEMENTO DE LA OPERACION": ("Suplemento", pl.Int64),
    "NUMERO DE COMPONENTE": ("Componente", pl.Int64),
    "CODIGO DE RIESGO": ("CodRiesgo", pl.Int64),
    "DESCRIPCION DEL RIESGO": ("Riesgo", pl.String),
    "CODIGO DE COBERTURA": ("CodCobertura", pl.Int64),
    "DESCRIPCION DE LA COBERTURA": ("Cobertura", pl.String),
    "NUMERO DE INTERMEDIARIO": ("CodOrganizador", pl.Int64),
    "NUMERO DE INTERMEDIARIO_duplicated_0": ("CodProductor", pl.Int64),
    "FEC_EMI": ("FEmision", pl.Date),
    "VIG_DESDE": ("FVigDesde", pl.Date),
    "VIG_HASTA": ("FVigHasta", pl.String),
    "SUMA ASEGURADA X SUPLEMENTO": ("SaSuplemento", pl.Float64),
    "DATOS FILATORIOS NOMBRE": ("NomAsegurado", pl.String),
    "C.U.I.T.": ("CuitAsegurado", pl.String),
    "CODIGO POSTAL": ("Cp", pl.String),
    "SUFIJO DEL CODIGO POSTAL": ("CpSufijo", pl.String),
    "LOCALIDAD": ("Localidad", pl.String),
    "CODIGO DE PROVINCIA": ("CodProvincia", pl.String),
    "PORMILAJE DE PRIMA": ("PormilajeCobertura", pl.Float64),
    "PRIMA POR COBERTURA": ("PrimaTarifaCobertura", pl.Float64),
    "PRIMA DE TARIFA": ("PrimaTarifaSuplemento", pl.Float64),
    "% BONIFICACION SOBRE PRIMA": ("PctBonPrima", pl.Float64),
    "PREMIO BRUTO": ("PremioSuplemento", pl.Float64),
    "DESCRIPCION DE LA OPERACION": ("DescOperacion", pl.String),
    "POLIZA ANTERIOR": ("PolizaAnterior", pl.Int64),
    "POLIZA POSTERIOR": ("PolizaPosterior", pl.Int64),
}


@register(
    "fact-primas-vida",
    "hechos",
    "Primas de vida desde CSV mainframe (R94959699OpEmVIDA.csv)",
)
def run() -> None:
    renamecols = {k: v[0] for k, v in COLUMNAS_CSV.items()}
    schema = {k: v[1] for k, v in COLUMNAS_CSV.items()}
    data = (
        pl.read_csv(
            PRIMAS_VIDA_CSV,
            separator=";",
            decimal_comma=True,
            encoding="latin1",
            schema_overrides=schema,
        )
        .select([pl.col(k).alias(v) for k, v in renamecols.items()])
        .with_columns(
            [
                (
                    pl.col("PrimaTarifaSuplemento") * (100 - pl.col("PctBonPrima"))
                ).alias("PrimaNetaSuplemento"),
                (
                    pl.col("PrimaTarifaCobertura") * (100 - pl.col("PctBonPrima"))
                ).alias("PrimaNetaCobertura"),
            ]
        )
    )
    if data.is_empty():
        logger.warning("CSV de vida vacío; nada para cargar.")
        return

    min_fecha: date = data["FEmision"].min()
    with ch_client() as ch:
        for a, m in iter_months(min_fecha):
            chunk = data.filter(
                (pl.col("FEmision").dt.year() == a) & (pl.col("FEmision").dt.month() == m)
            )
            if chunk.is_empty():
                continue
            n = load_incremental(ch, TABLE, chunk, KEYS, "FEmision")
            logger.info("primas_vida %s-%02d: %s filas nuevas", a, m, n)
