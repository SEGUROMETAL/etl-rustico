CREATE TABLE IF NOT EXISTS dim_coberturas_rv (
    CodRama UInt32,
    CodCobertura UInt32,
    Cobertura String,
    Pormilaje Float32,
    Informe LowCardinality(String)
)
ENGINE = MergeTree()
ORDER BY (Informe, CodRama, CodCobertura);
