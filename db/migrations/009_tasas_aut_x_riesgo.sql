-- Tabla derivada: se calcula dentro de ClickHouse a partir de dim_tasas_actual + dim_coberturas_aut.
CREATE TABLE IF NOT EXISTS tasas_aut_x_riesgo (
    NumTarifa UInt32,
    Cap UInt32,
    Air UInt32,
    segmento_ant UInt32,
    AntMinima Int32,
    AntMaxima Int32,
    CodCobertura LowCardinality(String),
    TasaAnual Float64,
    Habilitado UInt16,
    TasaIt Float64,
    TasaRt Float64,
    TasaAt Float64,
    TasaIp Float64,
    TasaRp Float64,
    TasaAp Float64
)
ENGINE = MergeTree()
ORDER BY (NumTarifa, Cap, Air, segmento_ant, CodCobertura, AntMinima, AntMaxima);
