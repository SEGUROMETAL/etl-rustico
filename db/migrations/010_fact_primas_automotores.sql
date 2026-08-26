CREATE TABLE IF NOT EXISTS primas_automotores (
    FEmision Date,
    FVigDesde Date,
    FVigHasta Date,
    Op UInt32,
    Comp UInt32,
    Supl UInt32,
    CodRama UInt32,
    Poliza UInt32,
    SaComponente Float64,
    Cap UInt32,
    Var UInt32,
    Air UInt32,
    Origen String,
    AnioComponente UInt32,
    CodCoberturaAut String,
    CodTipoVeh UInt32,
    CodUsoVeh UInt32,
    PrimaTarifaSupl Float64,
    BonPrimaSupl Float64,
    PremioSupl Float64,
    PremioCobradoSupl Float64,
    CodOrganizador UInt32,
    CodProductor UInt32,
    PrimaTarifaComp Float64,
    PrimaRcTarifaComp Float64,
    PrimaCascoTarifaComp Float64,
    PrimaNetaComp Float64,
    PrimaRcNetaComp Float64,
    PrimaCascoNetaComp Float64
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(FEmision)
ORDER BY (Op, CodRama, Poliza, Supl, Comp, CodCoberturaAut)
SETTINGS index_granularity = 8192;

-- OJO: la MV agrupa por casi todas las columnas, por lo que la agg es casi
-- idéntica a la base. Candidata a rediseño (ver README).
CREATE TABLE IF NOT EXISTS primas_automotores_agg (
    FEmisionMes Date,
    CodOrganizador UInt32,
    CodProductor UInt32,
    CodRama UInt32,
    CodCoberturaAut String,
    CodTipoVeh UInt32,
    CodUsoVeh UInt32,
    AnioComponente UInt32,
    Origen String,
    FVigDesde Date,
    FVigHasta Date,
    Op UInt32,
    Comp UInt32,
    Supl UInt32,
    Poliza UInt32,
    SaComponente Float64,
    Cap UInt32,
    Var UInt32,
    Air UInt32,
    PrimaTarifaSupl Float64,
    BonPrimaSupl Float64,
    PremioSupl Float64,
    PremioCobradoSupl Float64,
    PrimaTarifaComp Float64,
    PrimaRcTarifaComp Float64,
    PrimaCascoTarifaComp Float64,
    PrimaNetaComp Float64,
    PrimaRcNetaComp Float64,
    PrimaCascoNetaComp Float64
)
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(FEmisionMes)
ORDER BY (FEmisionMes, CodOrganizador, CodProductor, CodRama, CodCoberturaAut, CodTipoVeh, CodUsoVeh, AnioComponente, Origen)
SETTINGS index_granularity = 8192;

CREATE MATERIALIZED VIEW IF NOT EXISTS primas_automotores_agg_mv
TO primas_automotores_agg AS
SELECT
    toStartOfMonth(FEmision) AS FEmisionMes,
    CodOrganizador,
    CodProductor,
    CodRama,
    CodCoberturaAut,
    CodTipoVeh,
    CodUsoVeh,
    AnioComponente,
    Origen,
    FVigDesde,
    FVigHasta,
    Op,
    Comp,
    Supl,
    Poliza,
    SaComponente,
    Cap,
    Var,
    Air,
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
FROM primas_automotores
GROUP BY
    FEmisionMes,
    CodOrganizador,
    CodProductor,
    CodRama,
    CodCoberturaAut,
    CodTipoVeh,
    CodUsoVeh,
    AnioComponente,
    Origen,
    FVigDesde,
    FVigHasta,
    Op,
    Comp,
    Supl,
    Poliza,
    SaComponente,
    Cap,
    Var,
    Air;
