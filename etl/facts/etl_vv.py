import db
from datetime import date, timedelta
import polars as pl
from sqlalchemy import text

from etl.etl_constantes import TABLA_VV


# def from_mysql_to_parquet():
#     engine = db.get_engine_mysql()

#     a = 2025
#     m = 2
#     d = 4
#     i = 0

#     while True:
#         fecha = date(a, m, d) + timedelta(i)
#         if fecha > date.today():
#             print("\tÚltima", fecha)
#             i += 1
#             break

#         if fecha < date(2025, 2, 4):
#             print("\tNo deseada", fecha)
#             i += 1
#             continue

#         fn = FILES / rf"{fecha.strftime('%Y%m%d')}.parquet"
#         if fn.exists():
#             i += 1
#             continue

#         sql = """
#             SELECT
#                 *
#             FROM vigentes_vehiculos_dia
#             WHERE Fecha = :fecha;
#             """

#         data = pl.read_database(
#             sql,
#             connection=engine,
#             execute_options={"parameters": {"fecha": fecha}},
#         )
#         if data.is_empty():
#             print("\tFecha vacía", fecha)
#             i += 1
#             continue

#         data.write_parquet(fn)

#         print(f"\tFecha {fecha.strftime('%Y%m%d')}")

#         i += 1
#     return


def etl_vv():
    engine = db.get_engine_mysql()
    print("\nVehículos vigentes Día")

    fecha = date(2025, 2, 3)

    with engine.connect() as cn:
        with db.get_client_ch() as ch:
            create_sql = f"""
                CREATE TABLE IF NOT EXISTS {TABLA_VV} (
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
                        );"""
            ch.command(create_sql)

            query = f"SELECT Distinct Fecha FROM {TABLA_VV};"
            resp = ch.query(query, parameters={"fecha": fecha}, column_oriented=True)
            fecha_existentes: list[pl.Date] = (
                pl.from_dict(
                    data={k: v for k, v in zip(resp.column_names, resp.result_set)}
                )
                .to_series()
                .to_list()
            )

            while True:
                fecha += timedelta(1)
                if fecha in fecha_existentes:
                    continue
                if fecha >= date.today():
                    break

                existe: tuple | None = cn.execute(
                    text(
                        "Select Poliza from vigentes_vehiculos_dia where Fecha = :fecha Limit 1;"
                    ),
                    {"fecha": fecha},
                ).fetchone()  # pyright: ignore[reportAssignmentType]

                if existe is None:
                    print(fecha, "No existe en MySql")
                    continue

                data = pl.read_database(
                    f"Select * from {TABLA_VV} Where Fecha = :fecha",
                    connection=engine,
                    execute_options={"parameters": {"fecha": fecha}},
                ).select(
                    [
                        "CodOrganizador",
                        "CodProductor",
                        "CodRama",
                        "Poliza",
                        "Supl",
                        "Componente",
                        # "EstadoComponente",
                        "FVigDesde",
                        "FVigHasta",
                        "NroAsegurado",
                        "NomAsegurado",
                        "CpAsegurado",
                        "CpSufijoAsegurado",
                        "CodMarca",
                        "CodModelo",
                        "CodSubModelo",
                        "Marca",
                        "Modelo",
                        "SubModelo",
                        "CvaCapitulo",
                        "CvaVariante",
                        "CvaDescripcion",
                        "AnioVehiculo",
                        "CodUsoVehiculo",
                        "CodTipoVehiculo",
                        # "TipoVehiculo",
                        "CodCoberturaAut",
                        "SumaAsegurada",
                        pl.col("NroMotor").str.strip_chars(),
                        pl.col("NroChasis").str.strip_chars(),
                        "Origen",
                        "NroPersonaPagador",
                        "NroPersonaTomador",
                        "CodCarroceria",
                        # "Periodo",
                        "NomProductor",
                        "DomicilioProductor",
                        "CpProductor",
                        "CpSufijoProductor",
                        "LocalidadProductor",
                        "CodProvinciaProductor",
                        "ProvinciaProductor",
                        "CodProvinciaInderProductor",
                        "MatriculoProductor",
                        "CodGrupoOrganizador",
                        "GrupoOrganizador",
                        "TarifaMadreLetra",
                        "TarifaHija",
                        pl.col("Dominio").str.strip_chars(),
                        "Ant",
                        "Fecha",
                    ]
                )

                if data.is_empty():
                    continue

                ch.insert_arrow(TABLA_VV, data.to_arrow())
                print("\t", fecha, len(data))

                # for a in range(2025, date.today().year + 1):
                #     for m in range(1, 13):
                #         qc.set_parameter("a", a)
                #         qc.set_parameter("m", m)
                #         result = ch.query(context=qc)
                #         fdesde: date = result.result_set[0][0]
                #         fhasta: date = result.result_set[1][0]

                #         pat = f"{a}{m:02d}*.parquet"
                #         # print(pat, len(list(FILES.glob(pat))))
                #         files = FILES.glob(pat)
                #         lcombined: list[pl.DataFrame] = [transform_pl(f) for f in files]
                #         if lcombined:
                #             combined = pl.concat(lcombined)
                #             # print(combined.min(), combined.max())
                #             combined = combined.filter(
                #                 ~(pl.col("Fecha").is_between(fdesde, fhasta))
                #             )
                #             if combined.is_empty():
                #                 continue
                #             ch.insert_arrow("vv_dia", combined.to_arrow())

        ch.command(f"OPTIMIZE TABLE reportes.{TABLA_VV} FINAL;")
        res = ch.query(
            "SELECT Mes,Minimo ,Maximo ,Promedio ,Gap ,Std   from v_vv_diaria_resumen_mensual order by Mes Desc;",
            column_oriented=True,
        )
        columns = res.column_names
        data = {k: v for k, v in zip(columns, res.result_set)}
        print(pl.DataFrame(data=data))


if __name__ == "__main__":
    etl_vv()
