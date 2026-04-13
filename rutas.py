from pathlib import Path

# folders
FILES: Path = Path("files")
SQL_FILES: Path = FILES / "sql"
CSV_SOURCES: Path = FILES / "csv_sources"
PARQUET_FILES: Path = FILES / "par"
DAF_FILES: Path = FILES / "daf"

# files
PRIMAS_VIDA: Path = CSV_SOURCES / "R94959699OpEmVIDA.csv"
PRIMAS_AUTOS: Path = CSV_SOURCES / "RAutMotoOpEmSinCobradas.csv"
PRIMAS_RVARIAS: Path = CSV_SOURCES / "RVariasOpEmTodas.csv"
PRIMAS_VIDA: Path = CSV_SOURCES / "R94959699OpEmVIDA.csv"
