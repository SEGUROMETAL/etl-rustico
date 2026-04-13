create table if not exists dim_localidades (
    Cp UInt32,
    CpSufijo UInt32,
    Localidad String,
    CodProvinciaStr LowCardinality(String),
    CodProvInder UInt32,
    Provincia LowCardinality(String)
) Engine MergeTree()
order by
    (Cp, CpSufijo);


CREATE VIEW localidades_sufijo_x_provincia_cp_segun_prima AS WITH cps AS (
    SELECT
        sum(PrimaNeta) OVER (
            PARTITION BY ProvinciaAsegurado,
            CpAsegurado,
            CpSufijoAsegurado
        ) AS prima,
        ProvinciaAsegurado,
        CpAsegurado,
        CpSufijoAsegurado
    FROM
        sehpm151t
    WHERE
        CodTipoOp <= 2
)
SELECT
    ProvinciaAsegurado as Provincia,
    CpAsegurado as Cp,
    argMax(CpSufijoAsegurado, prima) AS CpSufijo
FROM
    cps
GROUP BY
    ProvinciaAsegurado,
    CpAsegurado
ORDER BY
    CpAsegurado;