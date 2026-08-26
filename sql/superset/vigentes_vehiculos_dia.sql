/*
 Columnas excluidas
 -- EstadoComponente String,
 -- Periodo UInt32,
 -- AnioPeriodo UInt32,
 -- MesPeriodo UInt32,
 */
CREATE TABLE IF NOT EXISTS vigentes_vehiculos_dia (
    CodOrganizador UInt32,
    CodProductor UInt32,
    CodRama UInt32,
    Poliza UInt32,
    Supl UInt32,
    Componente UInt32,
    FVigDesde Date,
    FVigHasta Date,
    NroAsegurado UInt32,
    NomAsegurado String,
    CpAsegurado UInt32,
    CpSufijoAsegurado UInt32,
    CodMarca String,
    CodModelo String,
    CodSubModelo String,
    Marca LowCardinality(String),
    Modelo String,
    SubModelo String,
    CvaCapitulo UInt32,
    CvaVariante UInt32,
    CvaDescripcion String,
    AnioVehiculo UInt32,
    CodUsoVehiculo UInt32,
    CodTipoVehiculo UInt32,
    CodCoberturaAut String,
    SumaAsegurada Float32,
    NroMotor String,
    NroChasis String,
    Origen LowCardinality(String),
    NroPersonaPagador UInt32,
    NroPersonaTomador UInt32,
    CodCarroceria LowCardinality(String),
    NomProductor String,
    DomicilioProductor String,
    CpProductor UInt32,
    CpSufijoProductor UInt32,
    LocalidadProductor String,
    CodProvinciaProductor String,
    ProvinciaProductor String,
    CodProvinciaInderProductor UInt32,
    MatriculoProductor UInt32,
    CodGrupoOrganizador UInt32,
    GrupoOrganizador String,
    TarifaMadreLetra LowCardinality(String),
    TarifaHija UInt32,
    Dominio String,
    Ant Int32,
    Fecha Date
) ENGINE = MergeTree() PARTITION BY toYYYYMM(Fecha)
ORDER BY
    (
        Fecha,
        CodOrganizador,
        CodProductor,
        CodCoberturaAut,
        NroAsegurado
    );


CREATE VIEW reportes.v_vv_diaria_resumen_mensual AS WITH diaria AS (
    SELECT
        Fecha,
        count(*) AS cantidad
    FROM
        reportes.vigentes_vehiculos_dia
    GROUP BY
        Fecha
)
SELECT
    toYYYYMM(Fecha) as Mes,
    argMax(Fecha, cantidad) AS maxFecha,
    max(cantidad) AS Maximo,
    argMin(Fecha, cantidad) AS minFecha,
    min(cantidad) AS Minimo,
    count() AS Dias,
    round(avg(cantidad), 0) AS Promedio,
    Maximo - Minimo as Gap,
    round(stddevPop(cantidad), 0) as Std,
    quantile(0.25) (cantidad) as Q1,
    quantile(0.5) (cantidad) as Q2,
    quantile(0.75) (cantidad) as Q3,
    CASE
        when Q2 < Promedio then 'D'
        when Q2 > Promedio then 'I'
        ELSE 'N'
    END as Cola
FROM
    diaria
GROUP BY
    toYYYYMM(Fecha);