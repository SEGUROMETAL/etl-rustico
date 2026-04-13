from etl.etl_constantes import TABLA_TASAS_ANUALES
import polars as pl
import db


def update_tasas_discriminadas():
    print("\nActualizar tAsas x Riesgo")

    with db.get_client_ch() as ch:
        create = """
            CREATE TABLE IF NOT EXISTS tasas_aut_x_riesgo (
                NumTarifa UInt32,
                Cap UInt32,
                Air UInt32,
                segmento_ant UInt32,
                AntMinima Int32,
                AntMaxima Int32,
                CodCobertura LowCardinality(String),
                TasaAnual Float64,
                Habilitado UInt16,
                TasaIt Float64,
                TasaRt Float64,
                TasaAt Float64,
                TasaIp Float64,
                TasaRp Float64,
                TasaAp Float64
            ) Engine = MergeTree()
            ORDER BY
                (
                    NumTarifa,
                    Cap,
                    Air,
                    segmento_ant,
                    CodCobertura,
                    AntMinima,
                    AntMaxima
                );"""

        ch.command(create)
        truncate: str = "Truncate Table tasas_aut_x_riesgo;"
        ch.command(truncate)

        q: str = """
            WITH sinant AS (
                SELECT
                    NumTarifa,
                    Cap,
                    Air,
                    anyIf(TasaAnual, CodCobertura = 'C2') AS tasaC2,
                    anyIf(TasaAnual, CodCobertura = 'C5') AS tasaC5,
                    anyIf(TasaAnual, CodCobertura = 'B5') AS tasaB5,
                    anyIf(TasaAnual, CodCobertura = 'C4') AS tasaC4,
                    anyIf(TasaAnual, CodCobertura = 'B4') AS tasaB4
                FROM
                    reportes.dim_tasas_actual FINAL
                WHERE
                    NOT (CodCobertura LIKE 'D%')
                GROUP BY
                    NumTarifa,
                    Cap,
                    Air
            ),
            conant AS (
                SELECT
                    NumTarifa,
                    Cap,
                    Air,
                    segmento_ant,
                    anyIf(TasaAnual, CodCobertura = 'C2') AS tasaC2,
                    anyIf(TasaAnual, CodCobertura = 'C5') AS tasaC5,
                    anyIf(TasaAnual, CodCobertura = 'B5') AS tasaB5,
                    anyIf(TasaAnual, CodCobertura = 'C4') AS tasaC4,
                    anyIf(TasaAnual, CodCobertura = 'B4') AS tasaB4
                FROM
                    reportes.dim_tasas_actual FINAL
                GROUP BY
                    NumTarifa,
                    Cap,
                    Air,
                    segmento_ant
            ),
            parcial as (
                SELECT
                    NumTarifa,
                    Cap,
                    Air,
                    segmento_ant,
                    AntMinima,
                    AntMaxima,
                    CodCobertura,
                    TasaAnual,
                    greatest(c.tasaC2, s.tasaC2) as tasaC2,
                    greatest(c.tasaC4, s.tasaC4) as tasaC4,
                    greatest(c.tasaC5, s.tasaC5) as tasaC5,
                    greatest(c.tasaB4, s.tasaB4) as tasaB4,
                    greatest(c.tasaB5, s.tasaB5) as tasaB5
                FROM
                    dim_tasas_actual AS t FINAL
                    LEFT JOIN conant AS c USING (NumTarifa, Cap, Air, segmento_ant)
                    LEFT JOIN sinant AS s USING (NumTarifa, Cap, Air)
                where
                    TasaAnual Between 0.01
                    and 998
            )
            SELECT
                NumTarifa,
                Cap,
                Air,
                segmento_ant,
                AntMinima,
                AntMaxima,
                CodCobertura,
                TasaAnual,
                least(tasaC2, tasaC4, tasaC5, tasaB4, tasaB5) > 0 as Habilitado,
                tasaB4 * It as TasaIt,
                greatest(least(TasaAnual - TasaIt, tasaB5), 0) * Rt AS TasaRt,
                greatest(
                    least(
                        TasaAnual - TasaRt - TasaIt,
                        tasaC2 - tasaC5 - tasaC4
                    ),
                    0
                ) * At AS TasaAt,
                greatest(
                    least(
                        ((TasaAnual - TasaRt) - TasaIt) - TasaAt,
                        tasaC4 - tasaB4
                    ),
                    0
                ) * Ip AS TasaIp,
                greatest(
                    least(
                        TasaAnual - TasaRt - TasaIt - TasaAt - TasaIp,
                        tasaC5 - tasaB5
                    ),
                    0
                ) * Rp AS TasaRp,
                greatest(
                    TasaAnual - TasaRt - TasaIt - TasaAt - TasaIp - TasaRp,
                    0
                ) AS TasaAp
            from
                parcial
                LEFT JOIN dim_coberturas_aut AS dcob USING (CodCobertura)
            """

        try:
            res = ch.query(q, column_oriented=True)

            data = pl.from_dict(
                data={k: v for k, v in zip(res.column_names, res.result_set)}
            )

            ch.insert_arrow("tasas_aut_x_riesgo", data.to_arrow())

        except Exception as e:
            print(q)
            print(e)
            return

    print("\tLISTO")


