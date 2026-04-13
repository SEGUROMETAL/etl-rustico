from datetime import date, timedelta
from time import sleep

from reportes.primas_vv import (
    df_vv,
    df_primas_automotores,
    df_tasas_automotores,
)

import polars as pl
from dateutil import parser
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table


def pedir_fecha(console, prompt_text="Ingresa una fecha") -> date:
    """Pide una fecha por consola"""
    while True:
        s = Prompt.ask(f"{prompt_text} (ej. 2026-03-31")
        try:
            dt = parser.parse(s, yearfirst=True)
            return dt.date()
        except (ValueError, OverflowError):
            console.print("[red]Fecha no válida. Intenta de nuevo.[/red]")


def pedir_entero(console, prompt_text="Imgrese un entero") -> int:
    """Pide un entero por consola"""
    while True:
        s = Prompt.ask(f"{prompt_text}")
        try:
            res = int(s)
            return res
        except (ValueError, OverflowError):
            console.print("[]Entrada no válida. Intenta de nuevo.[/red]")


def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body", ratio=1),
        Layout(name="footer", size=3),
    )
    layout["body"].split_row(Layout(name="left"), Layout(name="right"))
    return layout


def render_state(
    fecha: date,
    dias: int = 0,
    vv: pl.DataFrame | None = None,
    primas: pl.DataFrame | None = None,
    no_encontrados: pl.DataFrame | None = None,
    output_list: list[str] | None = None,
):
    output_list = [] if output_list is None else output_list
    layout = make_layout()
    layout["header"].update(
        Panel(
            f"[bold cyan]Primas Emitidas de Vehículos Vigentes '{fecha.isoformat()}'[/]"
        )
    )
    tabla = Table()
    tabla.add_column("Tabla")
    tabla.add_column("Filas")

    tabla.add_row("Vehículos Vigentes", len(vv) if vv else "")
    tabla.add_row("Primas", len(primas) if primas else "")
    tabla.add_row("No encontrados", len(no_encontrados) if no_encontrados else "")

    layout["left"].update(Panel(tabla, title="Datos"))

    output_list.insert(
        0, f"Desde '{(fecha - timedelta(dias)).isoformat()}' hasta '{fecha.isoformat()}"
    )
    texto_derecha: str = "- ".join(output_list)

    layout["right"].update(
        Panel(
            texto_derecha,
            title="Salida",
        )
    )

    layout["footer"].update(Panel("q: salir"))
    return layout


def layout():

    console = Console()
    fecha = pedir_fecha(
        console=console,
        prompt_text="Elija la fecha de los vehículos vigentes que quiere analizar",
    )
    console.print(f"[green]Fecha parseada:[/green] {fecha.isoformat()}")
    dias = pedir_entero(
        console=console,
        prompt_text="Elija La cantidad de días hacia atrás de emisiones de primas",
    )
    console.print(f"[green]Días:[/green] {dias}")

    fecha_desde = fecha - timedelta(dias)

    console.print(f"[green]Fecha Desde:[/green] {fecha_desde.isoformat()}")
    console.print(f"[green]Fecha Hasta:[/green] {fecha.isoformat()}")

    vv_data = df_vv(fecha=fecha)
    primas_data = df_primas_automotores(fecha=fecha, dias=dias)
    tasas_data = df_tasas_automotores()

    output_list = [
        f"Filas de Vehículos Vigentes {len(vv_data):d}",
        f"Filas de Primas automotores {len(primas_data):d}",
        f"Filas de Tasas automotores {len(tasas_data):d}",
    ]

    kwargs = {
        "fecha": fecha,
        "dias": dias,
        "vv": None,
        "primas": None,
        "no_encontrados": None,
        "output_list": output_list,
    }

    with Live(render_state(**kwargs), refresh_per_second=4) as live:
        while True:
            sleep(0.25)
            live.update(render_state(**kwargs))


layout()
