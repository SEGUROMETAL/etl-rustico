from datetime import date

import polars as pl

from ch.loading import load_incremental
from ch.pipelines.facts.vv import filtrar_existentes_del_dia


class _Res:
    def __init__(self, column_names, result_set):
        self.column_names = column_names
        self.result_set = result_set


class _ChStub:
    """Simula clickhouse_connect Client para probar la lógica de dedup."""

    def __init__(self, respuestas: dict[str, tuple[list, list]]):
        # clave: fragmento de SQL -> (column_names, columnas)
        self.respuestas = respuestas
        self.inserts: list[tuple[str, int]] = []

    def query(self, query, parameters=None, column_oriented=False):
        assert column_oriented
        for fragmento, (names, cols) in self.respuestas.items():
            if fragmento in query:
                return _Res(names, cols)
        raise AssertionError(f"Query inesperada: {query}")

    def insert_arrow(self, table, data):
        df = pl.from_arrow(data)
        self.inserts.append((table, len(df)))  # type: ignore[arg-type]


def test_load_incremental_filtra_duplicados_por_mes():
    ch = _ChStub(
        {
            "= 202501": (["Op", "Supl", "Comp"], [[1], [1], [1]]),
            "= 202502": (["Op", "Supl", "Comp"], [[]]),
        }
    )
    df = pl.DataFrame(
        {
            "Op": [1, 2, 3, 9],
            "Supl": [1, 2, 3, 9],
            "Comp": [1, 2, 3, 9],
            "FEmision": [date(2025, 1, 5)] * 3 + [date(2025, 2, 5)],
        }
    )

    total = load_incremental(ch, "primas_x", df, ["Op", "Supl", "Comp"], "FEmision")

    assert total == 3
    assert ch.inserts == [("primas_x", 2), ("primas_x", 1)]


def test_load_incremental_tabla_vacia_inserta_todo():
    ch = _ChStub({"FROM destino": (["Op"], [[], [], []])})
    df = pl.DataFrame(
        {
            "Op": [1, 2],
            "FEmision": [date(2025, 3, 5)] * 2,
        }
    )
    total = load_incremental(ch, "destino", df, ["Op"], "FEmision")
    assert total == 2


def test_filtrar_existentes_del_dia():
    fecha = date(2025, 8, 10)
    ch = _ChStub(
        {
            "WHERE Fecha = {fecha:Date}": (
                ["Fecha", "CodRama", "Poliza", "Supl", "Componente"],
                [
                    [fecha, fecha],
                    [4, 4],
                    [100, 200],
                    [0, 0],
                    [1, 1],
                ],
            )
        }
    )
    data = pl.DataFrame(
        {
            "Fecha": [fecha] * 3,
            "CodRama": [4, 4, 4],
            "Poliza": [100, 200, 300],
            "Supl": [0, 0, 0],
            "Componente": [1, 1, 1],
            "Ant": [10, 20, 30],
        }
    )

    nuevas = filtrar_existentes_del_dia(ch, data, fecha)

    assert nuevas["Poliza"].to_list() == [300]
