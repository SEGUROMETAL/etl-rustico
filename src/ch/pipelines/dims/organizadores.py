import polars as pl

from ch.connections import ch_client, mysql_engine
from ch.loading import replace_all
from ch.registry import register


@register("dim-organizadores", "dimensiones", "Organizadores (SEHINT01 ININTA=3)")
def run() -> None:
    data = pl.read_database(
        """SELECT ININNA as CodOrganizador,
                  INNRDF as NroPersona,
                  DFNOMB as Nombre,
                  DFDOMI as Domicilio,
                  DFCOPO as Cp,
                  DFCOPS as CpSufijo,
                  LOLOCA as Localidad,
                  LOPROC as CodProvincia,
                  DFTIDO as TipoDoc,
                  DFNRDO as NroDoc,
                  DFCUIT as Cuit,
                  PRPROD as Provincia,
                  PRRPRO as CodInderProvincia,
                  INMATR as Matricula,
                  gr.GPGRUP as CodGrupo,
                  gr.GPNOGR as Grupo
           FROM SEHINT01 s
           LEFT JOIN SETGRJ rel ON s.ININNA = rel.GJINTE
           LEFT JOIN SETGRP gr ON rel.GJGRUP = gr.GPGRUP
           WHERE ININTA = 3 AND DFNOMB <> 'LIBRE'""",
        connection=mysql_engine(),
    )
    data = data.with_columns(
        pl.col("Nombre").str.to_titlecase().str.strip_chars(),
        pl.col("Grupo").str.to_titlecase().str.strip_chars(),
    ).unique()
    with ch_client() as ch:
        replace_all(ch, "dim_organizadores", data)
