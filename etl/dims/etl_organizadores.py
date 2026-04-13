import polars as pl
from etl.etl_constantes import TABLA_ORGANIZADORES
import db


def etl_organizadores():
    print("\nOrganizadores")

    engine = db.get_engine_mysql()

    data = pl.read_database(
        """SELECT
            `ININNA` as CodOrganizador,
            `INNRDF` as NroPersona,
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
            `INMATR` as Matricula,
            gr.`GPGRUP` as CodGrupo,
            gr.`GPNOGR` as Grupo
        FROM
            `SEHINT01` s
            LEFT JOIN `SETGRJ` rel ON s.`ININNA` = rel.`GJINTE`
            LEFT JOIN `SETGRP` gr ON rel.`GJGRUP` = gr.`GPGRUP`
        WHERE
            `ININTA` = 3
            AND DFNOMB <> 'LIBRE';
        """,
        connection=engine,
    )
    data = data.with_columns(
        [
            pl.col("Nombre").str.to_titlecase().str.strip_chars(),
            pl.col("Grupo").str.to_titlecase().str.strip_chars(),
        ]
    ).unique()
    with db.get_client_ch() as ch:
        # Organizadores
        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {TABLA_ORGANIZADORES} (
                CodOrganizador UInt32,
                NroPersona UInt32,
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
                CodGrupo UInt32,
                Grupo String,
                version Datetime DEFAULT now()
            ) ENGINE = ReplacingMergeTree(version)
            ORDER BY (CodOrganizador);"""
        ch.command(create_sql)

        ch.command(f"TRUNCATE TABLE {TABLA_ORGANIZADORES}")
        ch.insert_arrow(
            TABLA_ORGANIZADORES,
            data.to_arrow(),
        )
    print("\tLISTO")
