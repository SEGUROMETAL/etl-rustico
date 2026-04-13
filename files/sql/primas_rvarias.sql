CREATE TABLE IF NOT EXISTS primas_rvarias
(
  FEmision Date,
  FVigDesde Date,
  FVigHasta Date,
  Op UInt32,
  CodRama UInt32,
  Poliza UInt32,
  Supl UInt32,
  Comp UInt32,
  CodOrganizador UInt32,
  CodProductor UInt32,
  CodRiesgo UInt32,
  Riesgo String,
  CodCobertura UInt32,
  Cobertura String,
  CodProvincia String,
  SaCobertura Float32,
  PremioBrutoSuplemento Float32,
  BonPrimaPorc Float32,
  Pormilaje Float32,
  PrimaTarifaSuplemento Float32,
  PrimaTarifaCobertura Float32,
  PrimaNetaSuplemento Float32,
  PrimaNetaCobertura Float32
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(FEmision)
ORDER BY (toYYYYMM(FEmision), CodRama, CodOrganizador, CodProductor, CodCobertura, CodProvincia);


CREATE TABLE IF NOT EXISTS primas_rvarias_agg_reaseguro
(
  FEmisionMes Date,
  CodRama UInt32,
  CodOrganizador UInt32,
  CodProductor UInt32,
  CodRiesgo UInt32,
  Riesgo String,
  CodCobertura UInt32,
  Cobertura String,
  CodProvincia String,
  SaCoberturaMillones Float32,
  SaCoberturaSuma Float32,
  SaCoberturaMin Float32,
  SaCoberturaMax Float32,
  PrimaTarifaCobertura Float32,
  PrimaNetaCobertura Float32
)
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(FEmisionMes)
ORDER BY (
  toYYYYMM(FEmisionMes),
  CodRama,
  CodOrganizador,
  CodProductor,
  CodCobertura,
  SaCoberturaMillones,
  CodProvincia
);

--


CREATE MATERIALIZED VIEW primas_rvarias_agg_reaseguro_mv
TO primas_rvarias_agg_reaseguro AS
SELECT
  toStartOfMonth(FEmision) AS FEmisionMes,
  CodRama,
  CodOrganizador,
  CodProductor,
  CodRiesgo,
  Riesgo,
  CodCobertura,
  Cobertura,
  CodProvincia,
  round(SaCobertura/1000000.0) AS SaCoberturaMillones,
  sum(SaCobertura) AS SaCoberturaSuma,
  min(SaCobertura) AS SaCoberturaMin,
  max(SaCobertura) AS SaCoberturaMax,
  sum(PrimaTarifaCobertura) AS PrimaTarifaCobertura,
  sum(PrimaNetaCobertura) AS PrimaNetaCobertura
FROM primas_rvarias
GROUP BY
  toStartOfMonth(FEmision),
  CodRama,
  CodOrganizador,
  CodProductor,
  CodRiesgo,
  Riesgo,
  CodCobertura,
  Cobertura,
  round(SaCobertura/1000000.0),
  CodProvincia;
