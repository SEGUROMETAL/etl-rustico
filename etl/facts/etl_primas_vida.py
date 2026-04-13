import db
import polars as pl
from etl.etl_constantes import TABLA_PRIMAS_VIDA
from datetime import date, timedelta
from rutas import PRIMAS_VIDA


# def etl_primas_vida_desde_csv(folder_into_data: str = ""):
#     """Tomas las primas emitidas  de ramas varias (sin VIDA) y las carga en la tabla primas_vida.

#     Returns:
#         bool: Todo Ok.
#     """
#     opeemirv_dict_cols = {
#         "FEC_EMI": {"col_nueva": "FEmision", "tipo": pl.Date},
#         "VIG_DESDE": {"col_nueva": "FVigDesde", "tipo": pl.Date},
#         "VIG_HASTA": {"col_nueva": "FVigHasta", "tipo": str},
#         "NUMERO DE OPERACION": {"col_nueva": "Op", "tipo": int},
#         "CODIGO DE RAMA DE SEGURO": {"col_nueva": "CodRama", "tipo": int},
#         "NUMERO DE LA POLIZA": {"col_nueva": "Poliza", "tipo": int},
#         "SUPLEMENTO DE LA OPERACION": {"col_nueva": "Supl", "tipo": int},
#         "NUMERO DE COMPONENTE": {"col_nueva": "Comp", "tipo": int},
#         "NUMERO DE INTERMEDIARIO": {"col_nueva": "CodOrganizador", "tipo": int},
#         "NUMERO DE INTERMEDIARIO_duplicated_0": {
#             "col_nueva": "CodProductor",
#             "tipo": int,
#         },
#         "CODIGO DE RIESGO": {"col_nueva": "CodRiesgo", "tipo": int},
#         "DESCRIPCION DEL RIESGO": {"col_nueva": "Riesgo", "tipo": str},
#         "CODIGO DE COBERTURA": {"col_nueva": "CodCobertura", "tipo": int},
#         "DESCRIPCION DE LA COBERTURA": {"col_nueva": "Cobertura", "tipo": str},
#         "CODIGO DE PROVINCIA": {"col_nueva": "CodProvincia", "tipo": str},
#         "SUMA ASEGURADA POR COBERTURA": {
#             "col_nueva": "SaCobertura",
#             "tipo": pl.Float32,
#         },
#         "PREMIO BRUTO": {"col_nueva": "PremioBrutoSuplemento", "tipo": pl.Float32},
#         "% BONIFICACION SOBRE PRIMA": {"col_nueva": "BonPrimaPorc", "tipo": pl.Float32},
#         "PORMILAJE DE PRIMA": {"col_nueva": "Pormilaje", "tipo": pl.Float32},
#         "PRIMA DE TARIFA": {"col_nueva": "PrimaTarifaSuplemento", "tipo": pl.Float32},
#         "PRIMA POR COBERTURA": {
#             "col_nueva": "PrimaTarifaCobertura",
#             "tipo": pl.Float32,
#         },
#     }

#     renamecols = {k: v["col_nueva"] for k, v in opeemirv_dict_cols.items()}
#     schema_override = {k: v["tipo"] for k, v in opeemirv_dict_cols.items()}

#     data = (
#         pl.read_csv(
#             PRIMAS_RVARIAS,
#             separator=";",
#             decimal_comma=True,
#             encoding="ANSI",
#             schema_overrides=schema_override,
#         )
#         .select([pl.col(k).alias(v) for k, v in renamecols.items()])
#         .with_columns(pl.col("FVigHasta").str.to_date("%d/%m/%Y", strict=False))
#     ).with_columns(
#         [
#             (
#                 pl.col("PrimaTarifaSuplemento") * (100 - pl.col("BonPrimaPorc") / 100)
#             ).alias("PrimaNetaSuplemento"),
#             (
#                 pl.col("PrimaTarifaCobertura") * (100 - pl.col("BonPrimaPorc") / 100)
#             ).alias("PrimaNetaCobertura"),
#         ]
#     )

#     fechadesde: date = data["FEmision"].min()  # pyright: ignore[reportAssignmentType]
#     a, m = fechadesde.year, fechadesde.month

#     while True:
#         _data = data.filter(
#             (pl.col("FEmision").dt.year() == a) & (pl.col("FEmision").dt.month() == m)
#         )
#         if _data.is_empty():
#             break

#         with db.get_client_ch() as ch:
#             query = f"SELECT Op, Supl, Comp, CodCobertura FROM {TABLA_PRIMAS_RVARIAS} Where toYYYYMM(FEmision) = {a * 100 + m} ;"
#             resp = ch.query(query, column_oriented=True)
#             if resp.result_set != []:
#                 existentes = pl.from_dict(
#                     data={k: v for k, v in zip(resp.column_names, resp.result_set)}
#                 )

#                 _data = _data.join(existentes, how="anti", on=resp.column_names)

#             print(f"\tMes {a * 100 + m}", f"nuevas {len(_data)} .", sep=" | ")
#             amdate: date = date(a, m, 5) + timedelta(days=30)
#             a, m = amdate.year, amdate.month

#             if _data.is_empty():
#                 continue
#             ch.insert_arrow(TABLA_PRIMAS_RVARIAS, _data.to_arrow())

#     print("\tLISTO")


def etl_primas_vida_desde_mysql(anio=2018):
    engine = db.get_engine_mysql()
    a: int = anio
    m: int = 1

    while True:
        q: str = f"""
                SELECT * 
                FROM primas_vida
                Where Year(FEmision) = {a} AND Month(FEmision) = {m};"""

        data: pl.DataFrame = pl.read_database(
            q, connection=engine, schema_overrides={"FVigHasta": pl.String}
        ).select(
            [
                "FEmision",
                "FVigDesde",
                # pl.col("FVigHasta").str.to_date("%d/%m/%Y", strict=False),
                "Op",
                "CodRama",
                "Poliza",
                "Supl",
                "Comp",
                "CodOrganizador",
                "CodProductor",
                "CodCobertura",
                "Cobertura",
                "CodProvincia",
                "SaSupl",
                pl.col("PremioBrutoSupl").alias("PremioBrutoSuplemento"),
                pl.col("PrimaTarifaSupl").alias("PrimaTarifaSuplemento"),
                pl.col("BonPrimaPctSupl").alias("BonPrimaPctSuplemento"),
                pl.col("PrimaNetaSupl").alias("PrimaNetaSuplemento"),
                "PrimaTarifaCobertura",
                "PrimaNetaCobertura",
            ]
        )

        if data.is_empty():
            break

        with db.get_client_ch() as ch:
            query = f"SELECT Op, Supl, Comp, CodCobertura FROM {TABLA_PRIMAS_RVARIAS} Where toYYYYMM(FEmision) = {a * 100 + m} ;"
            resp = ch.query(query, column_oriented=True)
            if resp.result_set != []:
                existentes = pl.from_dict(
                    data={k: v for k, v in zip(resp.column_names, resp.result_set)}
                )

                data = data.join(existentes, how="anti", on=resp.column_names)

        print(f"\tMes {a * 100 + m}", f"nuevas {len(data)} .", sep=" | ")
        amdate: date = date(a, m, 5) + timedelta(days=30)
        a, m = amdate.year, amdate.month

        if data.is_empty():
            continue
        ch.insert_arrow(TABLA_PRIMAS_RVARIAS, data.to_arrow())

    print("\tLISTO")
