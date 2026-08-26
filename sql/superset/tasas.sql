CREATE TABLE dim_tasas_scd (
    NumTarifa UInt32,
    Cap UInt32,
    Air UInt32,
    CodCobertura LowCardinality(String),
    segmento_ant UInt32,
    AntMinima UInt32,
    AntMaxima UInt32,
    TasaAnual Float32,
    fecha_desde Date
) ENGINE = MergeTree
ORDER BY
    (NumTarifa, Cap, Air, segmento_ant, fecha_desde);


CREATE TABLE dim_tasas_actual (
    NumTarifa UInt32,
    Cap UInt32,
    Air UInt32,
    CodCobertura LowCardinality(String),
    segmento_ant UInt32,
    AntMinima UInt32,
    AntMaxima UInt32,
    TasaAnual Float32,
    fecha_desde Date
) ENGINE = ReplacingMergeTree(fecha_desde)
ORDER BY
    (NumTarifa, Cap, Air, segmento_ant);


CREATE MATERIALIZED VIEW mv_dim_tasas_actual TO dim_tasas_actual AS
SELECT
    NumTarifa,
    Cap,
    Air,
    CodCobertura,
    segmento_ant,
    AntMinima,
    AntMaxima,
    TasaAnual,
    fecha_desde
FROM
    dim_tasas_scd;


---
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
    TasaRt Float64,
    TasaIt Float64,
    TasaRp Float64,
    TasaIp Float64,
    TasaAt Float64,
    TasaAp Float64
) Engine = MergeTree()
Order BY
    (
        NumTarifa,
        Cap,
        Air,
        segmento_ant,
        CodCobertura,
        AntMinima,
        AntMaxima
    );


--
WITH sinant AS (
    SELECT
        NumTarifa,
        Cap,
        Air,
        anyIf(TasaAnual, CodCobertura = 'C2') AS tasaC2,
        anyIf(TasaAnual, CodCobertura = 'C5') AS tasaC5,
        anyIf(TasaAnual, CodCobertura = 'B5') AS tasaB5,
        anyIf(TasaAnual, CodCobertura = 'C4') AS tasaC4,
        anyIf(TasaAnual, CodCobertura = 'B4') AS tasaB4
    FROM
        reportes.dim_tasas_actual FINAL
    WHERE
        NOT (CodCobertura LIKE 'D%')
    GROUP BY
        NumTarifa,
        Cap,
        Air
),
conant AS (
    SELECT
        NumTarifa,
        Cap,
        Air,
        segmento_ant,
        anyIf(TasaAnual, CodCobertura = 'C2') AS tasaC2,
        anyIf(TasaAnual, CodCobertura = 'C5') AS tasaC5,
        anyIf(TasaAnual, CodCobertura = 'B5') AS tasaB5,
        anyIf(TasaAnual, CodCobertura = 'C4') AS tasaC4,
        anyIf(TasaAnual, CodCobertura = 'B4') AS tasaB4
    FROM
        reportes.dim_tasas_actual FINAL
    GROUP BY
        NumTarifa,
        Cap,
        Air,
        segmento_ant
),
parcial as (
    SELECT
        NumTarifa,
        Cap,
        Air,
        segmento_ant,
        AntMinima,
        AntMaxima,
        CodCobertura,
        TasaAnual,
        greatest(c.tasaC2, s.tasaC2) as tasaC2,
        greatest(c.tasaC4, s.tasaC4) as tasaC4,
        greatest(c.tasaC5, s.tasaC5) as tasaC5,
        greatest(c.tasaB4, s.tasaB4) as tasaB4,
        greatest(c.tasaB5, s.tasaB5) as tasaB5
    FROM
        dim_tasas_actual AS t FINAL
        LEFT JOIN conant AS c USING (NumTarifa, Cap, Air, segmento_ant)
        LEFT JOIN sinant AS s USING (NumTarifa, Cap, Air)
    where
        TasaAnual Between 0.01
        and 998
)
SELECT
    NumTarifa,
    Cap,
    Air,
    segmento_ant,
    AntMinima,
    AntMaxima,
    CodCobertura,
    TasaAnual,
    least(tasaC2, tasaC4, tasaC5, tasaB4, tasaB5) > 0 as Habilitado,
    tasaB4 * It as TasaIt,
    greatest(least(TasaAnual - TasaIt, tasaB5), 0) * Rt AS TasaRt,
    greatest(
        least(
            TasaAnual - TasaRt - TasaIt,
            (tasaC2 - tasaC5) - tasaC4
        ),
        0
    ) * At AS TasaAt,
    greatest(
        least(
            ((TasaAnual - TasaRt) - TasaIt) - TasaAt,
            tasaC4 - tasaB4
        ),
        0
    ) * Ip AS TasaIp,
    greatest(
        least(
            TasaAnual - TasaRt - TasaIt - TasaAt - TasaIp,
            tasaC5 - tasaB5
        ),
        0
    ) * Rp AS TasaRp,
    greatest(
        TasaAnual - TasaRt - TasaIt - TasaAt - TasaIp - TasaRp,
        0
    ) AS TasaAp
from
    parcial
    LEFT JOIN dim_coberturas_aut AS dcob USING (CodCobertura)