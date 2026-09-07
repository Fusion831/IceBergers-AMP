"""
GEBCO_2026 Antarctic Bathymetry Ingestion Subsystem for AMIP.
"""

from data_ingestion.gebco.downloader import (
    GEBCODownloader,
    download_gebco,
    DEFAULT_ANTARCTIC_BBOX,
    CEDA_OPENDAP_SUBICE_URL,
)
from data_ingestion.gebco.processor import (
    GEBCOProcessor,
    process_gebco_file,
)
from data_ingestion.gebco.validator import (
    GEBCOValidator,
    GEBCOValidationError,
)
from data_ingestion.gebco.interface import (
    GEBCOBathymetryInterface,
    BathymetryHazard,
)

__all__ = [
    "GEBCODownloader",
    "download_gebco",
    "DEFAULT_ANTARCTIC_BBOX",
    "CEDA_OPENDAP_SUBICE_URL",
    "GEBCOProcessor",
    "process_gebco_file",
    "GEBCOValidator",
    "GEBCOValidationError",
    "GEBCOBathymetryInterface",
    "BathymetryHazard",
]
