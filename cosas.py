import sqlite3
from db.engines import get_engine_mysql
from pathlib import Path
from sqlalchemy import text


db: Path = Path(r"C:\Users\lcabral\REPOSITORIOS\SOS\reclamos\gestiones.db")


def llenar_cliente():
    with sqlite3.connect(db) as cn:
        q = """SELECT DISTINCT  g.dominio , g.poliza
            FROM gestiones g 
            where cliente = ''
                and g.activa = 1;"""
        cn.row_factory = sqlite3.Row

        res = cn.execute(q).fetchall()

        with get_engine_mysql().connect() as mysql:
            q_pv = """SELECT
                            `NroAsegurado`,`CodProductor`,`CodOrganizador`
                        from
                            vigentes_polizas_dia
                        WHERE
                            `CodRama` in (4,44)
                            and `Poliza` = :poliza
                        order by `Fecha` DESC
                        LIMIT 1
                        ;"""

            for dominio, poliza in res:
                poliza_str = str(poliza)[:7]
                poliza = int(poliza_str)
                if (
                    0
                    == mysql.execute(
                        text(
                            "Select Exists (Select * from vigentes_polizas_dia Where POliza = :poliza)"
                        ),
                        {"poliza": poliza},
                    ).fetchone()[0]
                ):
                    continue
                campos = mysql.execute(
                    text(q_pv), {"dominio": dominio, "poliza": poliza}
                ).fetchone()

                nro_as, codprod, codorg = campos
                cliente = mysql.execute(
                    text("Select DFNOMB from GNHDAF Where DFNRDF = :nroas"),
                    {"nroas": nro_as},
                ).fetchone()[0]
                nomprod = mysql.execute(
                    text(
                        "Select NomProductor from dims_productores Where CodProductor = :codprod"
                    ),
                    {"codprod": codprod},
                ).fetchone()[0]
                nomorg = mysql.execute(
                    text(
                        "Select NomOrganizador from dims_organizadores Where CodOrganizador = :codorg"
                    ),
                    {"codorg": codorg},
                ).fetchone()[0]

                params = {
                    "cliente": cliente,
                    "cod_productor": codprod,
                    "nom_productor": nomprod,
                    "cod_organizador": codorg,
                    "nom_organizador": nomorg,
                    "dominio": dominio,
                    "poliza": poliza,
                }

                print(f"\nDominio {dominio} - Póliza {poliza}")
                for k, v in params.items():
                    print(f"\t{k}:{v}")

                cn.execute(
                    """
                        Update gestiones
                        Set cliente = :cliente,
                            cod_productor = :cod_productor,
                            nom_productor = :nom_productor,
                            cod_organizador = :cod_organizador,
                            nom_organizador = :nom_organizador
                        Where  poliza = :poliza;""",
                    params,
                )


def llenar_productor():
    with sqlite3.connect(db) as cn:
        q = """SELECT DISTINCT g.poliza
                FROM gestiones g 
                where cod_productor is null
                    and g.activa = 1;"""
        cn.row_factory = sqlite3.Row
        res = cn.execute(q).fetchall()

        with get_engine_mysql().connect() as mysql:
            q_eo = """SELECT
                            `CodProductor`,`CodOrganizador`
                        from
                            emisiones_operaciones
                        WHERE
                            `CodRama` in (4,44)
                            and `Poliza` = :poliza
                        LIMIT 1
                        ;"""

            for (poliza,) in res:
                try:
                    poliza_mysql = int(str(poliza)[:7])

                except ValueError:
                    continue
                if (
                    0
                    == mysql.execute(
                        text(
                            "Select Exists (Select * from emisiones_operaciones Where Poliza = :poliza)"
                        ),
                        {"poliza": poliza_mysql},
                    ).fetchone()[0]
                ):
                    continue
                campos = mysql.execute(text(q_eo), {"poliza": poliza_mysql}).fetchone()
                if not campos:
                    continue

                codprod, codorg = campos
                nomprod = mysql.execute(
                    text(
                        "Select NomProductor from dims_productores Where CodProductor = :codprod"
                    ),
                    {"codprod": codprod},
                ).fetchone()[0]
                nomorg = mysql.execute(
                    text(
                        "Select NomOrganizador from dims_organizadores Where CodOrganizador = :codorg"
                    ),
                    {"codorg": codorg},
                ).fetchone()[0]

                params = {
                    "cod_productor": codprod,
                    "nom_productor": nomprod,
                    "cod_organizador": codorg,
                    "nom_organizador": nomorg,
                    "poliza": poliza,
                }

                print(f"\n\n Póliza {poliza}")
                for k, v in params.items():
                    print(f"\t{k}:{v}")

                cn.execute(
                    """
                        Update gestiones
                        Set cod_productor = :cod_productor,
                            nom_productor = :nom_productor,
                            cod_organizador = :cod_organizador,
                            nom_organizador = :nom_organizador
                        Where  poliza = :poliza;""",
                    params,
                )
        cn.commit()


llenar_productor()
