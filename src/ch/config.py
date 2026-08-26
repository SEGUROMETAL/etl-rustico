import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT: Path = Path(__file__).resolve().parents[2]


def _env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


@dataclass(frozen=True)
class Settings:
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_db: str
    ch_host: str
    ch_port_http: int
    ch_port_native: int
    ch_user: str
    ch_password: str
    ch_db: str


def _load() -> Settings:
    load_dotenv(REPO_ROOT / ".env", override=True)
    return Settings(
        mysql_host=_env("MYSQL_HOST", "HOST"),
        mysql_port=int(_env("MYSQL_PORT", "PORT", default="3306")),
        mysql_user=_env("MYSQL_USER", "USER"),
        mysql_password=_env("MYSQL_PASSWORD", "PASSWORD"),
        mysql_db=_env("MYSQL_DB", "SCHEMA"),
        ch_host=_env("CH_HOST", "CHHOST"),
        ch_port_http=int(_env("CH_PORT_HTTP", "CHPORTHTTP", default="8123")),
        ch_port_native=int(_env("CH_PORT_NATIVE", "CHPORTTCP", default="9000")),
        ch_user=_env("CH_USER", "CHUSER"),
        ch_password=_env("CH_PASSWORD", "CHPASSWORD"),
        ch_db=_env("CH_DB", "CHSCHEMA", default="reportes"),
    )


settings = _load()
