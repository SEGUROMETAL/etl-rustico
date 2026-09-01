import argparse
import inspect
import sys

from rich.console import Console
from rich.table import Table

from ch import pipelines  # noqa: F401  (registra los pipelines)
from ch.loading import apply_migrations
from ch.log import logger
from ch.registry import all_pipelines, get_pipeline

console = Console()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ch",
        description="Pipelines MySQL legacy -> ClickHouse (Superset)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="Lista los pipelines disponibles")
    sub.add_parser("init-db", help="Aplica las migraciones DDL a ClickHouse")

    p_run = sub.add_parser("run", help="Ejecuta un pipeline")
    p_run.add_argument("name", help="Nombre del pipeline")
    p_run.add_argument("--anio", type=int, default=None, help="Año inicial (ej. 2024)")
    p_run.add_argument("--desde", type=str, default=None, help="Fecha inicial AAAA-MM-DD")
    p_run.add_argument("--hasta", type=str, default=None, help="Fecha final AAAA-MM-DD (opcional)")
    p_run.add_argument(
        "--arg",
        action="append",
        default=[],
        metavar="CLAVE=VALOR",
        help="Parámetro extra para el pipeline (repetible)",
    )

    args = parser.parse_args(argv)

    if args.command == "list":
        table = Table(title="Pipelines")
        table.add_column("Grupo", style="cyan")
        table.add_column("Nombre", style="green")
        table.add_column("Descripción")
        for p in all_pipelines():
            table.add_row(p.group, p.name, p.description)
        console.print(table)
        return 0

    if args.command == "init-db":
        applied = apply_migrations()
        console.print(f"[green]{len(applied)}[/green] migraciones aplicadas:")
        for name in applied:
            console.print(f"  - {name}")
        return 0

    if args.command == "run":
        raw_kwargs: dict = {}
        if args.anio is not None:
            raw_kwargs["anio"] = args.anio
        if args.desde is not None:
            raw_kwargs["desde"] = args.desde
        if args.hasta is not None:
            raw_kwargs["hasta"] = args.hasta
        for par in args.arg:
            clave, _, valor = par.partition("=")
            if not clave:
                console.print(f"[red]--arg inválido: {par!r} (usar CLAVE=VALOR)[/red]")
                return 1
            raw_kwargs[clave] = valor
        try:
            info = get_pipeline(args.name)
        except KeyError as e:
            console.print(f"[red]{e.args[0]}[/red]")
            return 1
        sig = inspect.signature(info.func)
        has_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
        if has_var_kw:
            kwargs = raw_kwargs
        else:
            kwargs = {k: v for k, v in raw_kwargs.items() if k in sig.parameters}
            ignorados = sorted(set(raw_kwargs) - set(kwargs))
            if ignorados:
                logger.warning(
                    "Argumentos ignorados para '%s': %s",
                    info.name,
                    ", ".join(ignorados),
                )
        logger.info("Ejecutando pipeline '%s' (%s)...", info.name, info.group)
        info.func(**kwargs)
        console.print(f"[bold green]LISTO:[/bold green] {info.name}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
