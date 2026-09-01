from datetime import date

import polars as pl

from ch.connections import ch_client, mysql_engine
from ch.loading import df_from_ch, load_incremental
from ch.log import logger
from ch.months import iter_months, resolve_fin
from ch.registry import register

OVERRIDES = {
    "CodRama": pl.UInt32,
    "Siniestro": pl.UInt32,
    "NroLiquidacion": pl.UInt32,
    "CodItemPago": pl.String,
    "FechaPago": pl.Date,
    "CodCausa": pl.UInt32,
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
    "CodModeloAu": pl.String,
    "AnioVehiculoAut": pl.UInt32,
    "OrigenVehiculoAut": pl.String,
    "CodTipoVehiculoAut": pl.UInt32,
    "CodUsoVehiculoAut": pl.UInt32,
    "Importe": pl.Float32,
}

QUERY = """SELECT
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
    B1_VHMO as CodModeloAu,
    B1_VHA as AnioVehiculoAut,
    B1_VHNI as OrigenVehiculoAut,
    B1_VHCT as CodTipoVehiculoAut,
    B1_VHUV as CodUsoVehiculoAut,
    LD_IIAU as Importe
FROM SINPAGT sin
WHERE Year(LC_FPAG) = {a} AND Month(LC_FPAG) = {m}"""

CONTROL_QUERY = """SELECT
    (SELECT max(toYYYYMM(FechaPago)) FROM sinpagt) as max_sinpagt,
    (SELECT max(toYYYYMM(FechaPagoMes)) FROM sinpagt_agg) as max_sinpagt_agg,
    (SELECT min(toYYYYMM(FechaPago)) FROM sinpagt) as min_sinpagt,
    (SELECT min(toYYYYMM(FechaPagoMes)) FROM sinpagt_agg) as min_sinpagt_agg,
    (SELECT count(DISTINCT toYYYYMM(FechaPago)) FROM sinpagt) as distintos_sinpagt,
    (SELECT count(DISTINCT toYYYYMM(FechaPagoMes)) FROM sinpagt_agg) as distintos_sinpagt_agg"""


@register("fact-sinpag", "hechos", "Órdenes de pago de siniestros (SINPAGT), incremental mensual")
def run(
    desde: str | None = None,
    hasta: str | None = None,
    anio: int | None = None,
) -> None:
    engine = mysql_engine()
    keys = ["CodRama", "Siniestro", "NroLiquidacion", "CodItemPago"]
    if desde is not None:
        inicio = date.fromisoformat(desde)
    elif anio is not None:
        inicio = date(anio, 1, 1)
    else:
        from sqlalchemy import text

        with engine.connect() as cn:
            fpago = cn.execute(text("SELECT min(LC_FPAG) FROM SINPAGT")).fetchone()
        if fpago is None or fpago[0] is None:
            logger.error("No se pudo determinar el mes mínimo de SINPAGT")
            return
        inicio = fpago[0]
    fin = resolve_fin(hasta)

    with ch_client() as ch:
        for a, m in iter_months(inicio, fin):
            data = pl.read_database(
                QUERY.format(a=a, m=m),
                connection=engine,
                schema_overrides=OVERRIDES,
            )
            if data.is_empty():
                continue
            n = load_incremental(ch, "sinpagt", data, keys, "FechaPago")
            logger.info("sinpagt %s-%02d: %s filas nuevas", a, m, n)

        try:
            control = df_from_ch(ch, CONTROL_QUERY)
            logger.info("Control sinpagt vs sinpagt_agg:\n%s", control)
        except Exception as e:
            logger.warning(
                "Control sinpagt_agg omitido (tabla no existe o sin datos): %s", e
            )
            try:
                fallback = df_from_ch(
                    ch,
                    "SELECT max(toYYYYMM(FechaPago)) as max_sinpagt, "
                    "min(toYYYYMM(FechaPago)) as min_sinpagt, "
                    "count(DISTINCT toYYYYMM(FechaPago)) as distintos_sinpagt "
                    "FROM sinpagt",
                )
                logger.info("Control sinpagt (solo base):\n%s", fallback)
            except Exception as e2:
                logger.warning("No se pudo obtener control de sinpagt: %s", e2)
