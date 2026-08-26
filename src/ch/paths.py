from pathlib import Path

REPO_ROOT: Path = Path(__file__).resolve().parents[2]

FILES: Path = REPO_ROOT / "files"
CSV_SOURCES: Path = FILES / "csv_sources"
PARQUET_FILES: Path = FILES / "par"
DAF_FILES: Path = FILES / "daf"
SQL_SUPERSET: Path = REPO_ROOT / "sql" / "superset"
MIGRATIONS: Path = REPO_ROOT / "db" / "migrations"

PRIMAS_VIDA_CSV: Path = CSV_SOURCES / "R94959699OpEmVIDA.csv"
PRIMAS_AUTOS_CSV: Path = CSV_SOURCES / "RAutMotoOpEmSinCobradas.csv"
PRIMAS_RVARIAS_CSV: Path = CSV_SOURCES / "RVariasOpEmTodas.csv"


class _Paths:
    files = FILES
    csv_sources = CSV_SOURCES
    parquet = PARQUET_FILES
    daf = DAF_FILES
    sql_superset = SQL_SUPERSET
    migrations = MIGRATIONS
    primas_vida_csv = PRIMAS_VIDA_CSV
    primas_autos_csv = PRIMAS_AUTOS_CSV
    primas_rvarias_csv = PRIMAS_RVARIAS_CSV


paths = _Paths()
