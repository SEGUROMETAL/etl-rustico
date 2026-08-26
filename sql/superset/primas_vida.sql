CREATE TABLE if not exists primas_vida (
  Op UInt32,
  CodRama UInt32,
  Poliza UInt32,
  Suplemento UInt32,
  Componente UInt32,
  CodRiesgo Int64,
  CodCobertura UInt32,
  CodOrganizador UInt32,
  CodProductor UInt32,
  FEmision Date,
  FVigDesde Date,
  CantComponentes UInt32,
  SaSuplemento UInt32,
  PormilajeCobertura Float64,
  PrimaTarifaCobertura Float64,
  PrimaTarifaSuplemento Float64,
  PctBonPrima Float64,
  PremioSuplemento Float64,
  CantDias Int64,
  DescOperacion LowCardinality(String),
  PrimaNetaSuplemento Float64,
  PrimaNetaCobertura Float64,
  CodProvincia LowCardinality(String),
) ENGINE = MergeTree PARTITION BY toYYYYMM(FEmision)
ORDER BY
  (
    FEmision,
    CodRama,
    CodOrganizador,
    CodProductor,
    CodCobertura
  );