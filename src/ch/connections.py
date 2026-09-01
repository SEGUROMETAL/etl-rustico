from collections.abc import Iterator
from contextlib import contextmanager

import clickhouse_connect
from sqlalchemy import Engine, create_engine

from ch.config import settings

_mysql_engine: Engine | None = None


def mysql_engine() -> Engine:
    global _mysql_engine
    if _mysql_engine is None:
        _mysql_engine = create_engine(
            f"mysql+pymysql://{settings.mysql_user}:{settings.mysql_password}"
            f"@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_db}",
            pool_pre_ping=True,
        )
    return _mysql_engine


@contextmanager
def ch_client() -> Iterator[clickhouse_connect.driver.Client]:
    client = clickhouse_connect.get_client(
        host=settings.ch_host,
        port=settings.ch_port_http,
        username=settings.ch_user,
        password=settings.ch_password,
        database=settings.ch_db,
    )
    try:
        yield client
    finally:
        client.close()
