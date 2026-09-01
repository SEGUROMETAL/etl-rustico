import re
from collections.abc import Iterator
from pathlib import Path

import polars as pl
from clickhouse_connect.driver.client import Client as ChClient

from ch.connections import ch_client
from ch.log import logger
from ch.months import ym


def df_from_ch(
    ch: ChClient, query: str, parameters: dict | None = None
) -> pl.DataFrame:
    res = ch.query(query, parameters=parameters, column_oriented=True)
    return pl.from_dict(
        data={k: v for k, v in zip(res.column_names, res.result_set, strict=False)},
        strict=False,
    )


def insert_df(ch: ChClient, table: str, df: pl.DataFrame) -> int:
    if df.is_empty():
        return 0
    ch.insert_arrow(table, df.to_arrow())
    return len(df)


def replace_all(ch: ChClient, table: str, df: pl.DataFrame) -> int:
    """Trunca la tabla y carga el dataframe completo. Para dimensiones chicas."""
    ch.command(f"TRUNCATE TABLE {table}")
    n = insert_df(ch, table, df)
    logger.info("[dim] %s: %s filas cargadas (full refresh)", table, n)
    return n


def load_incremental(
    ch: ChClient,
    table: str,
    df: pl.DataFrame,
    keys: list[str],
    date_col: str,
) -> int:
    """Carga solo las filas cuya clave no exista ya en el mes correspondiente.

    El dataframe debe contener todas las filas de un único mes o de varios; se
    procesa mes por mes usando toYYYYMM(date_col).
    """
    if df.is_empty():
        return 0
    total = 0
    for a, m in sorted(
        set(zip(df[date_col].dt.year(), df[date_col].dt.month(), strict=True))
    ):
        chunk = df.filter(
            (pl.col(date_col).dt.year() == a) & (pl.col(date_col).dt.month() == m)
        )
        existing = df_from_ch(
            ch,
            f"SELECT DISTINCT {', '.join(keys)} FROM {table} "
            f"WHERE toYYYYMM({date_col}) = {ym(a, m)}",
        )
        if not existing.is_empty():
            chunk = chunk.join(existing, how="anti", on=keys)
        n = insert_df(ch, table, chunk)
        total += n
        logger.info("[fact] %s %s-%02d: %s filas nuevas", table, a, m, n)
    return total


def optimize_partitions(
    ch: ChClient, table: str, date_col: str, df: pl.DataFrame
) -> None:
    meses = sorted(
        set(zip(df[date_col].dt.year(), df[date_col].dt.month(), strict=True))
    )
    for a, m in meses:
        ch.command(f"OPTIMIZE TABLE {table} PARTITION {ym(a, m)}")


def apply_migrations(migrations_dir: Path | None = None) -> list[str]:
    """Aplica todos los .sql de db/migrations en orden alfabético. Idempotente."""
    migrations_dir = (
        migrations_dir or Path(__file__).resolve().parents[3] / "db" / "migrations"
    )
    applied: list[str] = []
    with ch_client() as ch:
        for sql_file in sorted(migrations_dir.glob("*.sql")):
            sql = sql_file.read_text(encoding="utf-8")
            for statement in _split_statements(sql):
                ch.command(statement)
            applied.append(sql_file.name)
            logger.info("[migrate] %s OK", sql_file.name)
    return applied


def _split_statements(sql: str) -> Iterator[str]:
    statement = ""
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        statement += line + "\n"
        if stripped.endswith(";"):
            clean = statement.strip().rstrip(";").strip()
            if clean:
                yield clean
            statement = ""
    if statement.strip():
        raise ValueError(f"Statement sin ';' final: {statement[:80]}...")


def sanitize_identifier(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"Identificador inválido: {name!r}")
    return name


__all__ = [
    "apply_migrations",
    "df_from_ch",
    "insert_df",
    "load_incremental",
    "optimize_partitions",
    "replace_all",
    "sanitize_identifier",
    "ym",
]
