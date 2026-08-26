import polars as pl

from ch.connections import ch_client, mysql_engine
from ch.loading import replace_all
from ch.log import logger
from ch.registry import register


@register("dim-coberturas-rv", "dimensiones", "Coberturas de ramas varias desde MySQL")
def run() -> None:
    data = pl.read_database(
        """SELECT CodRama, CodCobertura, Cobertura, Pormilaje, Informe
           FROM dims_coberturas_rv""",
        connection=mysql_engine(),
        schema_overrides={
            "CodRama": pl.UInt32,
            "CodCobertura": pl.UInt32,
            "Cobertura": pl.String,
            "Pormilaje": pl.Float32,
            "Informe": pl.String,
        },
    )
    if data.is_empty():
        logger.warning("No hay coberturas RV en MySQL; no se modifica la tabla.")
        return
    with ch_client() as ch:
        replace_all(ch, "dim_coberturas_rv", data)
