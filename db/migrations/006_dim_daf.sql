CREATE TABLE IF NOT EXISTS dim_daf (
    NroPersona UInt64,
    persona_key UInt64,
    Cuit String,
    NroDocumento String,
    Sexo String,
    Nombre String,
    Domicilio String,
    Cp LowCardinality(String),
    CpSufijo String,
    Bloqueado UInt8,
    EsDelegado UInt8,
    last_update DateTime,
    version UInt64
)
ENGINE = ReplacingMergeTree(version)
ORDER BY (NroPersona);

CREATE VIEW IF NOT EXISTS v_dim_daf_actual AS
SELECT
    NroPersona,
    argMax(persona_key, version) AS persona_key,
    argMax(Cuit, version) AS Cuit,
    argMax(NroDocumento, version) AS NroDocumento,
    argMax(Sexo, version) AS Sexo,
    argMax(Nombre, version) AS Nombre,
    argMax(Domicilio, version) AS Domicilio,
    argMax(Cp, version) AS Cp,
    argMax(CpSufijo, version) AS CpSufijo,
    argMax(Bloqueado, version) AS Bloqueado,
    argMax(EsDelegado, version) AS EsDelegado,
    argMax(last_update, version) AS last_update
FROM dim_daf
GROUP BY NroPersona;
