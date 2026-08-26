from datetime import date

from ch.pipelines.facts.vv import fechas_ya_cargadas


class _Res:
    def __init__(self, column_names, result_set):
        self.column_names = column_names
        self.result_set = result_set


class _ChStub:
    def __init__(self, column_names, result_set):
        self._names = column_names
        self._cols = result_set

    def query(self, query, parameters=None, column_oriented=False):
        assert column_oriented
        return _Res(self._names, self._cols)


def test_fechas_ya_cargadas_resultset_column_oriented():
    ch = _ChStub(["Fecha"], [[date(2025, 2, 4), date(2025, 2, 5), date(2025, 2, 6)]])
    assert fechas_ya_cargadas(ch) == {date(2025, 2, 4), date(2025, 2, 5), date(2025, 2, 6)}


def test_fechas_ya_cargadas_vacio():
    assert fechas_ya_cargadas(_ChStub(["Fecha"], [[]])) == set()
    assert fechas_ya_cargadas(_ChStub(["Fecha"], [])) == set()


def test_fechas_ya_cargadas_ignora_nulos():
    ch = _ChStub(["Fecha"], [[date(2025, 2, 4), None]])
    assert fechas_ya_cargadas(ch) == {date(2025, 2, 4)}
