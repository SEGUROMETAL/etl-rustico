CREATE TABLE IF NOT EXISTS dim_coberturas_aut (
    CodCobertura String,
    OrCobertura UInt32,
    CatCobertura String,
    OrCatCobertura UInt32,
    Rt UInt16,
    Rp UInt16,
    It UInt16,
    Ip UInt16,
    At UInt16,
    Ap UInt16,
    version DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(version)
ORDER BY (CodCobertura);
