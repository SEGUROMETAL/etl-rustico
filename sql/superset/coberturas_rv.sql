CREATE TABLE IF NOT EXIST dim_coberturas_rv
(
    CodRama UInt32,
    CodCobertura UInt32,
    Cobertura String,
    Pormilaje Float32,
    Informe LowCardinality(String),
    fd Date,
    fh Date
)
ENGINE = MergeTree()
ORDER BY (CodRama, CodCobertura, fd);

CREATE TABLE IF NOT EXIST dim_coberturas_rv_current
(
    CodRama UInt32,
    CodCobertura UInt32,
    Cobertura String,
    Pormilaje Float32,
    Informe LowCardinality(String)
)
ENGINE = ReplacingMergeTree()
ORDER BY (Informe, CodRama, CodCobertura);

CREATE MATERIALIZED VIEW IF NOT EXIST mv_dim_coberturas_rv_to_current
TO dim_coberturas_rv_current
AS
SELECT
	CodRama,
	CodCobertura,
	argMax(Cobertura, fd) AS Cobertura,
	argMax(Pormilaje, fd) AS Pormilaje,
	argMax(Informe, fd) AS Informe
FROM
	dim_coberturas_rv
GROUP BY
	CodRama,
	CodCobertura;