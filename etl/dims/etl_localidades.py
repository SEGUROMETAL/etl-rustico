import polars as pl
from etl.etl_constantes import TABLA_LOCALIDADES
import db


def etl_localidades():
    engine = db.get_engine_mysql()

    data = pl.read_database(
        """SELECT
                `LOCOPO` as Cp,
                `LOCOPS` as CpSufijo,
                `LOLOCA` as Localidad,
                `LOPROC` as CodProvinciaStr,
                `PRRPRO` as CodProvInder,
                `PRPROD` as Provincia
            FROM
                `GNTLOC` l
                LEFT JOIN `GNTPRO` p on l.`LOPROC` = p.`PRPROC`;
        """,
        connection=engine,
    )
    data = data.with_columns(
        [
            pl.col("Localidad").str.to_titlecase().str.strip_chars(),
            pl.col("Provincia").str.to_titlecase().str.strip_chars(),
        ]
    )
    with db.get_client_ch() as ch:
        print("\nLocalidades")
        create_sql = f"""create table if not exists {TABLA_LOCALIDADES} (
                Cp UInt32,
                CpSufijo UInt32,
                Localidad String,
                CodProvinciaStr LowCardinality(String),
                CodProvInder UInt32,
                Provincia LowCardinality(String)
            ) Engine MergeTree()
            order by
                (Cp, CpSufijo);"""
        ch.command(create_sql)

        ch.command(f"TRUNCATE TABLE {TABLA_LOCALIDADES}")
        ch.insert_arrow(
            TABLA_LOCALIDADES,
            data.to_arrow(),
        )
    print("\tLISTO")
