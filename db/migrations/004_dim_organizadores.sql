CREATE TABLE IF NOT EXISTS dim_organizadores (
    CodOrganizador UInt32,
    NroPersona UInt32,
    Nombre String,
    Domicilio String,
    Cp UInt32,
    CpSufijo UInt32,
    Localidad String,
    CodProvincia LowCardinality(String),
    TipoDoc LowCardinality(String),
    NroDoc UInt32,
    Cuit String,
    Provincia LowCardinality(String),
    CodInderProvincia LowCardinality(String),
    Matricula UInt32,
    CodGrupo UInt32,
    Grupo String,
    version DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(version)
ORDER BY (CodOrganizador);
