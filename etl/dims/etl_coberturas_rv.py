from etl.etl_constantes import TABLA_COBERTURAS_RV
import polars as pl
import db


def etl_coberturas_rv():
    print("\n Coberturas Ramas Varias.")

    engine = db.get_engine_mysql()
    data = pl.read_database(
        """SELECT
                `CodRama`,
                `CodCobertura`,
                `Cobertura`,
                `Pormilaje`,
                `Informe`
            FROM
                dims_coberturas_rv;
            """,
        schema_overrides={
            "CodRama": pl.UInt32,
            "CodCobertura": pl.UInt32,
            "Cobertura": pl.String,
            "Pormilaje": pl.Float32,
            "Informe": pl.String,
        },
        connection=engine,
    )

    with db.get_client_ch() as ch:
        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {TABLA_COBERTURAS_RV} (
                CodRama UInt32,
                CodCobertura UInt32,
                Cobertura String,
                Pormilaje Float32,
                Informe LowCardinality(String)
            )
            ENGINE = MergeTree()
            ORDER BY (Informe, CodRama, CodCobertura);"""
        ch.command(create_sql)

        if data.is_empty():
            print("No hay coberturas desde Mysql")
            return

        ch.command(f"Truncate table {TABLA_COBERTURAS_RV};")
        ch.insert_arrow(
            TABLA_COBERTURAS_RV,
            data.to_arrow(),
        )

        print("\tLISTO")
