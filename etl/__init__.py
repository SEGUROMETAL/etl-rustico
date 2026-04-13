from etl.dims.etl_coberturas_aut import etl_coberturas_aut
from etl.dims.etl_coberturas_rv import etl_coberturas_rv
from etl.dims.etl_daf import etl_daf
from etl.dims.etl_localidades import etl_localidades
from etl.dims.etl_organizadores import etl_organizadores
from etl.dims.etl_productores import etl_productores
from etl.dims.etl_rcs import et_rcs_anuales_from_mysql
from etl.dims.etl_tasas import etl_tasas_anuales_autos_from_mysql
from etl.facts.etl_denupet import etl_denupet

#
from .facts.etl_primas_automotores import etl_primas_automotores
from .facts.etl_primas_rvarias import (
    etl_primas_ramas_varias_desde_csv,
    etl_primas_ramas_varias_desde_mysql,
)
from .facts.etl_sehpm151 import etl_sehpm151t
from .facts.etl_sinpag import etl_sinpagt
from .facts.etl_vv import etl_vv

__all__ = [
    "etl_coberturas_aut",
    "etl_coberturas_rv",
    "etl_productores",
    "etl_organizadores",
    "etl_localidades",
    "etl_daf",
    #
    "etl_vv",
    "etl_primas_automotores",
    "etl_sehpm151t",
    "etl_sinpagt",
    "etl_primas_ramas_varias_desde_csv",
    "etl_primas_ramas_varias_desde_mysql",
    "et_rcs_anuales_from_mysql",
    "etl_tasas_anuales_autos_from_mysql",
    "etl_denupet",
]
