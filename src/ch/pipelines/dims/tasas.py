import polars as pl

from ch.connections import ch_client, mysql_engine
from ch.loading import df_from_ch, insert_df, replace_all
from ch.log import logger
from ch.registry import register

TASAS_X_RIESGO_SQL = """
WITH sinant AS (
    SELECT NumTarifa, Cap, Air,
        anyIf(TasaAnual, CodCobertura = 'C2') AS tasaC2,
        anyIf(TasaAnual, CodCobertura = 'C5') AS tasaC5,
        anyIf(TasaAnual, CodCobertura = 'B5') AS tasaB5,
        anyIf(TasaAnual, CodCobertura = 'C4') AS tasaC4,
        anyIf(TasaAnual, CodCobertura = 'B4') AS tasaB4
    FROM reportes.dim_tasas_actual FINAL
    WHERE NOT (CodCobertura LIKE 'D%')
    GROUP BY NumTarifa, Cap, Air
),
conant AS (
    SELECT NumTarifa, Cap, Air, segmento_ant,
        anyIf(TasaAnual, CodCobertura = 'C2') AS tasaC2,
        anyIf(TasaAnual, CodCobertura = 'C5') AS tasaC5,
        anyIf(TasaAnual, CodCobertura = 'B5') AS tasaB5,
        anyIf(TasaAnual, CodCobertura = 'C4') AS tasaC4,
        anyIf(TasaAnual, CodCobertura = 'B4') AS tasaB4
    FROM reportes.dim_tasas_actual FINAL
    GROUP BY NumTarifa, Cap, Air, segmento_ant
),
parcial AS (
    SELECT t.NumTarifa, t.Cap, t.Air, t.segmento_ant, t.AntMinima, t.AntMaxima,
        t.CodCobertura, t.TasaAnual,
        greatest(c.tasaC2, s.tasaC2) as tasaC2,
        greatest(c.tasaC4, s.tasaC4) as tasaC4,
        greatest(c.tasaC5, s.tasaC5) as tasaC5,
        greatest(c.tasaB4, s.tasaB4) as tasaB4,
        greatest(c.tasaB5, s.tasaB5) as tasaB5
    FROM reportes.dim_tasas_actual AS t FINAL
    LEFT JOIN conant AS c USING (NumTarifa, Cap, Air, segmento_ant)
    LEFT JOIN sinant AS s USING (NumTarifa, Cap, Air)
    WHERE t.TasaAnual BETWEEN 0.01 AND 998
)
SELECT
    NumTarifa, Cap, Air, segmento_ant, AntMinima, AntMaxima, CodCobertura, TasaAnual,
    least(tasaC2, tasaC4, tasaC5, tasaB4, tasaB5) > 0 as Habilitado,
    tasaB4 * It as TasaIt,
    greatest(least(TasaAnual - TasaIt, tasaB5), 0) * Rt AS TasaRt,
    greatest(least(TasaAnual - TasaRt - TasaIt, tasaC2 - tasaC5 - tasaC4), 0) * At AS TasaAt,
    greatest(least(((TasaAnual - TasaRt) - TasaIt) - TasaAt, tasaC4 - tasaB4), 0) * Ip AS TasaIp,
    greatest(
        least(TasaAnual - TasaRt - TasaIt - TasaAt - TasaIp, tasaC5 - tasaB5), 0
    ) * Rp AS TasaRp,
    greatest(TasaAnual - TasaRt - TasaIt - TasaAt - TasaIp - TasaRp, 0) AS TasaAp
FROM parcial
LEFT JOIN reportes.dim_coberturas_aut AS dcob USING (CodCobertura)
"""


@register(
    "dim-tasas",
    "dimensiones",
    "Tasas anuales autos (TasasAnualesHist) -> SCD + actual + tasas x riesgo",
)
def run_tasas() -> None:
    data = pl.read_database(
        "SELECT * FROM TasasAnualesHist",
        connection=mysql_engine(),
        schema_overrides={
            "NumTarifa": pl.UInt32,
            "Cap": pl.UInt32,
            "Air": pl.UInt32,
            "CodCobertura": pl.String,
            "Tasa": pl.Float32,
            "Ant_": pl.UInt32,
            "Min": pl.UInt32,
            "Max": pl.UInt32,
            "Fecha": pl.Date,
        },
    ).select(
        [
            "NumTarifa",
            "Cap",
            "Air",
            "CodCobertura",
            pl.col("Ant_").alias("segmento_ant"),
            pl.col("Min").alias("AntMinima"),
            pl.when(
                pl.col("Ant_")
                == pl.col("Ant_").max().over(["NumTarifa", "Cap", "Air", "CodCobertura"])
            )
            .then(200)
            .otherwise(pl.col("Max"))
            .alias("AntMaxima"),
            pl.col("Tasa").alias("TasaAnual"),
            pl.col("Fecha").alias("fecha_desde"),
        ]
    )

    with ch_client() as ch:
        existing = df_from_ch(ch, "SELECT * FROM dim_tasas_actual")
        if existing.is_empty():
            insert_df(ch, "dim_tasas_scd", data)
        else:
            keys = ["NumTarifa", "Cap", "Air", "CodCobertura", "segmento_ant"]
            joined = data.join(existing, how="inner", on=keys, suffix="_ch")
            cambiada = (
                (pl.col("AntMinima") != pl.col("AntMinima_ch"))
                | (pl.col("AntMaxima") != pl.col("AntMaxima_ch"))
                | (pl.col("TasaAnual") != pl.col("TasaAnual_ch"))
            )
            mas_nueva = pl.col("fecha_desde") > pl.col("fecha_desde_ch")
            updates = joined.filter(cambiada & mas_nueva).select(data.columns)
            nuevas = data.join(existing, how="anti", on=keys)
            insert_df(ch, "dim_tasas_scd", nuevas)
            insert_df(ch, "dim_tasas_scd", updates)

        resumen = df_from_ch(ch, TASAS_X_RIESGO_SQL)
        replace_all(ch, "tasas_aut_x_riesgo", resumen)

    logger.info("dim_tasas + tasas_aut_x_riesgo: LISTO")
