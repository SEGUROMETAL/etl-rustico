import polars as pl

from ch.connections import ch_client, mysql_engine
from ch.loading import replace_all
from ch.registry import register


@register("dim-productores", "dimensiones", "Productores (SEHINT01 ININTA=4)")
def run() -> None:
    data = pl.read_database(
        """SELECT ININNA as CodProductor,
                  INNRDF as NroPersonaProductor,
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
                  INMATR as Matricula
           FROM SEHINT01
           WHERE ININTA = 4 AND DFNOMB <> 'LIBRE'""",
        connection=mysql_engine(),
    ).unique()
    with ch_client() as ch:
        replace_all(ch, "dim_productores", data)
