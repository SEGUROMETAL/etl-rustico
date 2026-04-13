import os
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from dotenv import load_dotenv
import clickhouse_connect


def get_engine_mysql() -> Engine:
    load_dotenv(".env")
    user = os.getenv("USER")
    password = os.getenv("PASSWORD")
    host = os.getenv("HOST")
    port = os.getenv("PORT")
    schema = os.getenv("SCHEMA")
    mysql_engine: Engine = create_engine(
        f"mysql+pymysql://{user}:{password}@{host}:{port}/{schema}"
    )
    return mysql_engine


def get_client_ch():
    load_dotenv(".env")
    user: str = os.getenv("CHUSER", "")
    password: str = os.getenv("CHPASSWORD", "")
    host: str = os.getenv("CHHOST", "")
    # port: str = os.getenv("CHPORTTCP", "")
    schema: str = os.getenv("CHSCHEMA", "")

    return clickhouse_connect.get_client(
        host=host, username=user, password=password, database=schema
    )
