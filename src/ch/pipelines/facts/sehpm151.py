from datetime import date

import polars as pl

from ch.connections import ch_client, mysql_engine
from ch.loading import load_incremental
from ch.log import logger
from ch.months import iter_months
from ch.registry import register

OVERRIDES = {
    "Op": pl.UInt32,
    "Suplemento": pl.UInt32,
    "CodTipoOp": pl.UInt32,
    "CodSubTipoOp": pl.UInt32,
    "PlVidaNvaRen": pl.UInt32,
    "CodRama": pl.UInt32,
    "Poliza": pl.UInt32,
    "NroAsegurado": pl.UInt32,
    "CpAsegurado": pl.UInt32,
    "CpSufijoAsegurado": pl.UInt32,
    "NombreAsegurado": str,
    "LocalidadAsegurado": str,
    "ProvinciaAsegurado": str,
    "CodOrganizador": pl.UInt32,
    "CodProductor": pl.UInt32,
    "SumaAsegurada": pl.Float64,
    "PrimaNeta": pl.Float64,
    "RecFin": pl.Float64,
    "RecAdm": pl.Float64,
    "DerEmision": pl.Float64,
    "SellRiesgo": pl.Float64,
    "ImpInt": pl.Float64,
    "ServSoc": pl.Float64,
    "TasaSsn": pl.Float64,
    "Iva": pl.Float64,
    "IvaPercepcion": pl.Float64,
    "IvaRespNoInscr": pl.Float64,
    "BonifPrima": pl.Float64,
    "Acc": pl.Float64,
    "RecCapital": pl.Float64,
    "FEmision": pl.Date,
    "FVigDesde": pl.Date,
    "FVigHasta": str,
    "PrimaTarifa": pl.Float64,
    "PremioBruto": pl.Float64,
    "CodOrganizadorComision": pl.UInt32,
    "ComOrganizador": pl.Float64,
    "CodProductorComision": pl.UInt32,
    "ComProductor": pl.Float64,
}

QUERY = """SELECT
    M1OPER as Op,
    M1SUOP as Suplemento,
    M1TIOU as CodTipoOp,
    M1STOU as CodSubTipoOp,
    M1PVNR as PlVidaNvaRen,
    M1RAMA as CodRama,
    M1POLI as Poliza,
    M1ASEN as NroAsegurado,
    M1COPOA as CpAsegurado,
    M1COPSA as CpSufijoAsegurado,
    M1NOMBA as NombreAsegurado,
    M1NOLOA as LocalidadAsegurado,
    M1PRLOA as ProvinciaAsegurado,
    M1ORG1 as CodOrganizador,
    M1PRO1 as CodProductor,
    MASAOP as SumaAsegurada,
    MAPRIM as PrimaNeta,
    MAREFI as RecFin,
    MAREAD as RecAdm,
    MADERE as DerEmision,
    MASERI as SellRiesgo,
    MAIMPI as ImpInt,
    MASERS as ServSoc,
    MATSSN as TasaSsn,
    MAIPR1 as Iva,
    MAIPR3 as IvaPercepcion,
    MAIPR4 as IvaRespNoInscr,
    MABPRI as BonifPrima,
    MAIPR2 as Acc,
    MAIPR5 as RecCapital,
    DATE(CONCAT(M1FEMA, '-', M1FEMM, '-', M1FEMD)) as FEmision,
    DATE(CONCAT(M1FIOA, '-', M1FIOM, '-', M1FIOD)) as FVigDesde,
    CONCAT(M1FVOA, '-', M1FVOM, '-', M1FVOD) as FVigHasta,
    MAPRIM + MABPRI AS PrimaTarifa,
    MAIPR5 + MAPREM as PremioBruto,
    CodIntOrg as CodOrganizadorComision,
    ComOrg as ComOrganizador,
    CodIntProd as CodProductorComision,
    ComProd as ComProductor
FROM SEHPM151T sh
WHERE M1FEMA = {a} AND M1FEMM = {m}"""


@register(
    "fact-sehpm151",
    "hechos",
    "Emisión de operaciones (SEHPM151T), incremental mensual",
)
def run(anio: int = 2025) -> None:
    engine = mysql_engine()
    keys = ["Op", "Suplemento"]
    with ch_client() as ch:
        for a, m in iter_months(date(anio, 1, 1)):
            data = (
                pl.read_database(
                    QUERY.format(a=a, m=m),
                    connection=engine,
                    schema_overrides=OVERRIDES,
                )
                .with_columns(pl.col("FVigHasta").str.to_date("%Y-%m-%d", strict=False))
                .with_columns(
                    pl.col("CodOrganizador").replace({3873: 9105}),
                    pl.col("CodProductor").replace({9105: 3873}),
                )
            )
            if data.is_empty():
                continue
            n = load_incremental(ch, "sehpm151t", data, keys, "FEmision")
            logger.info("sehpm151t %s-%02d: %s filas nuevas", a, m, n)
