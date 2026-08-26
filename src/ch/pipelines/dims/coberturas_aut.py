import polars as pl

from ch.connections import ch_client, mysql_engine
from ch.loading import insert_df
from ch.log import logger
from ch.registry import register


@register("dim-coberturas-aut", "dimensiones", "Coberturas de automotores desde MySQL")
def run() -> None:
    data = pl.read_database(
        """SELECT CodCobertura, OrCobertura, CatCobertura, OrCatCobertura,
                  Rt, Rp, It, Ip, At, Ap
           FROM dims_coberturas_aut""",
        connection=mysql_engine(),
    )
    with ch_client() as ch:
        n = insert_df(ch, "dim_coberturas_aut", data)
    logger.info("dim_coberturas_aut: %s filas", n)
