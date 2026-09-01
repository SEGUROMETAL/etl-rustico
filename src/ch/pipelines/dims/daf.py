import time

import polars as pl

from ch.connections import ch_client, mysql_engine
from ch.loading import df_from_ch, insert_df
from ch.log import logger
from ch.paths import DAF_FILES
from ch.pipelines.dims.daf_transforms import (
    agrupar_por_documento,
    cuit_invalido,
    desbloquear_grupos,
    dni_invalido,
    normalizar_daf,
    preparar_salida,
    resolver_cadena_grupos,
)
from ch.registry import register


def _informes_calidad(daf: pl.DataFrame) -> None:
    """Exporta a files/daf los Excel de control de calidad de grupos."""
    daf.filter(pl.col("Grupo") > 0).with_columns(
        [
            (pl.col("Bloqueado") == "_").sum().over("Grupo").alias("No Bloqueados"),
            (pl.col("Bloqueado") == "S").sum().over("Grupo").alias("Bloqueados"),
        ]
    ).filter(pl.col("No Bloqueados") > 1).sort("Grupo").select(
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
    ).write_excel(DAF_FILES / "Grupos_mas_de_un_habilitado.xlsx")

    daf.filter(pl.col("NroPersona").is_in(daf["Grupo"].to_list())).filter(
        pl.col("NroPersona") != pl.col("Grupo")
    ).write_excel(DAF_FILES / "Personas_que_son_grupo_y_pertenecen_a_otro_grupo.xlsx")

    daf.with_columns(
        pl.col("NroPersona").n_unique().over("Grupo").alias("PersonasEnElGrupo")
    ).filter(pl.col("NroPersona").is_in(daf["Grupo"].to_list())).filter(
        pl.col("Bloqueado") == "S"
    ).join(daf.select(["Grupo", "NroPersona"]), how="inner", on="Grupo", suffix="_p").group_by(
        pl.exclude("NroPersona_p")
    ).agg(pl.col("NroPersona_p").unique().implode().alias("Personas_del_grupo")).sort(
        "PersonasEnElGrupo", descending=True
    ).write_excel(DAF_FILES / "Personas_que_son_grupo_y_estan_bloqueadas.xlsx")

    (
        daf.filter(~(cuit_invalido() & dni_invalido()))
        .with_columns(
            [
                pl.when(~cuit_invalido())
                .then(pl.len().over("Cuit"))
                .otherwise(None)
                .alias("Pers_x_Cuit"),
                (pl.col("Grupo").max().over("Cuit")).alias("MaxGrupo_x_Cuit"),
                pl.when(~dni_invalido())
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
        .select(
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
        )
        .sort("NroDocumento", "Cuit")
        .write_excel(DAF_FILES / "singrupo.xlsx")
    )

    validos = ~(cuit_invalido() & dni_invalido())
    (
        daf.filter(validos)
        .with_columns(
            [
                pl.when(~cuit_invalido())
                .then(pl.len().over("Cuit"))
                .otherwise(None)
                .alias("Pers_x_Cuit"),
                pl.when(~cuit_invalido())
                .then(pl.col("Grupo").n_unique().over("Cuit"))
                .otherwise(None)
                .alias("Gru_x_Cuit"),
                pl.when(~dni_invalido())
                .then(pl.len().over("NroDocumento"))
                .otherwise(None)
                .alias("Pers_x_Dni"),
                pl.when(~dni_invalido())
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
        .write_excel(
            DAF_FILES / "incoherencias.xlsx",
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
    )


@register(
    "dim-daf",
    "dimensiones",
    "Asegurados (GNHDAF): normalización de grupos + informes Excel de calidad",
)
def run() -> None:
    logger.info("Extrayendo GNHDAF de MySQL...")
    daf = pl.read_database(
        """SELECT DFNRDF AS NroPersona,
                  DFNOMB AS Nombre,
                  DFDOMI AS Domicilio,
                  DFCOPO AS Cp,
                  DFCOPS AS CpSufijo,
                  DFNRDO AS NroDocumento,
                  DFCUIT AS Cuit,
                  CAST(DFFNAC AS CHAR) as FechaNac,
                  DFSEXO AS Sexo,
                  DFBLOQ AS Bloqueado,
                  DFNRD1 as Grupo
           FROM GNHDAF""",
        connection=mysql_engine(),
    )

    daf = normalizar_daf(daf)
    logger.info("Generando informes de calidad en %s...", DAF_FILES)
    _informes_calidad(daf)

    daf = desbloquear_grupos(resolver_cadena_grupos(daf))
    daf = agrupar_por_documento(daf)

    batch_version = int(time.time() * 1_000_000)
    salida = preparar_salida(daf, batch_version)

    with ch_client() as ch:
        n = insert_df(ch, "dim_daf", salida)
        total = df_from_ch(ch, "SELECT count() AS n FROM dim_daf")
    logger.info("dim_daf: insertadas %s filas (total tabla: %s)", n, total.item(0, 0))
