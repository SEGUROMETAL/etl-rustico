CREATE TABLE IF NOT EXISTS dim_localidades (
    Cp UInt32,
    CpSufijo UInt32,
    Localidad String,
    CodProvinciaStr LowCardinality(String),
    CodProvInder UInt32,
    Provincia LowCardinality(String)
)
ENGINE = MergeTree()
ORDER BY (Cp, CpSufijo);
