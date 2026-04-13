from etl.etl_constantes import TABLA_RCS_ANUALES
import polars as pl
import db


def et_rcs_anuales_from_mysql():
    mysql = db.get_engine_mysql()

    data = (
        pl.read_database(
            "Select * from RcsAnualesHist;",
            connection=mysql,
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

    with db.get_client_ch() as ch:
        create: str = """CREATE TABLE IF NOT EXISTS dim_rc_scd
            (
                NumTarifa UInt32,
                Cap UInt32,
                Var UInt32,
                RcSl Float32,
                RcCl Float32,
                RcExt Float32,
                RcAp Float32,
                RcObl Float32,
                fecha_desde Date
            )
            ENGINE = MergeTree
            ORDER BY (NumTarifa, Cap, Var, fecha_desde);"""
        ch.command(create)

        create: str = """CREATE TABLE IF NOT EXISTS dim_rc_actual
                (
                    NumTarifa UInt32,
                    Cap UInt32,
                    Var UInt32,
                    RcSl Float32,
                    RcCl Float32,
                    RcExt Float32,
                    RcAp Float32,
                    RcObl Float32,
                    fecha_desde Date
                )
                ENGINE = ReplacingMergeTree(fecha_desde)
                ORDER BY (NumTarifa, Cap, Var);"""
        ch.command(create)

        create: str = """CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dim_rc_actual
            TO dim_rc_actual
            AS
            SELECT
                NumTarifa ,
                Cap ,
                Var ,
                RcSl ,
                RcCl ,
                RcExt ,
                RcAp ,
                RcObl ,
                fecha_desde 
            FROM dim_rc_scd;"""
        ch.command(create)

        resp = ch.query("Select * from dim_rc_actual;")
        if resp.result_set != []:
            existentes = pl.from_dict(
                data={k: v for k, v in zip(resp.column_names, resp.result_set)}
            )
            _data = data.join(
                existentes, how="left", on=["NumTarifa", "Cap", "Var"], suffix="_ch"
            )
            x_nueva = pl.col("NumTarifa_ch").is_null()
            x_cambiada = (
                (pl.col("RcSl") == pl.col("RcSl_ch"))
                | (pl.col("RcCl") == pl.col("RcCl"))
                | (pl.col("RcExt") == pl.col("RcExt_ch"))
                | (pl.col("RcAp") == pl.col("RcAp_ch"))
                | (pl.col("RcObl") == pl.col("RcObl_ch"))
            )
            data = _data.filter(x_nueva | x_cambiada).select(data.columns)

        ch.insert_arrow(TABLA_RCS_ANUALES, data.to_arrow())
