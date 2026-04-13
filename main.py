import os
from typing import Callable

import etl


def main():
    menu = {
        # Dims
        "Coberturas Autos": {
            "tipo": "d",
            "funcion": etl.etl_coberturas_aut,
        },
        "Coberturas RVarias": {
            "tipo": "d",
            "funcion": etl.etl_coberturas_rv,
        },
        "Organizadores": {
            "tipo": "d",
            "funcion": etl.etl_organizadores,
        },
        "Productores": {
            "tipo": "d",
            "funcion": etl.etl_productores,
        },
        "Personas": {
            "tipo": "d",
            "funcion": etl.etl_daf,
        },
        "Localidades": {
            "tipo": "d",
            "funcion": etl.etl_localidades,
        },
        "Tasas Anuales Autos": {
            "tipo": "d",
            "funcion": etl.etl_tasas_anuales_autos_from_mysql,
        },
        # Facts
        "Vehículos Vigentes Día": {
            "tipo": "f",
            "funcion": etl.etl_vv,
        },
        "SEHPM151 (Emisión de Operaciones)": {
            "tipo": "f",
            "funcion": etl.etl_sehpm151t,
        },
        "SINPAG (Órdenes de pago)": {
            "tipo": "f",
            "funcion": etl.etl_sinpagt,
        },
        "DenuPe (Denuncias de Siniestros)": {
            "tipo": "f",
            "funcion": etl.etl_denupet,
        },
        "Primas Autos x Componente": {
            "tipo": "f",
            "funcion": etl.etl_primas_automotores,
        },
        "Primas RVarias x Cobertura": {
            "tipo": "f",
            "funcion": etl.etl_primas_ramas_varias_desde_mysql,
        },
    }

    # etl.etl_primas_ramas_varias_desde_csv()

    items: list = list(enumerate(menu.items(), start=1))

    items_opciones: list[int] = [i[0] for i in items]
    items_labels_dims: str = "\n".join(
        [
            "\t- ".join([str(i), dtuple[0]])
            for i, dtuple in items
            if dtuple[1]["tipo"] == "d"
        ]
    )
    items_labels_facts: str = "\n".join(
        [
            "\t- ".join([str(i), dtuple[0]])
            for i, dtuple in items
            if dtuple[1]["tipo"] == "f"
        ]
    )

    while True:
        try:
            op: int = int(
                input(
                    "\n".join(
                        [
                            "\t\tDIMENSIONES",
                            "0\t- SALIR",
                            items_labels_dims,
                            "\n\t\tHECHOS",
                            items_labels_facts,
                            "\nELIJA UNA OPCIÓN: ",
                        ]
                    )
                )
            )

            if op == 0:
                break

            if op not in items_opciones:
                os.system("cls")
                print(
                    "La opción no está entre las habilitadas", f"Opción Escogida {op}\n"
                )
                continue

            item = [item for o, item in items if o == op][0]
            label: str = item[0]
            tipo: str = item[1]["tipo"]
            funcion: Callable = item[1]["funcion"]

            os.system("cls")
            sn = input(
                f"Eligió el Proceso '{label}' del tipo: '{'Dimensión' if tipo == 'd' else 'Hechos'}'  [S/n]"
            )
            if sn.lower() != "s":
                print("No eligió 'S'\n")
                continue
            if funcion == etl.etl_sehpm151t:
                while True:
                    try:
                        respuesta_anio = int(input("Desde duál año quiere actualizar?"))
                    except ValueError:
                        print("El año ingresado no es un número entero")
                    funcion(respuesta_anio)
                    break
                continue
            funcion()
            continue

        except ValueError:
            os.system("cls")
            print("La opcion debe ser un número entero\n")
            continue
        except Exception as e:
            os.system("cls")
            print(e)
            continue

        break
    print("Saliendo...")


if __name__ == "__main__":
    main()
