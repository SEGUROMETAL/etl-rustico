DROP TABLE IF EXISTS ss_perfil_agentes;

CREATE TABLE ss_perfil_agentes (
    `Año` UInt16,
    `Mes` UInt8,
    `CodRama` UInt32,
    `Rama` LowCardinality(String),
    `FullRama` LowCardinality(String),
    `GrupoOrganizador` String,
    `CodOrganizador` UInt32,
    `NomOrganizador` LowCardinality(String),
    `FullOrganizador` LowCardinality(String),
    `CodProductor` UInt32,
    `NomProductor` String,
    `FullProductor` LowCardinality(String),
    `PrimaNeta` Float64,
    `RecAdm` Float64,
    `RecFin` Float64,
    `RecCapital` Float64,
    `ImporteSiniestro` Float64,
    `Resultado` Float64,
    `SiniestrosPagados` UInt64,
    `Denuncias` UInt64
) 
ENGINE = SummingMergeTree
PARTITION BY (`Año`, `Mes`)
ORDER BY (`Año`, `Mes`, `CodRama`, `CodOrganizador`, `CodProductor`)
SETTINGS index_granularity = 8192;

INSERT INTO ss_perfil_agentes
SELECT
    `Año`,
    `Mes`,
    `CodRama`,
    '' AS Rama,
    '' AS FullRama,
    `GrupoOrganizador`,
    `CodOrganizador`,
    `NomOrganizador`,
    `CodOrganizador` || ' - ' || `NomOrganizador` AS FullOrganizador,
    `CodProductor`,
    `NomProductor`,
    `CodProductor` || ' - ' || `NomProductor` AS FullProductor,
    `PrimaNeta`,
    `RecAdm`,
    `RecFin`,
    `RecCapital`,
    `ImporteSiniestro`,
    `Resultado`,
    `SiniestrosPagados`,
    `Denuncias`
FROM
    v_perfiles_prima_siniestros_denuncias;