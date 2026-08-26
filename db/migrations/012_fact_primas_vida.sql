-- Reconstruido desde el schema de Polars del ETL.
-- Verificar contra producción: SHOW CREATE TABLE primas_vida
CREATE TABLE IF NOT EXISTS primas_vida (
    FEmision Date,
    FVigDesde Date,
    FVigHasta Date,
    Op Int64,
    CodRama Int64,
    Poliza Int64,
    Suplemento Int64,
    Componente Int64,
    CodRiesgo Int64,
    Riesgo String,
    CodCobertura Int64,
    Cobertura String,
    CodOrganizador Int64,
    CodProductor Int64,
    SaSuplemento Float64,
    NomAsegurado String,
    CuitAsegurado String,
    Cp String,
    CpSufijo String,
    Localidad String,
    CodProvincia String,
    PormilajeCobertura Float64,
    PrimaTarifaCobertura Float64,
    PrimaTarifaSuplemento Float64,
    PctBonPrima Float64,
    PremioSuplemento Float64,
    DescOperacion String,
    PolizaAnterior Int64,
    PolizaPosterior Int64,
    PrimaNetaSuplemento Float64,
    PrimaNetaCobertura Float64
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(FEmision)
ORDER BY (Op, Suplemento, Componente, CodCobertura);
