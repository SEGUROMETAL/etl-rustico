import db
import polars as pl
from sqlalchemy import text
from datetime import date, timedelta


def etl_sehpm151t(anio: int = 2025):
    engine = db.get_engine_mysql()
    a: int = anio
    m: int = 1

    schema_overrides: dict = {
        "Op": pl.UInt32,
        "Suplemento": pl.UInt32,
        "CodTipoOp": pl.UInt32,
        "CodSubTipoOp": pl.UInt32,
        "PlVidaNvaRen": pl.UInt32,
        "CodRama": pl.UInt32,
        "Poliza": pl.UInt32,
        "NroAsegurado": pl.UInt32,
        "CpAsegurado": pl.UInt32,
        "CpSufijoAsegurado": pl.UInt32,
        "NombreAsegurado": str,
        "LocalidadAsegurado": str,
        "ProvinciaAsegurado": str,
        "CodOrganizador": pl.UInt32,
        "CodProductor": pl.UInt32,
        "SumaAsegurada": pl.Float64,
        "PrimaNeta": pl.Float64,
        "RecFin": pl.Float64,
        "RecAdm": pl.Float64,
        "DerEmision": pl.Float64,
        "SellRiesgo": pl.Float64,
        "ImpInt": pl.Float64,
        "ServSoc": pl.Float64,
        "TasaSsn": pl.Float64,
        "Iva": pl.Float64,
        "IvaPercepcion": pl.Float64,
        "IvaRespNoInscr": pl.Float64,
        "BonifPrima": pl.Float64,
        "Acc": pl.Float64,
        "RecCapital": pl.Float64,
        "FEmision": pl.Date,
        "FVigDesde": pl.Date,
        "FVigHasta": str,
        "PrimaTarifa": pl.Float64,
        "PremioBruto": pl.Float64,
        "CodOrganizadorComision": pl.UInt32,
        "ComOrganizador": pl.Float64,
        "CodProductorComision": pl.UInt32,
        "ComProductor": pl.Float64,
        
    }

    while True:
        q: str = f"""
                SELECT
                    `M1OPER` as Op,
                    `M1SUOP` as Suplemento,
                    `M1TIOU` as CodTipoOp,
                    `M1STOU` as CodSubTipoOp,
                    `M1PVNR` as PlVidaNvaRen,
                    `M1RAMA` as CodRama,
                    `M1POLI` as Poliza,
                    `M1ASEN` as NroAsegurado,
                    `M1COPOA` as CpAsegurado,
                    `M1COPSA` as CpSufijoAsegurado,
                    `M1NOMBA` as NombreAsegurado,
                    `M1NOLOA` as LocalidadAsegurado,
                    `M1PRLOA` as ProvinciaAsegurado,
                    `M1ORG1` as CodOrganizador,
                    `M1PRO1` as CodProductor,
                    `MASAOP` as SumaAsegurada,
                    `MAPRIM`  as PrimaNeta,
                    `MAREFI` as RecFin,
                    `MAREAD` as RecAdm,
                    `MADERE` as DerEmision,
                    `MASERI` as SellRiesgo,
                    `MAIMPI` as ImpInt,
                    `MASERS` as ServSoc,
                    `MATSSN` as TasaSsn,
                    `MAIPR1` as Iva,
                    `MAIPR3` as IvaPercepcion,
                    `MAIPR4` as IvaRespNoInscr,
                    `MABPRI` as BonifPrima,
                    `MAIPR2` as Acc,
                    `MAIPR5` as RecCapital,
                    DATE(CONCAT(`M1FEMA`, '-', `M1FEMM`, '-', `M1FEMD`)) as FEmision,
                    DATE(CONCAT(`M1FIOA`, '-', `M1FIOM`, '-', `M1FIOD`)) as FVigDesde,
                    CONCAT(`M1FVOA`, '-', `M1FVOM`, '-', `M1FVOD`) as FVigHasta,
                    `MAPRIM` + `MABPRI` AS PrimaTarifa,
                    `MAIPR5` + `MAPREM` as PremioBruto,
                    `CodIntOrg` as CodOrganizadorComision,
                    `ComOrg` as ComOrganizador,
                    `CodIntProd` as CodProductorComision,
                    `ComProd` as ComProductor

                FROM
                    `SEHPM151T` sh
                Where M1FEMA = {a} AND M1FEMM = {m};"""

        sehpm151t: pl.DataFrame = (
            pl.read_database(
                q,
                connection=engine,
                schema_overrides=schema_overrides,
            )
            .with_columns(
                pl.col("FVigHasta").str.to_date(format="%Y-%m-%d", strict=False)
            )
            .with_columns(
                [
                    pl.col("CodOrganizador").replace(3873, 9105),
                    pl.col("CodProductor").replace(9105, 3873),
                ]
            )
        )

        if sehpm151t.is_empty():
            break

        with db.get_client_ch() as ch:
            query = f"SELECT Op, Suplemento FROM sehpm151t Where toYYYYMM(FEmision) = {a * 100 + m} ;"
            resp = ch.query(query, column_oriented=True)
            if resp.result_set != []:
                existentes = pl.from_dict(
                    data={k: v for k, v in zip(resp.column_names, resp.result_set)}
                )

                sehpm151t = sehpm151t.join(existentes, how="anti", on=resp.column_names)

        print(f"Mes {a * 100 + m}", f"nuevas {len(sehpm151t)} .", sep=" | ")
        amdate: date = date(a, m, 5) + timedelta(days=30)
        a, m = amdate.year, amdate.month

        if sehpm151t.is_empty():
            continue
        ch.insert_arrow("sehpm151t", sehpm151t.to_arrow())
