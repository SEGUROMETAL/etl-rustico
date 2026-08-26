"""Transformaciones puras del pipeline DAF (sin I/O, testeables)."""

import datetime

import polars as pl


def cuit_invalido() -> pl.Expr:
    return (
        (pl.col("Cuit").str.len_chars() != 11)
        | (pl.col("Cuit") == "20000999998")
        | (~(pl.col("Cuit").str.starts_with("2") | pl.col("Cuit").str.starts_with("3")))
        | _digitos_todos_iguales("Cuit", desde=4)
    )


def dni_invalido() -> pl.Expr:
    return (
        (pl.col("NroDocumento") == 0)
        | (pl.col("NroDocumento") == 99999999)
        | (pl.col("NroDocumento") < 1000000)
        | _digitos_todos_iguales("NroDocumento", desde=2, cast_string=True)
    )


def _digitos_todos_iguales(col: str, desde: int, cast_string: bool = False) -> pl.Expr:
    """True si todos los dígitos desde `desde` son iguales entre sí."""
    expr = pl.col(col).cast(pl.String) if cast_string else pl.col(col)
    return (
        expr.str.slice(desde).str.extract_all(".").list.n_unique() <= 1
    )


def normalizar_daf(daf: pl.DataFrame) -> pl.DataFrame:
    """Limpia nombres, fechas, sexo y marca el grupo inicial."""
    grupos = (
        daf.filter((pl.col("Grupo").is_not_null()) & (pl.col("Grupo") > 0))["Grupo"]
        .unique()
        .to_list()
    )
    fnac = pl.col("FechaNac").str.to_date("%Y-%m-%d", strict=False)
    return daf.select(
        [
            "NroPersona",
            pl.col("Nombre").str.strip_chars().str.to_titlecase(),
            pl.col("Domicilio").str.strip_chars().str.to_titlecase(),
            "Cp",
            "CpSufijo",
            "NroDocumento",
            "Cuit",
            pl.when(fnac.dt.year() == 1).then(None).otherwise(fnac).alias("FechaNac"),
            (
                pl.when(pl.col("Sexo") == 1)
                .then(pl.lit("M"))
                .when(pl.col("Sexo") == 2)
                .then(pl.lit("F"))
                .otherwise(None)
                .alias("Sexo")
            ),
            "Bloqueado",
            (
                pl.when(pl.col("Grupo").is_not_null() & (pl.col("Grupo") != 0))
                .then(pl.col("Grupo"))
                .when(pl.col("NroPersona").is_in(grupos))
                .then(pl.col("NroPersona"))
                .otherwise(None)
                .alias("Grupo")
            ).fill_null(0),
        ]
    )


def resolver_cadena_grupos(daf: pl.DataFrame, max_iter: int = 20) -> pl.DataFrame:
    """Si una persona es cabeza de grupo pero pertenece a otro grupo, su grupo pasa a
    ser ella misma. Repite hasta punto fijo (con tope de iteraciones)."""
    for _ in range(max_iter):
        pendientes = daf.filter(
            pl.col("NroPersona").is_in(daf["Grupo"].to_list())
            & (pl.col("NroPersona") != pl.col("Grupo"))
        )
        if pendientes.is_empty():
            break
        daf = daf.with_columns(
            pl.when(
                pl.col("NroPersona").is_in(pendientes["NroPersona"].to_list())
            )
            .then(pl.col("NroPersona"))
            .otherwise(pl.col("Grupo"))
            .alias("Grupo")
        )
    return daf


def desbloquear_grupos(daf: pl.DataFrame) -> pl.DataFrame:
    x_es_grupo = pl.col("NroPersona").is_in(daf["Grupo"].to_list())
    return daf.with_columns(
        pl.when(x_es_grupo & (pl.col("Bloqueado") == "S"))
        .then(pl.lit("_"))
        .otherwise(pl.col("Bloqueado"))
        .alias("Bloqueado")
    )


def agrupar_por_documento(daf: pl.DataFrame) -> pl.DataFrame:
    """Unifica grupos por CUIT válido y luego por DNI+Sexo válidos."""
    x_cuit_malo = cuit_invalido()
    x_dni_malo = dni_invalido()

    x_personas_x_cuit = pl.len().over("Cuit")
    x_max_grupo_x_cuit = pl.col("Grupo").max().over("Cuit")
    x_cant_grupos_x_cuit = pl.col("Grupo").n_unique().over("Cuit")
    x_max_nro_persona_x_cuit = pl.col("NroPersona").max().over("Cuit")

    daf = daf.with_columns(
        pl.when(
            (~x_cuit_malo)
            & (x_personas_x_cuit > 1)
            & (x_cant_grupos_x_cuit > 1)
        )
        .then(x_max_grupo_x_cuit)
        .when((~x_cuit_malo) & (x_personas_x_cuit > 1) & (x_max_grupo_x_cuit == 0))
        .then(x_max_nro_persona_x_cuit)
        .otherwise(pl.col("Grupo"))
        .alias("Grupo")
    )

    x_personas_x_dni = pl.len().over(["NroDocumento", "Sexo"])
    x_max_grupo_x_dni = pl.col("Grupo").max().over(["NroDocumento", "Sexo"])
    x_cant_grupos_x_dni = pl.col("Grupo").n_unique().over(["NroDocumento", "Sexo"])
    x_max_nro_persona_x_dni = pl.col("NroPersona").max().over(["NroDocumento", "Sexo"])

    daf = daf.with_columns(
        pl.when(
            (~x_dni_malo) & (x_personas_x_dni > 1) & (x_cant_grupos_x_dni > 1)
        )
        .then(x_max_grupo_x_dni)
        .when((~x_dni_malo) & (x_personas_x_dni > 1) & (x_max_grupo_x_dni == 0))
        .then(x_max_nro_persona_x_dni)
        .when(pl.col("Grupo") == 0)
        .then(pl.col("NroPersona"))
        .otherwise(pl.col("Grupo"))
        .alias("Grupo")
    )
    return daf


def preparar_salida(
    daf: pl.DataFrame,
    batch_version: int,
    now: datetime.datetime | None = None,
) -> pl.DataFrame:
    x_es_grupo = pl.col("NroPersona").is_in(daf["Grupo"].to_list())
    return (
        daf.with_row_index("row_id")
        .with_columns(x_es_grupo.alias("EsDelegado").cast(pl.UInt16))
        .with_columns(
            [
                (pl.lit(batch_version) + pl.col("row_id").cast(pl.UInt64)).alias(
                    "version"
                ),
                pl.lit(now or datetime.datetime.now()).alias("last_update"),
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
