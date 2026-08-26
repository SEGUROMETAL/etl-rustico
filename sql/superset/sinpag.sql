CREATE TABLE IF NOT EXISTS reportes.sinpagt (
    CodRama UInt32,
    Siniestro UInt32,
    NroLiquidacion UInt32,
    CodItemPago LowCardinality(String),
    FechaPago Date,
    CodCausa UInt32,
    NroAsegurado UInt32,
    CodOrganizador UInt32,
    CodProductor UInt32,
    TipoMovimiento String,
    TipoLiquidacion String,
    Clasereserva UInt32,
    TipoAcreedor String,
    CodAcreedor UInt32,
    CodMayorAuxiliar String,
    NroMayorAuxiliar UInt32,
    Pagado String,
    Proceso String,
    EstadoIngreso String,
    CantFrentes UInt32,
    Op UInt32,
    NroBeneficiario UInt32,
    TipoReserva String,
    CodRiesgo String,
    CoberturaReservada UInt32,
    ItemPago String,
    FechaDenuncia Date,
    FechaOcurrencia Date,
    DireccionSiniestro String,
    CpSiniestro UInt32,
    MarcaFueraTermino String,
    CodTerminado String,
    CodUbicacion String,
    FueraVigencia String,
    PolizaAnulada String,
    EnCaducidad String,
    ComponenteBaja String,
    Conductor UInt32,
    CondHabitual String,
    Poliza UInt32,
    Supl UInt32,
    Comp UInt32,
    CodCoberturaAut String,
    SumaAseguradaAut Float32,
    CodInderProvinciaAut UInt32,
    CodMarcaAu String,
    CodModeloAut String,
    AnioVehiculoAut UInt32,
    OrigenVehiculoAut String,
    CodTipoVehiculoAut UInt32,
    CodUsoVehiculoAut UInt32,
    Importe Float32
) ENGINE = MergeTree PARTITION BY toYYYYMM(FechaPago)
ORDER BY
    (
        toYYYYMM(FechaPago),
        CodRama,
        CodOrganizador,
        CodProductor,
        NroAsegurado,
        CodCausa,
        CodItemPago
    ) SETTINGS index_granularity = 8192;


--
--
CREATE MATERIALIZED VIEW sinpagt_perfiles_agg_mv TO sinpagt_perfiles_agg AS
SELECT
    CodRama,
    CodOrganizador,
    CodProductor,
    NroAsegurado,
    toStartOfMonth(FechaPago) AS FechaPagoMes,
    sum(Importe) AS Importe,
    countDistinct(Siniestro) as siniestros_pagados
FROM
    sinpagt
GROUP BY
    CodRama,
    CodOrganizador,
    CodProductor,
    NroAsegurado,
    FechaPagoMes;


--
CREATE TABLE sinpagt_perfiles_agg (
    `CodRama` UInt32,
    `CodOrganizador` UInt32,
    `CodProductor` UInt32,
    `NroAsegurado` UInt32,
    `FechaPagoMes` Date,
    `Importe` Float32,
    siniestros_pagados Int32
) ENGINE = SummingMergeTree PARTITION BY toYYYYMM(FechaPagoMes)
ORDER BY
    (
        `CodRama`,
        `CodOrganizador`,
        `CodProductor`,
        `NroAsegurado`,
        `FechaPagoMes`
    ) SETTINGS index_granularity = 8192;


--
--
--Control de meses
select
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
    ) as distinc_sinpagt_agg;


--