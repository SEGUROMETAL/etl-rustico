
import polars as pl

from ch.connections import ch_client, mysql_engine
from ch.loading import load_incremental
from ch.log import logger
from ch.months import iter_months, resolve_fin, resolve_inicio
from ch.registry import register

OVERRIDES = {
    "FEmision": pl.Date,
    "FVigDesde": pl.Date,
    "FVigHasta": pl.Date,
    "Op": pl.UInt32,
    "Comp": pl.UInt32,
    "Supl": pl.UInt32,
    "CodRama": pl.UInt32,
    "Poliza": pl.UInt32,
    "SaComponente": pl.Float64,
    "Cap": pl.UInt32,
    "Var": pl.UInt32,
    "Air": pl.UInt32,
    "Origen": str,
    "AnioComponente": pl.UInt32,
    "CodCoberturaAut": str,
    "CodTipoVeh": pl.UInt32,
    "CodUsoVeh": pl.UInt32,
    "PrimaTarifaSupl": pl.Float64,
    "BonPrimaSupl": pl.Float64,
    "PremioSupl": pl.Float64,
    "relPriPreSupl": pl.Float64,
    "PremioCobradoSupl": pl.Float64,
    "CodOrganizador": pl.UInt32,
    "CodProductor": pl.UInt32,
    "PrimaTarifaComp": pl.Float64,
    "PrimaRcTarifaComp": pl.Float64,
    "PrimaCascoTarifaComp": pl.Float64,
    "PrimaNetaComp": pl.Float64,
    "PrimaRcNetaComp": pl.Float64,
    "PrimaCascoNetaComp": pl.Float64,
}

EXCLUIR = [
    "AnioMesEmision",
    "AnioEmision",
    "MesEmision",
    "DiaEmision",
    "estadopoliza",
    "ant",
    "relPriPreSupl",
]

QUERY = """SELECT *
FROM primas_automotores
WHERE Year(FEmision) = {a} AND Month(FEmision) = {m}"""


@register(
    "fact-primas-automotores",
    "hechos",
    "Primas de automotores por componente, incremental mensual",
)
def run(
    anio: int | None = None,
    desde: str | None = None,
    hasta: str | None = None,
) -> None:
    engine = mysql_engine()
    keys = ["Op", "Supl", "Comp"]
    inicio = resolve_inicio(desde, anio, default_year=2026)
    fin = resolve_fin(hasta)
    with ch_client() as ch:
        for a, m in iter_months(inicio, fin):
            data = pl.read_database(
                QUERY.format(a=a, m=m),
                connection=engine,
                schema_overrides=OVERRIDES,
            ).select(pl.exclude(EXCLUIR))
            if data.is_empty():
                continue
            n = load_incremental(ch, "primas_automotores", data, keys, "FEmision")
            logger.info("primas_automotores %s-%02d: %s filas nuevas", a, m, n)
