import db
import polars as pl
from sqlalchemy import text
from datetime import date, timedelta

# La tabla está particionada por mes


def etl_sinpagt():
    print("\nSINPAG")
    engine = db.get_engine_mysql()

    query_control: str = """select
        (
            SELECT
                max(toYYYYMM(FechaPago))
            from
                sinpagt
        ) as min_sinpagt,
        (
            SELECT
                max(toYYYYMM(FechaPagoMes))
            from
                sinpagt_agg
        ) as min_sinpagt_agg,
        (
            SELECT
                min(toYYYYMM(FechaPago))
            from
                sinpagt
        ) as max_sinpagt,
        (
            SELECT
                min(toYYYYMM(FechaPagoMes))
            from
                sinpagt_agg
        ) as max_sinpagt_agg,
        (
            SELECT
                count(DISTINCT toYYYYMM(FechaPago))
            from
                sinpagt
        ) as distinc_sinpagt,
        (
            SELECT
                count(DISTINCT toYYYYMM(FechaPagoMes))
            from
                sinpagt_agg
        ) as distinc_sinpagt_agg;"""

    schema_overrides = {
        "CodRama": pl.UInt32,
        "Siniestro": pl.UInt32,
        "NroLiquidacion": pl.UInt32,
        "CodItemPago": pl.String,
        "FechaPago": pl.Date,
        "Codcausa": pl.UInt32,
        "NroAsegurado": pl.UInt32,
        "CodOrganizador": pl.UInt32,
        "CodProductor": pl.UInt32,
        "TipoMovimiento": pl.String,
        "TipoLiquidacion": pl.String,
        "Clasereserva": pl.UInt32,
        "TipoAcreedor": pl.String,
        "CodAcreedor": pl.UInt32,
        "CodMayorAuxiliar": pl.String,
        "NroMayorAuxiliar": pl.UInt32,
        "Pagado": pl.String,
        "Proceso": pl.String,
        "EstadoIngreso": pl.String,
        "CantFrentes": pl.UInt32,
        "Op": pl.UInt32,
        "NroBeneficiario": pl.UInt32,
        "TipoReserva": pl.String,
        "CodRiesgo": pl.String,
        "CoberturaReservada": pl.UInt32,
        "ItemPago": pl.String,
        "FechaDenuncia": pl.Date,
        "FechaOcurrencia": pl.Date,
        "DireccionSiniestro": pl.String,
        "CpSiniestro": pl.UInt32,
        "MarcaFueraTermino": pl.String,
        "CodTerminado": pl.String,
        "CodUbicacion": pl.String,
        "FueraVigencia": pl.String,
        "PolizaAnulada": pl.String,
        "EnCaducidad": pl.String,
        "ComponenteBaja": pl.String,
        "Conductor": pl.UInt32,
        "CondHabitual": pl.String,
        "Poliza": pl.UInt32,
        "Supl": pl.UInt32,
        "Comp": pl.UInt32,
        "CodCoberturaAut": pl.String,
        "SumaAseguradaAut": pl.UInt32,
        "CodInderProvinciaAut": pl.UInt32,
        "CodMarcaAu": pl.String,
        "CodModeloAut": pl.String,
        "AnioVehiculoAut": pl.UInt32,
        "OrigenVehiculoAut": pl.String,
        "CodTipoVehiculoAut": pl.UInt32,
        "CodUsoVehiculoAut": pl.UInt32,
        "Importe": pl.Float32,
    }

    with engine.connect() as cn:
        try:
            fpago: date = (
                cn.execute(text("Select min(LC_FPAG) From SINPAGT;")).fetchone()[0]  # pyright: ignore[reportOptionalSubscript]
            )
            a, m = fpago.year, fpago.month
        except Exception:
            print("Problemas con el mes mñinimo en SINPAGT")
            return

    while True:
        q: str = f"""SELECT
                LC_RAMA as CodRama,
                LD_SINI as Siniestro,
                LC_LIQN as NroLiquidacion,
                TRIM(sin.LD_ITEC) as CodItemPago,
                LC_FPAG as FechaPago,
                DC_CAUC as CodCausa,
                PO_ASEN as NroAsegurado,
                PO_ORG1 as CodOrganizador,
                PO_PRO1 as CodProductor,
                LC_MOVT as TipoMovimiento,
                LC_LIQT as TipoLiquidacion,
                LC_CLRE as Clasereserva,
                LC_ACRT as TipoAcreedor,
                LC_ACRC as CodAcreedor,
                LC_COMA as CodMayorAuxiliar,
                LC_NRMA as NroMayorAuxiliar,
                LC_MDPA as Pagado,
                LC_MARP as Proceso,
                LC_IVSI as EstadoIngreso,
                LC_CFRE as CantFrentes,
                LD_OPER as Op,
                LD_BENN as NroBeneficiario,
                LD_TIPR as TipoReserva,
                LD_RIEC as CodRiesgo,
                LD_COBR as CoberturaReservada,
                LD_ITED as ItemPago,
                DC_FDEN as FechaDenuncia,
                DC_FSIN as FechaOcurrencia,
                DC_LUDI as DireccionSiniestro,
                DC_COPO as CpSiniestro,
                DC_MDFT as MarcaFueraTermino,
                DC_TERM as CodTerminado,
                DC_COUB as CodUbicacion,
                DP_MSFV as FueraVigencia,
                DP_MAPA as PolizaAnulada,
                DP_MPEC as EnCaducidad,
                DP_MCDB as ComponenteBaja,
                DP_NRDF as Conductor,
                DP_COSN as CondHabitual,
                PO_POLI as Poliza,
                DP_SUOP as Supl,
                LD_POCO as Comp,
                C1_COBL as CodCoberturaAut,
                C1_VHVU as SumaAseguradaAut,
                B1_RPRO as CodInderProvinciaAut,
                B1_VHMC as CodMarcaAu,
                B1_VHMO as CodModeloAut,
                B1_VHA as AnioVehiculoAut,
                B1_VHNI as OrigenVehiculoAut,
                B1_VHCT as CodTipoVehiculoAut,
                B1_VHUV as CodUsoVehiculoAut,
                LD_IIAU as Importe
            FROM
                SINPAGT sin
            Where Year(LC_FPAG) = {a} AND Month(LC_FPAG) = {m};"""

        sinpagt: pl.DataFrame = pl.read_database(
            q,
            connection=engine,
            schema_overrides=schema_overrides,
        )

        if sinpagt.is_empty():
            break

        with db.get_client_ch() as ch:
            query = f"""SELECT CodRama, Siniestro, NroLiquidacion, CodItemPago FROM sinpagt Where toYYYYMM(FechaPago) = {a * 100 + m};"""
            resp = ch.query(query, column_oriented=True)
            if resp.result_set != []:
                existentes = pl.from_dict(
                    data={k: v for k, v in zip(resp.column_names, resp.result_set)}
                )

                sinpagt = sinpagt.join(existentes, how="anti", on=resp.column_names)

        print(f"\tMes {a * 100 + m}", f"nuevas {len(sinpagt)} .", sep=" | ")
        amdate: date = date(a, m, 5) + timedelta(days=30)
        a, m = amdate.year, amdate.month
        if sinpagt.is_empty():
            continue
        ch.insert_arrow("sinpagt", sinpagt.to_arrow())

    with db.get_client_ch() as ch:
        resp_control = ch.query(query_control, column_oriented=True)
        if resp_control.result_set != []:
            control = pl.from_dict(
                data={
                    k: v
                    for k, v in zip(resp_control.column_names, resp_control.result_set)
                }
            )
            print(control)

    print("\tLISTO")
