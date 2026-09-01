from datetime import date
from itertools import count


def iter_months(desde: date, hasta: date | None = None) -> list[tuple[int, int]]:
    """Lista de tuplas (anio, mes) desde `desde` hasta `hasta` (default: hoy), inclusive."""
    hasta = hasta or date.today()
    meses: list[tuple[int, int]] = []
    total = (hasta.year - desde.year) * 12 + (hasta.month - desde.month)
    for i in count():
        if i > total:
            break
        y = desde.year + (desde.month - 1 + i) // 12
        m = (desde.month - 1 + i) % 12 + 1
        meses.append((y, m))
    return meses


def resolve_inicio(
    desde: str | None, anio: int | None, default_year: int = 2025
) -> date:
    if desde is not None:
        return date.fromisoformat(desde)
    if anio is not None:
        return date(anio, 1, 1)
    return date(default_year, 1, 1)


def resolve_fin(hasta: str | None) -> date | None:
    return date.fromisoformat(hasta) if hasta is not None else None


def next_month(anio: int, mes: int) -> tuple[int, int]:
    return (anio + 1, 1) if mes == 12 else (anio, mes + 1)


def ym(anio: int, mes: int) -> int:
    return anio * 100 + mes
