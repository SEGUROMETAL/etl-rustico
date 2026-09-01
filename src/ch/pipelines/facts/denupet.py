from datetime import date

import polars as pl

from ch.connections import ch_client, mysql_engine
from ch.loading import load_incremental
from ch.log import logger
from ch.months import iter_months
from ch.registry import register

OVERRIDES = {
    "Op": pl.UInt32,
    "CodRama": pl.UInt32,
    "Poliza": pl.UInt32,
    "Supl": pl.UInt32,
    "Comp": pl.UInt32,
    "Siniestro": pl.UInt32,
    "FechaDenuncia": pl.Date,
    "FechaSiniestro": pl.Date,
    "CodCausa": pl.UInt32,
    "Causa": pl.String,
    "DireccionSiniestro": pl.String,
    "CpSiniestro": pl.UInt32,
    "CodOrganizador": pl.UInt32,
    "CodProductor": pl.UInt32,
    "NroAsegurado": pl.UInt32,
}

QUERY = """SELECT
        DPOPER as Op,
        DCRAMA as CodRama,
        POPOLI as Poliza,
        POPOSP as Supl,
        DPPOCO as Comp,
        DCSINI as Siniestro,
        FEDENU as FechaDenuncia,
        FESINI as FechaSiniestro,
        DCCAUC as CodCausa,
        TACAUD as Causa,
        DCLUDI as DireccionSiniestro,
        DCCOPO as CpSiniestro,
        POORG1 as CodOrganizador,
        POPRO1 as CodProductor,
        POASEN as NroAsegurado
    FROM DenuPe
    WHERE Year(FEDENU) = {a} AND Month(FEDENU) = {m}"""


@register("fact-denupet", "hechos", "Denuncias de siniestros (DenuPe), incremental mensual")
def run(anio: int = 2025) -> None:
    engine = mysql_engine()
    keys = ["Op", "Siniestro", "Comp"]
    with ch_client() as ch:
        for a, m in iter_months(date(anio, 1, 1)):
            data = pl.read_database(
                QUERY.format(a=a, m=m),
                connection=engine,
                schema_overrides=OVERRIDES,
            )
            if data.is_empty():
                continue
            n = load_incremental(ch, "denupet", data, keys, "FechaDenuncia")
            logger.info("denupet %s-%02d: %s filas nuevas", a, m, n)