def etl_tasas_anuales_autos_from_mysql():
    print("\nTasas Anuales")
    mysql = db.get_engine_mysql()

    data = pl.read_database(
        "Select * from TasasAnualesHist;",
        connection=mysql,
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
            # pl.col("Max").alias("AntMaxima"),
            pl.when(
                pl.col("Ant_")
                == pl.col("Ant_")
                .max()
                .over(partition_by=["NumTarifa", "Cap", "Air", "CodCobertura"])
            )
            .then(200)
            .otherwise(pl.col("Max"))
            .alias("AntMaxima"),
            pl.col("Tasa").alias("TasaAnual"),
            pl.col("Fecha").alias("fecha_desde"),
        ]
    )

    with db.get_client_ch() as ch:
        create: str = """CREATE TABLE if not exists dim_tasas_scd
                (
                    NumTarifa UInt32,
                    Cap UInt32,
                    Air UInt32,
                    CodCobertura LowCardinality(String),
                    segmento_ant UInt32,
                    AntMinima UInt32,
                    AntMaxima UInt32,
                    TasaAnual Float32,
                    fecha_desde Date
                )
                ENGINE = MergeTree
                ORDER BY (NumTarifa, Cap, Air, CodCobertura, segmento_ant, fecha_desde);"""
        ch.command(create)

        create: str = """CREATE TABLE if not exists dim_tasas_actual
                (
                    NumTarifa UInt32,
                    Cap UInt32,
                    Air UInt32,
                    CodCobertura LowCardinality(String),
                    segmento_ant UInt32,
                    AntMinima UInt32,
                    AntMaxima UInt32,
                    TasaAnual Float32,
                    fecha_desde Date
                )
                ENGINE = ReplacingMergeTree(fecha_desde)
                ORDER BY (NumTarifa, Cap, Air, CodCobertura,segmento_ant);"""
        ch.command(create)

        create: str = """CREATE MATERIALIZED VIEW if not exists mv_dim_tasas_actual
            TO dim_tasas_actual
            AS
            SELECT
                NumTarifa ,
                Cap ,
                Air ,
                CodCobertura ,
                segmento_ant ,
                AntMinima ,
                AntMaxima ,
                TasaAnual ,
                fecha_desde 
            FROM dim_tasas_scd;"""
        ch.command(create)

        resp = ch.query("Select * from dim_tasas_actual;", column_oriented=True)
        if resp.result_set != []:
            existentes = pl.from_dict(
                data={k: v for k, v in zip(resp.column_names, resp.result_set)},
                strict=False,
            )

            data_insert = data.join(
                existentes,
                how="anti",
                on=["NumTarifa", "Cap", "Air", "CodCobertura", "segmento_ant"],
            )

            x_cambiada = (
                (pl.col("AntMinima") != pl.col("AntMinima_ch"))
                | (pl.col("AntMaxima") != pl.col("AntMaxima_ch"))
                | (pl.col("TasaAnual") != pl.col("TasaAnual_ch"))
            )
            x_mas_nueva = pl.col("fecha_desde") > pl.col("fecha_desde_ch")
            data_update = (
                data.join(
                    existentes,
                    how="inner",
                    on=["NumTarifa", "Cap", "Air", "CodCobertura", "segmento_ant"],
                    suffix="_ch",
                )
                .filter(x_cambiada & x_mas_nueva)
                .select(data.columns)
            )
        else:
            data_insert = data
            data_update = pl.DataFrame({})

        if not data_insert.is_empty():
            ch.insert_arrow(TABLA_TASAS_ANUALES, data_insert.to_arrow())
        if not data_update.is_empty():
            ch.insert_arrow(TABLA_TASAS_ANUALES, data_update.to_arrow())

        print("\tLISTO")

    update_tasas_discriminadas()
