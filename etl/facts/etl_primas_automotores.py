import db
import polars as pl
from etl.etl_constantes import TABLA_PRIMAS_AUTOMOTORES
from datetime import date, timedelta


def etl_primas_automotores(anio: int = 2025):
    engine = db.get_engine_mysql()
    a: int = anio
    m: int = 1

    override = {
        "FEmision": pl.Date,
        "FVigDesde": pl.Date,
        "FVigHasta": pl.Date,
        "Op": pl.UInt32,
        "Comp": pl.UInt32,
        "Supl": pl.UInt32,
        "CodRama": pl.UInt32,
        "Poliza": pl.UInt32,
        "SaComponente": pl.Float64,
        "Cap": pl.UInt32,
        "Var": pl.UInt32,
        "Air": pl.UInt32,
        "Origen": str,
        "AnioComponente": pl.UInt32,
        "CodCoberturaAut": str,
        "CodTipoVeh": pl.UInt32,
        "CodUsoVeh": pl.UInt32,
        "PrimaTarifaSupl": pl.Float64,
        "BonPrimaSupl": pl.Float64,
        "PremioSupl": pl.Float64,
        "relPriPreSupl": pl.Float64,
        "PremioCobradoSupl": pl.Float64,
        "CodOrganizador": pl.UInt32,
        "CodProductor": pl.UInt32,
        "PrimaTarifaComp": pl.Float64,
        "PrimaRcTarifaComp": pl.Float64,
        "PrimaCascoTarifaComp": pl.Float64,
        "PrimaNetaComp": pl.Float64,
        "PrimaRcNetaComp": pl.Float64,
        "PrimaCascoNetaComp": pl.Float64,
    }

    while True:
        q: str = f"""
                SELECT * 
                FROM primas_automotores
                Where Year(FEmision) = {a} AND Month(FEmision) = {m};"""

        pr_autos: pl.DataFrame = pl.read_database(
            q,
            connection=engine,
            schema_overrides=override,  # pyright: ignore[reportArgumentType]
        ).select(
            pl.exclude(
                [
                    "AnioMesEmision",
                    "AnioEmision",
                    "MesEmision",
                    "DiaEmision",
                    "estadopoliza",
                    "ant",
                    "relPriPreSupl",
                ]
            )
        )

        if pr_autos.is_empty():
            break

        with db.get_client_ch() as ch:
            create = """CREATE TABLE IF NOT Exists primas_automotores (
                    `FEmision` Date,
                    `FVigDesde` Date,
                    `FVigHasta` Date,
                    `Op` UInt32,
                    `Comp` UInt32,
                    `Supl` UInt32,
                    `CodRama` UInt32,
                    `Poliza` UInt32,
                    `SaComponente` Float64,
                    `Cap` UInt32,
                    `Var` UInt32,
                    `Air` UInt32,
                    `Origen` String,
                    `AnioComponente` UInt32,
                    `CodCoberturaAut` String,
                    `CodTipoVeh` UInt32,
                    `CodUsoVeh` UInt32,
                    `PrimaTarifaSupl` Float64,
                    `BonPrimaSupl` Float64,
                    `PremioSupl` Float64,
                    `PremioCobradoSupl` Float64,
                    `CodOrganizador` UInt32,
                    `CodProductor` UInt32,
                    `PrimaTarifaComp` Float64,
                    `PrimaRcTarifaComp` Float64,
                    `PrimaCascoTarifaComp` Float64,
                    `PrimaNetaComp` Float64,
                    `PrimaRcNetaComp` Float64,
                    `PrimaCascoNetaComp` Float64
                ) ENGINE = MergeTree PARTITION BY toYYYYMM(FEmision)
                ORDER BY
                    (Op, CodRama, Poliza, Supl, Comp, CodCoberturaAut) 
                SETTINGS index_granularity = 8192;"""
            ch.command(create)

            create = """CREATE TABLE IF NOT Exists primas_automotores_agg (
                        FEmisionMes Date,
                        `CodOrganizador` UInt32,
                        `CodProductor` UInt32,
                        `CodRama` UInt32,
                        `CodCoberturaAut` String,
                        `CodTipoVeh` UInt32,
                        `CodUsoVeh` UInt32,
                        `AnioComponente` UInt32,
                        `Origen` String,
                        `FVigDesde` Date,
                        `FVigHasta` Date,
                        `Op` UInt32,
                        `Comp` UInt32,
                        `Supl` UInt32,
                        `Poliza` UInt32,
                        `SaComponente` Float64,
                        `Cap` UInt32,
                        `Var` UInt32,
                        `Air` UInt32,
                        `PrimaTarifaSupl` Float64,
                        `BonPrimaSupl` Float64,
                        `PremioSupl` Float64,
                        `PremioCobradoSupl` Float64,
                        `PrimaTarifaComp` Float64,
                        `PrimaRcTarifaComp` Float64,
                        `PrimaCascoTarifaComp` Float64,
                        `PrimaNetaComp` Float64,
                        `PrimaRcNetaComp` Float64,
                        `PrimaCascoNetaComp` Float64
                    ) ENGINE = SummingMergeTree() PARTITION BY toYYYYMM(FEmisionMes)
                    ORDER BY
                        (
                            FEmisionMes,
                            CodOrganizador,
                            CodProductor,
                            CodRama,
                            CodCoberturaAut,
                            CodTipoVeh,
                            CodUsoVeh,
                            AnioComponente,
                            Origen
                        ) 
                    SETTINGS index_granularity = 8192;"""
            ch.command(create)

            create = """CREATE MATERIALIZED VIEW IF NOT Exists primas_automotores_agg_mv TO primas_automotores_agg AS
                SELECT
                    toStartOfMonth(`FEmision`) AS FEmisionMes,
                    `CodOrganizador`,
                    `CodProductor`,
                    `CodRama`,
                    `CodCoberturaAut`,
                    `CodTipoVeh`,
                    `CodUsoVeh`,
                    `AnioComponente`,
                    `Origen`,
                    `FVigDesde`,
                    `FVigHasta`,
                    `Op`,
                    `Comp`,
                    `Supl`,
                    `Poliza`,
                    `SaComponente`,
                    `Cap`,
                    `Var`,
                    `Air`,
                    sum(PrimaTarifaSupl) AS PrimaTarifaSupl,
                    sum(BonPrimaSupl) AS BonPrimaSupl,
                    sum(PremioSupl) AS PremioSupl,
                    sum(PremioCobradoSupl) AS PremioCobradoSupl,
                    sum(PrimaTarifaComp) AS PrimaTarifaComp,
                    sum(PrimaRcTarifaComp) AS PrimaRcTarifaComp,
                    sum(PrimaCascoTarifaComp) AS PrimaCascoTarifaComp,
                    sum(PrimaNetaComp) AS PrimaNetaComp,
                    sum(PrimaRcNetaComp) AS PrimaRcNetaComp,
                    sum(PrimaCascoNetaComp) AS PrimaCascoNetaComp
                FROM
                    primas_automotores
                GROUP BY
                    FEmisionMes,
                    `CodOrganizador`,
                    `CodProductor`,
                    `CodRama`,
                    `CodCoberturaAut`,
                    `CodTipoVeh`,
                    `CodUsoVeh`,
                    `AnioComponente`,
                    `Origen`,
                    `FVigDesde`,
                    `FVigHasta`,
                    `Op`,
                    `Comp`,
                    `Supl`,
                    `Poliza`,
                    `SaComponente`,
                    `Cap`,
                    `Var`,
                    `Air`;"""
            ch.command(create)

            query = f"SELECT Op, Supl, Comp FROM {TABLA_PRIMAS_AUTOMOTORES} Where toYYYYMM(FEmision) = {a * 100 + m} ;"
            resp = ch.query(query, column_oriented=True)
            if resp.result_set != []:
                existentes = pl.from_dict(
                    data={k: v for k, v in zip(resp.column_names, resp.result_set)}
                )

                pr_autos = pr_autos.join(existentes, how="anti", on=resp.column_names)

        print(f"\tMes {a * 100 + m}", f"nuevas {len(pr_autos)} .", sep=" | ")
        amdate: date = date(a, m, 5) + timedelta(days=30)
        a, m = amdate.year, amdate.month

        if pr_autos.is_empty():
            continue
        ch.insert_arrow(TABLA_PRIMAS_AUTOMOTORES, pr_autos.to_arrow())

    print("\tLISTO")
