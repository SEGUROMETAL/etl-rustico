-- Reconstruido desde el schema de Polars del ETL (la tabla original se creó a mano en CH).
-- Verificar contra producción: SHOW CREATE TABLE primas_rvarias
CREATE TABLE IF NOT EXISTS primas_rvarias (
    FEmision Date,
    FVigDesde Date,
    FVigHasta Date,
    Op UInt32,
    CodRama UInt32,
    Poliza UInt32,
    Supl UInt32,
    Comp UInt32,
    CodOrganizador UInt32,
    CodProductor UInt32,
    CodRiesgo UInt32,
    Riesgo String,
    CodCobertura UInt32,
    Cobertura String,
    CodProvincia String,
    SaCobertura Float32,
    PremioBrutoSuplemento Float32,
    Pormilaje Float32,
    PrimaTarifaSuplemento Float32,
    PrimaTarifaCobertura Float32,
    PrimaNetaSuplemento Float32,
    PrimaNetaCobertura Float32
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(FEmision)
ORDER BY (Op, Supl, Comp, CodCobertura);
