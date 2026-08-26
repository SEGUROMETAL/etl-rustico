from datetime import date

from ch.months import iter_months, next_month, ym


def test_iter_months_mismo_anio():
    assert iter_months(date(2025, 1, 1), date(2025, 4, 1)) == [
        (2025, 1),
        (2025, 2),
        (2025, 3),
        (2025, 4),
    ]


def test_iter_months_cruce_de_anio():
    assert iter_months(date(2025, 11, 1), date(2026, 2, 1)) == [
        (2025, 11),
        (2025, 12),
        (2026, 1),
        (2026, 2),
    ]


def test_iter_months_hasta_hoy_default():
    meses = iter_months(date(2020, 1, 1))
    assert meses[0] == (2020, 1)
    assert meses[-1] == (date.today().year, date.today().month)


def test_next_month():
    assert next_month(2025, 3) == (2025, 4)
    assert next_month(2025, 12) == (2026, 1)


def test_ym():
    assert ym(2025, 7) == 202507
