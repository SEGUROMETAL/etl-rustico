from db import get_client_ch, get_engine_mysql
import polars as pl
from pathlib import Path
import time
import datetime


def etl_daf():
    mysql = get_engine_mysql()

    FILES_FOLDER: Path = Path("files")
    FILES_DAF_FOLDER: Path = FILES_FOLDER / "daf"

    x_cuit_invalido = (
        (pl.col("Cuit").str.len_chars() != 11)
        | (pl.col("Cuit") == "20000999998")
        | (
            ~(
                (pl.col("Cuit").str.starts_with("2"))
                | (pl.col("Cuit").str.starts_with("3"))
            )
        )
        | pl.all_horizontal(
            [
                (
                    pl.col("Cuit").str.slice(pos, 1)
                    == pl.col("Cuit").str.slice(10 - 6, 1)
                )
                for pos in range(10 - 6, 10)
            ]
        )
    )
    x_dni_invalido = (
        (pl.col("NroDocumento") == 0)
        | (pl.col("NroDocumento") == 99999999)
        | (pl.col("NroDocumento") < 1000000)
        | pl.all_horizontal(
            [
                (
                    pl.col("NroDocumento").cast(pl.String).str.slice(pos, 1)
                    == pl.col("NroDocumento").cast(pl.String).str.slice(8 - 6, 1)
                )
                for pos in range(8 - 6, 10)
            ]
        )
    )

    # Leemos el daf de la base de datos
    daf = pl.read_database(
        """SELECT
        `DFNRDF` AS NroPersona,
            `DFNOMB` AS Nombre,
            `DFDOMI` AS Domicilio,
            `DFCOPO` AS Cp,
            `DFCOPS` AS CpSufijo,
            `DFNRDO` AS NroDocumento,
            `DFCUIT` AS Cuit,
            CAST(DFFNAC AS CHAR) as FechaNac,
            `DFSEXO` AS Sexo,
            `DFBLOQ` AS Bloqueado,
            DFNRD1 as Grupo
        FROM
            `GNHDAF`;""",
        connection=mysql,
    )

    x_fnac_todate = pl.col("FechaNac").str.to_date("%Y-%m-%d", strict=False)
    grupos = daf.filter((pl.col("Grupo").is_not_null()) & (pl.col("Grupo") > 0))[
        "Grupo"
    ].unique()

    # Transformaciones
    daf = daf.select(
        [
            "NroPersona",
            pl.col("Nombre").str.strip_chars().str.to_titlecase(),
            pl.col("Domicilio").str.strip_chars().str.to_titlecase(),
            "Cp",
            "CpSufijo",
            "NroDocumento",
            "Cuit",
            pl.when(x_fnac_todate.dt.year() == 1)
            .then(None)
            .otherwise(x_fnac_todate)
            .alias("FechaNac"),
            (
                pl.when(pl.col("Sexo") == 1)
                .then(pl.lit("M"))
                .when(pl.col("Sexo") == 2)
                .then(pl.lit("F"))
                .otherwise(None)
                .alias("Sexo")
            ),
            # (pl.col("Bloqueado") == "S"),
            "Bloqueado",
            (
                pl.when(pl.col("Grupo").is_not_null() & (pl.col("Grupo") != 0))
                .then(pl.col("Grupo"))
                .when(pl.col("NroPersona").is_in(grupos.to_list()))
                .then(pl.col("NroPersona"))
                .otherwise(None)
                .alias("Grupo")
            ).fill_null(0),
        ]
    )

    # Grupos con mas de un No Bloqueado
    daf.filter(pl.col("Grupo") > 0).with_columns(
        [
            (pl.col("Bloqueado") == "_").sum().over("Grupo").alias("No Bloqueados"),
            (pl.col("Bloqueado") == "S").sum().over("Grupo").alias("Bloqueados"),
        ]
    ).select(
        [
            "Grupo",
            "Nombre",
            "NroPersona",
            "NroDocumento",
            "Cuit",
            "Bloqueado",
            "No Bloqueados",
            "Bloqueados",
        ]
    ).sort("Grupo").filter(pl.col("No Bloqueados") > 1).write_excel(
        FILES_DAF_FOLDER / "Grupos_mas_de_un_habilitado.xlsx"
    )

    # Personas que son grupo y pertenecen a otro grupo

    daf.filter(pl.col("NroPersona").is_in(daf["Grupo"].to_list())).filter(
        pl.col("NroPersona") != pl.col("Grupo")
    ).write_excel(
        FILES_DAF_FOLDER / "Personas_que_son_grupo_y_pertenecen_a_otro_grupo.xlsx"
    )

    # PersonasEnElGrupo que son grupo y están bloqueados

    daf.with_columns(
        pl.col("NroPersona").n_unique().over("Grupo").alias("PersonasEnElGrupo")
    ).filter(pl.col("NroPersona").is_in(daf["Grupo"].to_list())).filter(
        pl.col("Bloqueado") == "S"
    ).join(
        daf.select(["Grupo", "NroPersona"]), how="inner", on="Grupo", suffix="_p"
    ).group_by(pl.exclude("NroPersona_p")).agg(
        pl.col("NroPersona_p").unique().implode().alias("Personas_del_grupo")
    ).sort("PersonasEnElGrupo", descending=True).write_excel(
        FILES_DAF_FOLDER / "Personas_que_son_grupo_y_estan_bloqueadas.xlsx"
    )

    # Sin grupo
    (
        daf.filter(~(x_cuit_invalido & x_dni_invalido))
        .with_columns(
            [
                pl.when(~x_cuit_invalido)
                .then(pl.len().over("Cuit"))
                .otherwise(None)
                .alias("Pers_x_Cuit"),
                (pl.col("Grupo").max().over("Cuit")).alias("MaxGrupo_x_Cuit"),
                pl.when(~x_dni_invalido)
                .then(pl.len().over("NroDocumento"))
                .otherwise(None)
                .alias("Pers_x_Dni"),
                (pl.col("Grupo").max().over("NroDocumento")).alias("MaxGrupo_x_Dni"),
            ]
        )
        .filter(
            (pl.col("Pers_x_Dni") > 1)
            & (pl.col("MaxGrupo_x_Dni") == 0)
            & (pl.col("Pers_x_Cuit") > 1)
            & (pl.col("MaxGrupo_x_Cuit") == 0)
        )
    ).select(
        [
            "NroDocumento",
            "Cuit",
            "NroPersona",
            "Nombre",
            "Domicilio",
            "Cp",
            "CpSufijo",
            "FechaNac",
            "Sexo",
            "Bloqueado",
            "Grupo",
            "Pers_x_Dni",
            "MaxGrupo_x_Dni",
            "Pers_x_Cuit",
            "MaxGrupo_x_Cuit",
        ]
    ).sort("NroDocumento", "Cuit").write_excel(FILES_DAF_FOLDER / "singrupo.xlsx")

    # Incosistencias
    validos = ~(x_cuit_invalido & x_dni_invalido)

    (
        daf.filter(validos)
        .with_columns(
            [
                pl.when(~x_cuit_invalido)
                .then(pl.len().over("Cuit"))
                .otherwise(None)
                .alias("Pers_x_Cuit"),
                pl.when(~x_cuit_invalido)
                .then(pl.col("Grupo").n_unique().over("Cuit"))
                .otherwise(None)
                .alias("Gru_x_Cuit"),
                pl.when(~x_dni_invalido)
                .then(pl.len().over("NroDocumento"))
                .otherwise(None)
                .alias("Pers_x_Dni"),
                pl.when(~x_dni_invalido)
                .then(pl.col("Grupo").n_unique().over("NroDocumento"))
                .otherwise(None)
                .alias("Gru_x_Dni"),
            ]
        )
        .filter((pl.col("Gru_x_Dni") > 1) | (pl.col("Gru_x_Cuit") > 1))
        .join(
            daf.select("NroPersona", "Nombre", "NroDocumento", "Cuit", "Bloqueado"),
            how="left",
            left_on="Grupo",
            right_on="NroPersona",
            suffix="_grupo",
        )
        .sort("NroDocumento", "Cuit")
    ).write_excel(
        FILES_DAF_FOLDER / "incoherencias.xlsx",
        autofilter=True,
        autofit=True,
        column_formats={
            "Cp": "0",
            "NroPersona": "0",
            "Grupo": "0",
            "NroDocumento": "0",
            "Personas_x_Cuit": "0",
        },
    )

    ######### Grupos

    # Grupos que son su mismo grupo se convierten en su mismo grupo
    x_personas_que_son_grupo = pl.col("NroPersona").is_in(daf["Grupo"].to_list())
    x_personas_que_no_son_su_mismo_grupo = pl.col("NroPersona") != pl.col("Grupo")
    while True:
        if daf.filter(
            x_personas_que_son_grupo & x_personas_que_no_son_su_mismo_grupo
        ).is_empty():
            break
        daf = daf.with_columns(
            pl.when(x_personas_que_son_grupo & x_personas_que_no_son_su_mismo_grupo)
            .then("NroPersona")
            .otherwise("Grupo")
            .alias("Grupo_")
        )

    # Dsbloquear grupos
    x_bloqueadas = pl.col("Bloqueado") == "S"
    daf = daf.with_columns(
        pl.when(x_personas_que_son_grupo & x_bloqueadas)
        .then(pl.lit("_"))
        .otherwise(pl.col("Bloqueado"))
    )

    # Agrupar por cuit
    x_personas_x_cuit = pl.len().over("Cuit")
    x_max_grupo_x_cuit = pl.col("Grupo").max().over("Cuit")
    x_cant_grupos_x_cuit = pl.col("Grupo").n_unique().over("Cuit")
    x_max_nro_persona_x_cuit = pl.col("NroPersona").max().over("Cuit")
    x_max_grupo_x_cuit = pl.col("Grupo").max().over("Cuit")

    daf = daf.with_columns(
        [
            x_cant_grupos_x_cuit.alias("x_cant_grupos_x_cuit"),
            pl.when(
                (~x_cuit_invalido)
                & (x_personas_x_cuit > 1)
                & (x_cant_grupos_x_cuit > 1)
            )
            .then(x_max_grupo_x_cuit)
            .when(
                (~x_cuit_invalido) & (x_personas_x_cuit > 1) & (x_max_grupo_x_cuit == 0)
            )
            .then(x_max_nro_persona_x_cuit)
            .otherwise(pl.col("Grupo"))
            .alias("Grupo"),
        ]
    )

    # Agrupar por DNI
    x_personas_x_dni = pl.len().over(["NroDocumento", "Sexo"])
    x_max_grupo_x_dni = pl.col("Grupo").max().over(["NroDocumento", "Sexo"])
    x_cant_grupos_x_dni = pl.col("Grupo").n_unique().over(["NroDocumento", "Sexo"])
    x_max_nro_persona_x_dni = pl.col("NroPersona").max().over(["NroDocumento", "Sexo"])

    daf = daf.with_columns(
        [
            pl.when(
                (~x_dni_invalido) & (x_personas_x_dni > 1) & (x_cant_grupos_x_dni > 1)
            )
            .then(x_max_grupo_x_dni)
            .when((~x_dni_invalido) & (x_personas_x_dni > 1) & (x_max_grupo_x_dni == 0))
            .then(x_max_nro_persona_x_dni)
            .when(pl.col("Grupo") == 0)
            .then(pl.col("NroPersona"))
            .otherwise(pl.col("Grupo"))
            .alias("Grupo"),
        ]
    )

    batch_version = int(time.time() * 1_000_000)

    daf = (
        daf.with_row_index("row_id")
        .with_columns(x_personas_que_son_grupo.alias("EsDelegado").cast(pl.UInt16))
        .with_columns(
            [
                (pl.lit(batch_version) + pl.col("row_id").cast(pl.UInt64)).alias(
                    "version"
                ),
                pl.lit(datetime.datetime.now()).alias("last_update"),
            ]
        )
        .select(
            [
                "NroPersona",
                pl.col("Grupo").alias("persona_key"),
                "Cuit",
                pl.col("NroDocumento").cast(pl.String),
                "Sexo",
                "Nombre",
                "Domicilio",
                pl.col("Cp").cast(pl.String),
                pl.col("CpSufijo").cast(pl.String),
                (pl.col("Bloqueado").str.to_lowercase() == "s").cast(pl.Int16),
                "EsDelegado",
                "last_update",
                "version",
            ]
        )
    )

    with get_client_ch() as ch:
        create_table = """CREATE TABLE IF NOT EXISTS dim_daf (
                    NroPersona UInt64,
                    persona_key UInt64,
                    Cuit String,
                    NroDocumento String,
                    Sexo String,
                    Nombre String,
                    Domicilio String,
                    Cp LowCardinality(String),
                    CpSufijo String,
                    Bloqueado UInt8,
                    EsDelegado UInt8,
                    last_update DateTime,
                    version UInt64
                ) ENGINE = ReplacingMergeTree(version)
                ORDER BY
                (NroPersona);"""
        ch.command(create_table)

        create_view = """CREATE VIEW if not exists v_dim_daf_actual AS
                SELECT
                    NroPersona,
                    argMax(persona_key, version) AS persona_key,
                    argMax(Cuit, version) AS Cuit,
                    argMax(NroDocumento, version) AS NroDocumento,
                    argMax(Sexo, version) AS Sexo,
                    argMax(Nombre, version) AS Nombre,
                    argMax(Domicilio, version) AS Domicilio,
                    argMax(Cp, version) AS Cp,
                    argMax(CpSufijo, version) AS CpSufijo,
                    argMax(Bloqueado, version) AS Bloqueado,
                    argMax(EsDelegado, version) AS EsDelegado,
                    argMax(last_update, version) AS last_update
                FROM dim_daf
                GROUP BY NroPersona;"""
        ch.command(create_view)

        print("\nDAF")

        ch.insert_arrow(
            "dim_daf",
            daf.to_arrow(),
        )

        print("\tLISTO")
