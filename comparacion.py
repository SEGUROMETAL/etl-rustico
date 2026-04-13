from db.engines import get_engine_mysql
import polars as pl


data_ssn = pl.read_excel("Pzas gastos SIEP.xlsx").select(
    [
        pl.col("codigo_ramo").alias("cod_ramo_ssn"),
        pl.when(pl.col("codigo_ramo") == 1030)
        .then(pl.lit(4))
        .otherwise(pl.lit(44))
        .alias("cod_rama"),
        pl.col("nro_poliza").cast(pl.Int32),
    ]
)

data_sehpm151t = pl.read_database(
    query="""SELECT
                st.M1RAMA as cod_rama ,
                st.M1POLI as nro_poliza,
                st.M1ORG1 as cod_org,
                do.NomOrganizador as nom_org,
                st.M1PRO1 as cod_prod,
                dp.NomProductor as nom_prod,
                st.MABPRE + st.MAPRIM as prima_tarifa,
                st.MABPRE as bon_prima,
                st.MAPRIM as prima_neta,
                st.ComOrg as com_org,
                st.ComProd as com_prod
            from
                SEHPM151T st
            left JOIN dims_productores dp on
                st.M1PRO1 = dp.CodProductor
            left JOIN dims_organizadores do on
                st.M1ORG1 = do.CodOrganizador
        WHERE
            st.M1RAMA IN (4, 44)
            and not ISNULL(st.ComProd)
            and (st.M1FEMA * 100 + st.M1FEMM ) >= 202506
            and st.M1SUOP = 0; """,
    connection=get_engine_mysql(),
    schema_overrides={
        "cod_rama": pl.Int32,
        "nro_poliza": pl.Int32,
        "prima_tarifa": pl.Float32,
        "bon_prima": pl.Float32,
        "prima_neta": pl.Float32,
        "com_org": pl.Float32,
        "com_prod": pl.Float32,
    },
)

joined_data = (
    data_ssn.join(
        data_sehpm151t,
        how="left",
        on=[
            "cod_rama",
            "nro_poliza",
        ],
    )
    .with_columns(
        [
            (pl.col("com_org") + pl.col("com_prod")).alias("com_total"),
            (
                (pl.col("com_org") + pl.col("com_prod")) * 100 / pl.col("prima_neta")
            ).alias("%com_total"),
            (pl.col("com_prod") * 100 / pl.col("prima_neta")).alias("%com_prod"),
            (pl.col("com_org") * 100 / pl.col("prima_neta")).alias("%com_org"),
        ]
    )
    .sort(["cod_rama", "nro_poliza"])
    .select(
        [
            "cod_ramo_ssn",
            "cod_rama",
            "nro_poliza",
            "prima_tarifa",
            "bon_prima",
            "prima_neta",
            "cod_org",
            "nom_org",
            "cod_prod",
            "nom_prod",
            "com_org",
            "%com_org",
            "com_prod",
            "%com_prod",
            "com_total",
            "%com_total",
        ]
    )
)

joined_data.write_excel(
    "comisiones_contra_ssn.xlsx",
    column_formats={
        "codigo_ramo": "0",
        "nro_poliza": "0",
    },
    dtype_formats={pl.Int32: "#", pl.Float32: "0.00"},
    autofit=True,
)


import os

os.startfile("comisiones_contra_ssn.xlsx")
