import polars as pl

from ch.connections import ch_client, mysql_engine
from ch.loading import df_from_ch, insert_df
from ch.log import logger
from ch.registry import register


@register(
    "dim-rcs",
    "dimensiones",
    "RC anuales históricos (RcsAnualesHist) -> dim_rc_scd + dim_rc_actual",
)
def run() -> None:
    data = (
        pl.read_database(
            "SELECT * FROM RcsAnualesHist",
            connection=mysql_engine(),
            schema_overrides={
                "NumTarifa": pl.UInt32,
                "Cap": pl.UInt32,
                "Var": pl.UInt32,
                "RcSl": pl.Float32,
                "RcCl": pl.Float32,
                "RcExt": pl.Float32,
                "RcAp": pl.Float32,
                "RcObl": pl.Float32,
                "Fecha": pl.Date,
            },
        )
        .with_columns(pl.col("Fecha").alias("fecha_desde"))
        .select(pl.exclude("Fecha"))
    )

    with ch_client() as ch:
        existing = df_from_ch(ch, "SELECT * FROM dim_rc_actual")
        if existing.is_empty():
            to_load = data
        else:
            joined = data.join(
                existing, how="left", on=["NumTarifa", "Cap", "Var"], suffix="_ch"
            )
            es_nueva = pl.col("NumTarifa_ch").is_null()
            cambiada = (
                (pl.col("RcSl") != pl.col("RcSl_ch"))
                | (pl.col("RcCl") != pl.col("RcCl_ch"))
                | (pl.col("RcExt") != pl.col("RcExt_ch"))
                | (pl.col("RcAp") != pl.col("RcAp_ch"))
                | (pl.col("RcObl") != pl.col("RcObl_ch"))
            )
            to_load = joined.filter(es_nueva | cambiada).select(data.columns)
        n = insert_df(ch, "dim_rc_scd", to_load)
    logger.info("dim_rc_scd: %s filas nuevas/cambiadas", n)
