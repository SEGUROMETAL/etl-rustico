# ch — Pipelines MySQL legacy → ClickHouse para Superset

Repositorio de ingesta de datos: extrae del ERP legacy (MySQL), transforma con
Polars y carga en ClickHouse (`reportes`), que alimenta los dashboards de Superset.

## Estructura

```
src/ch/
  config.py         Settings leídas de .env (nombres MYSQL_*/CH_*, acepta los viejos)
  connections.py    Engine MySQL (singleton) y client ClickHouse (context manager)
  paths.py          Rutas de archivos y carpetas
  log.py            Logging con Rich
  months.py         Utilidades de meses (iter_months, next_month, ym)
  loading.py        Carga: full refresh, incremental mensual anti-join, migraciones
  registry.py       Registro de pipelines (@register)
  cli.py            CLI: ch list | ch run <pipeline> | ch init-db
  pipelines/
    dims/           Dimensiones: coberturas, localidades, organizadores,
                    productores, daf (+transforms puras), rcs, tasas
    facts/          Hechos: vv, sehpm151, sinpag, denupet,
                    primas automotores / rvarias / vida
  reports/          Consultas de análisis (primas_vv)
db/migrations/      DDL versionado de tablas, vistas y MVs (idempotente)
sql/superset/       Queries usadas por los dashboards de Superset
tests/              Tests unitarios de transformaciones puras
files/              Insumos: csv_sources/, daf/, par/ (no versionados)
scripts/            Utilidades puntuales
```

## Instalación

```bash
uv sync                      # crea .venv e instala el paquete 'ch' + deps
cp .env.example .env         # completar credenciales (no se commitea nunca)
docker compose up -d         # levanta ClickHouse
uv run ch init-db            # aplica db/migrations/*.sql (CREATE IF NOT EXISTS)
uv run ch list               # ver pipelines disponibles
uv run ch run dim-localidades
uv run ch run fact-sehpm151 --anio 2025
```

## Ejecución

Cada pipeline es un comando independiente; corren a mano o desde el scheduler
que prefieras. `--anio` arranca la recorrida mensual en ese año; `--desde`
(AAAA-MM-DD) fija fecha de inicio donde aplica; `--arg clave=valor` pasa
parámetros extra (ej. el mes en `fact-vv-reload-mes`).

| Nombre | Qué hace |
|---|---|
| `dim-coberturas-aut` | Coberturas de autos (insert con ReplacingMergeTree) |
| `dim-coberturas-rv` | Coberturas ramas varias (truncate + load) |
| `dim-localidades` | Localidades/provincias (truncate + load) |
| `dim-organizadores` | Organizadores (truncate + load) |
| `dim-productores` | Productores (truncate + load) |
| `dim-daf` | Asegurados: normalización de grupos + informes Excel en files/daf |
| `dim-rcs` | RC anuales → SCD + actual (detecta cambios reales) |
| `dim-tasas` | Tasas autos → SCD + actual + tabla derivada tasas_aut_x_riesgo |
| `fact-vv` | Snapshot diario vehículos vigentes (saltea fechas ya cargadas) |
| `fact-vv-reload-mes` | Recarga completa un mes de vv: `ch run fact-vv-reload-mes --arg mes=2025-03` |
| `fact-sehpm151` | Emisión de operaciones, incremental mensual |
| `fact-sinpag` | Órdenes de pago, incremental mensual |
| `fact-denupet` | Denuncias de siniestros, incremental mensual |
| `fact-primas-automotores` | Primas autos por componente, incremental mensual |
| `fact-primas-rvarias-mysql` / `-csv` | Primas ramas varias desde MySQL o CSV |
| `fact-primas-vida` | Primas vida desde CSV |

Incremental = por cada mes compara claves contra ClickHouse (anti-join) e inserta
solo filas nuevas. Si el origen **corrige** un valor, no se actualiza: para eso
hay que borrar/recargar (ver `fact-vv-reload-mes`; para otros facts, pedir
extensión del mismo mecanismo).

## Decisiones y hallazgos de esta reescritura

Bugs corregidos:
- `etl_rcs`: la detección de cambios comparaba `RcCl == RcCl` (consigo misma) y
  usaba `==` en vez de `!=`: re-insertaba todo sin cambios. Ahora compara bien.
- `etl_daf`: el bucle de cadenas de grupos era un no-op infinito potencial
  (creaba columna `Grupo_` sin usarla). Implementado como punto fijo acotado.
- `etl_vv`: hacía `OPTIMIZE TABLE ... FINAL` global tras cada corrida. Ahora
  optimiza solo las particiones tocadas.
- Cliente ClickHouse reutilizable (antes se abría/cerraba por mes procesado).
- Env vars genéricas `USER/PASSWORD` (colisión con las del SO) renombradas a
  `MYSQL_*`.

Inconsistencias de negocio detectadas (NO cambiadas, requieren validación):
- Prima neta: `primas_vida` calcula `tarifa * (100 - bonif)` mientras
  `primas_rvarias` usa `tarifa * (100 - bonif/100)`. Una de las dos está mal.
- `sehpm151` cruza los códigos 3873↔9105 entre organizador/productor a propósito.
- `sinpagt_agg` se referencia pero su DDL no está versionado (pendiente).

Deuda técnica pendiente:
- La MV `primas_automotores_agg` agrupa por casi todas las columnas: es casi
  idéntica a la base. Rediseñar (o eliminar si Superset no la usa).
- Los DDL reconstruidos (`011–015`) salieron del código Python: validar contra
  producción con `SHOW CREATE TABLE`.
- Estrategia futura: si el server ClickHouse logra alcanzar al MySQL, muchas
  cargas pasan a `mysql()` engine y Python queda solo para transformaciones.

## Seguridad

Las contraseñas viejas quedaron expuestas en el historial de git
(`docker-compose.yml` commiteaba `CLICKHOUSE_PASSWORD`). Este repo ya no
contiene secretos, pero **el historial sí**: hay que rotar la contraseña del
usuario ClickHouse (y de paso revisar la de MySQL). Con `git filter-repo`
se puede limpiar el historial si hace falta.

## Tests

```bash
uv run pytest        # transformaciones puras (daf, months, registry)
uv run ruff check .
```
