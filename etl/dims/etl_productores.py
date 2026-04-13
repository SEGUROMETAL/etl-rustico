import polars as pl
from etl.etl_constantes import TABLA_PRODUCTORES
import db


def etl_productores():
    print("\nProductores")
    engine = db.get_engine_mysql()
    data = pl.read_database(
        """SELECT
            `ININNA` as CodProductor,
            `INNRDF` as NroPersonaProductor,
            `DFNOMB` as Nombre,
            `DFDOMI` as Domicilio,
            `DFCOPO` as Cp,
            `DFCOPS` as CpSufijo,
            `LOLOCA` as Localidad,
            `LOPROC` as CodProvincia,
            `DFTIDO` as TipoDoc,
            `DFNRDO` as NroDoc,
            `DFCUIT` as Cuit,
            `PRPROD` AS Provincia,
            `PRRPRO` AS CodInderProvincia,
            `INMATR` as Matricula
        FROM
            `SEHINT01`
        WHERE
            `ININTA` = 4
            AND `DFNOMB` <> 'LIBRE';
        """,
        connection=engine,
    ).unique()
    with db.get_client_ch() as ch:
        # Productores
        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {TABLA_PRODUCTORES} (
                CodProductor UInt32,
                NroPersonaProductor  UInt32,
                Nombre String,
                Domicilio String,
                Cp  UInt32,
                CpSufijo UInt32,
                Localidad String,
                CodProvincia LowCardinality(String),
                TipoDoc LowCardinality(String),
                NroDoc UInt32,
                Cuit String,
                Provincia LowCardinality(String),
                CodInderProvincia LowCardinality(String),
                Matricula  UInt32,
                version Datetime DEFAULT now()
            ) ENGINE = ReplacingMergeTree(version)
            ORDER BY (CodProductor);"""
        ch.command(create_sql)

        ch.command(f"TRUNCATE TABLE {TABLA_PRODUCTORES}")
        ch.insert_arrow(
            TABLA_PRODUCTORES,
            data.to_arrow(),
        )
    print("\tLISTO")
