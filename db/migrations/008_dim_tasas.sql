CREATE TABLE IF NOT EXISTS dim_tasas_scd (
    NumTarifa UInt32,
    Cap UInt32,
    Air UInt32,
    CodCobertura LowCardinality(String),
    segmento_ant UInt32,
    AntMinima UInt32,
    AntMaxima UInt32,
    TasaAnual Float32,
    fecha_desde Date
)
ENGINE = MergeTree
ORDER BY (NumTarifa, Cap, Air, CodCobertura, segmento_ant, fecha_desde);

CREATE TABLE IF NOT EXISTS dim_tasas_actual (
    NumTarifa UInt32,
    Cap UInt32,
    Air UInt32,
    CodCobertura LowCardinality(String),
    segmento_ant UInt32,
    AntMinima UInt32,
    AntMaxima UInt32,
    TasaAnual Float32,
    fecha_desde Date
)
ENGINE = ReplacingMergeTree(fecha_desde)
ORDER BY (NumTarifa, Cap, Air, CodCobertura, segmento_ant);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dim_tasas_actual
TO dim_tasas_actual AS
SELECT
    NumTarifa,
    Cap,
    Air,
    CodCobertura,
    segmento_ant,
    AntMinima,
    AntMaxima,
    TasaAnual,
    fecha_desde
FROM dim_tasas_scd;
