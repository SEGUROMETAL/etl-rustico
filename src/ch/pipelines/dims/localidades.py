import polars as pl

from ch.connections import ch_client, mysql_engine
from ch.loading import replace_all
from ch.registry import register


@register("dim-localidades", "dimensiones", "Localidades y provincias (GNTLOC/GNTPRO)")
def run() -> None:
    data = pl.read_database(
        """SELECT l.LOCOPO as Cp,
                  l.LOCOPS as CpSufijo,
                  l.LOLOCA as Localidad,
                  l.LOPROC as CodProvinciaStr,
                  p.PRRPRO as CodProvInder,
                  p.PRPROD as Provincia
           FROM GNTLOC l
           LEFT JOIN GNTPRO p ON l.LOPROC = p.PRPROC""",
        connection=mysql_engine(),
    ).with_columns(
        pl.col("Localidad").str.to_titlecase().str.strip_chars(),
        pl.col("Provincia").str.to_titlecase().str.strip_chars(),
    )
    with ch_client() as ch:
        replace_all(ch, "dim_localidades", data)
