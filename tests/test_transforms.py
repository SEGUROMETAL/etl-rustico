import polars as pl
import pytest

from ch.pipelines.dims.daf_transforms import (
    agrupar_por_documento,
    cuit_invalido,
    dni_invalido,
    normalizar_daf,
    resolver_cadena_grupos,
)
from ch.registry import PipelineInfo, get_pipeline, register


def _df(rows: dict) -> pl.DataFrame:
    return pl.DataFrame(rows)


def filtrar_invalidos(df: pl.DataFrame, expr: pl.Expr) -> list[bool]:
    return df.select(expr.alias("x"))["x"].to_list()


class TestCuit:
    def test_cuit_valido(self):
        df = _df({"Cuit": ["20321021551"]})
        assert not filtrar_invalidos(df, cuit_invalido())[0]

    def test_cuit_longitud_mala(self):
        df = _df({"Cuit": ["200"]})
        assert filtrar_invalidos(df, cuit_invalido())[0]

    def test_cuit_repetido(self):
        df = _df({"Cuit": ["20111111111"]})
        assert filtrar_invalidos(df, cuit_invalido())[0]

    def test_cuit_lista_negra(self):
        df = _df({"Cuit": ["20000999998"]})
        assert filtrar_invalidos(df, cuit_invalido())[0]


class TestDni:
    def test_dni_valido(self):
        df = _df({"NroDocumento": [30111222]})
        assert not filtrar_invalidos(df, dni_invalido())[0]

    def test_dni_cero(self):
        df = _df({"NroDocumento": [0]})
        assert filtrar_invalidos(df, dni_invalido())[0]

    def test_dni_bajo(self):
        df = _df({"NroDocumento": [500]})
        assert filtrar_invalidos(df, dni_invalido())[0]

    def test_dni_repetido(self):
        df = _df({"NroDocumento": [21111111]})
        assert filtrar_invalidos(df, dni_invalido())[0]


def test_normalizar_sexo_y_grupo():
    daf = _df(
        {
            "NroPersona": [1, 2],
            "Nombre": [" a ", "b"],
            "Domicilio": [" x ", "y"],
            "Cp": [1000, 2000],
            "CpSufijo": [1, 2],
            "NroDocumento": [30111222, 27888999],
            "Cuit": ["20321021551", "20272429471"],
            "FechaNac": ["1990-05-01", "0000-00-00"],
            "Sexo": [1, 2],
            "Bloqueado": ["_", "S"],
            "Grupo": [None, 0],
        }
    )
    out = normalizar_daf(daf)
    assert out["Sexo"].to_list() == ["M", "F"]
    assert out["Grupo"].to_list() == [0, 0]
    assert out["Nombre"].to_list() == ["A", "B"]
    assert out["FechaNac"][1] is None


def _daf_base(nros, grupos=None, docs=None, cuits=None):
    n = len(nros)
    grupos = grupos or [0] * n
    docs = docs or [30111222] * n
    cuits = cuits or ["20321021551"] * n
    return pl.DataFrame(
        {
            "NroPersona": nros,
            "Nombre": ["a"] * n,
            "Domicilio": ["x"] * n,
            "Cp": [1000] * n,
            "CpSufijo": [1] * n,
            "NroDocumento": docs,
            "Cuit": cuits,
            "FechaNac": ["1990-05-01"] * n,
            "Sexo": [1] * n,
            "Bloqueado": ["_"] * n,
            "Grupo": grupos,
        }
    )


def test_resolver_cadena_grupos():
    daf = _df(
        {
            "NroPersona": [10, 20],
            "Grupo": [20, 0],
            "Bloqueado": ["_", "_"],
        }
    )
    out = resolver_cadena_grupos(daf)
    assert out["Grupo"].to_list() == [20, 20]


def test_agrupar_por_documento_no_explota():
    daf = _daf_base([1, 2])
    out = agrupar_por_documento(daf)
    assert out["Grupo"].to_list() == [2, 2]


def test_registry_duplicado_y_busqueda():
    @register("test-x", "test", "desc")
    def _x(): ...

    with pytest.raises(ValueError):

        @register("test-x", "test")
        def _y(): ...

    info = get_pipeline("test-x")
    assert isinstance(info, PipelineInfo)

    with pytest.raises(KeyError):
        get_pipeline("no-existe")
