from etl.etl_constantes import TABLA_COBERTURAS_AUT
import polars as pl
import db


def etl_coberturas_aut():
    print("\n Coberturas Automotores.")
    engine = db.get_engine_mysql()
    data = pl.read_database(
        """Select CodCobertura,
            OrCobertura,
            CatCobertura,
            OrCatCobertura,
            Rt,
            Rp,
            It,
            Ip,
            At,
            Ap
        from dims_coberturas_aut;
        """,
        connection=engine,
    )
    with db.get_client_ch() as ch:
        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {TABLA_COBERTURAS_AUT} (
                CodCobertura String,
                OrCobertura UInt32,
                CatCobertura String,
                OrCatCobertura UInt32,
                Rt UInt16,
                Rp UInt16,
                It UInt16,
                Ip UInt16,
                At UInt16,
                Ap UInt16,
                version DateTime DEFAULT now()
            )
            ENGINE = ReplacingMergeTree(version)
            ORDER BY (CodCobertura);"""

        ch.command(create_sql)

        ch.insert_arrow(
            TABLA_COBERTURAS_AUT,
            data.to_arrow(),
        )
    print("\tLISTO")
