import db
import polars as pl
from datetime import date, timedelta

# La tabla está particionada por mes


def etl_denupet(anio_desde: int):
    engine = db.get_engine_mysql()
    a: int = anio_desde
    m: int = 1

    schema_overrides = {
        "Operacion": pl.UInt32,
        "CodRama": pl.UInt32,
        "Poliza": pl.UInt32,
        "Supl": pl.UInt32,
        "Comp": pl.UInt32,
        "Siniestro": pl.UInt32,
        "FechaDenuncia": pl.Date,
        "FechaSiniestro": pl.Date,
        "CodCausa": pl.UInt32,
        "Causa": pl.String,
        "DireccionSiniestro": pl.String,
        "CpSiniestro": pl.UInt32,
        "CodOrganizador": pl.UInt32,
        "CodProductor": pl.UInt32,
        "NroAsegurado": pl.UInt32,
    }

    while True:
        q: str = f"""
            SELECT
                `DPOPER` as Op,
                `DCRAMA` as CodRama,
                `POPOLI` as Poliza,
                `POPOSP` as Supl,
                `DPPOCO` as Comp,
                `DCSINI` as Siniestro,
                `FEDENU` as FechaDenuncia,
                `FESINI` as FechaSiniestro,
                `DCCAUC` as CodCausa,
                `TACAUD` as Causa,    
                `DCLUDI` as DireccionSiniestro,
                `DCCOPO` as CpSiniestro,
                `POORG1` as CodOrganizador,
                `POPRO1` as CodProductor,
                `POASEN` as NroAsegurado
            FROM
                `DenuPe`
            Where Year(FEDENU) = {a} AND Month(FEDENU) = {m};"""

        denupet: pl.DataFrame = pl.read_database(
            q,
            connection=engine,
            schema_overrides=schema_overrides,
        )

        if denupet.is_empty():
            break

        with db.get_client_ch() as ch:
            query = f"""SELECT Op, Siniestro, Comp FROM denupet Where toYYYYMM(FechaDenuncia) = {a * 100 + m};"""
            resp = ch.query(query, column_oriented=True)
            if resp.result_set != []:
                existentes = pl.from_dict(
                    data={k: v for k, v in zip(resp.column_names, resp.result_set)}
                )

                denupet = denupet.join(existentes, how="anti", on=resp.column_names)

        print(f"\tMes {a * 100 + m}", f"nuevas {len(denupet)} .", sep=" | ")
        amdate: date = date(a, m, 5) + timedelta(days=30)
        a, m = amdate.year, amdate.month
        if denupet.is_empty():
            continue
        ch.insert_arrow("denupet", denupet.to_arrow())

    print("\tLISTO")
