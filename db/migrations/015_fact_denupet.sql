-- Reconstruido desde el schema de Polars del ETL.
-- Verificar contra producción: SHOW CREATE TABLE denupet
CREATE TABLE IF NOT EXISTS denupet (
    Op UInt32,
    CodRama UInt32,
    Poliza UInt32,
    Supl UInt32,
    Comp UInt32,
    Siniestro UInt32,
    FechaDenuncia Date,
    FechaSiniestro Date,
    CodCausa UInt32,
    Causa String,
    DireccionSiniestro String,
    CpSiniestro UInt32,
    CodOrganizador UInt32,
    CodProductor UInt32,
    NroAsegurado UInt32
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(FechaDenuncia)
ORDER BY (Op, Siniestro, Comp);
