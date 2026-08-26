CREATE TABLE IF NOT EXISTS dim_rc_scd (
    NumTarifa UInt32,
    Cap UInt32,
    Var UInt32,
    RcSl Float32,
    RcCl Float32,
    RcExt Float32,
    RcAp Float32,
    RcObl Float32,
    fecha_desde Date
)
ENGINE = MergeTree
ORDER BY (NumTarifa, Cap, Var, fecha_desde);

CREATE TABLE IF NOT EXISTS dim_rc_actual (
    NumTarifa UInt32,
    Cap UInt32,
    Var UInt32,
    RcSl Float32,
    RcCl Float32,
    RcExt Float32,
    RcAp Float32,
    RcObl Float32,
    fecha_desde Date
)
ENGINE = ReplacingMergeTree(fecha_desde)
ORDER BY (NumTarifa, Cap, Var);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dim_rc_actual
TO dim_rc_actual AS
SELECT
    NumTarifa,
    Cap,
    Var,
    RcSl,
    RcCl,
    RcExt,
    RcAp,
    RcObl,
    fecha_desde
FROM dim_rc_scd;
