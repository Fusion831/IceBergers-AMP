"""
NSIDC Antarctic Sea-Ice Concentration (G02202 v6) Ingestion Subsystem.
"""

from data_ingestion.nsidc.downloader import NSIDCDownloader, download_nsidc
from data_ingestion.nsidc.coordinates import NSIDCCoordinateTransformer, default_transformer
from data_ingestion.nsidc.reader import NSIDCReader
from data_ingestion.nsidc.processor import NSIDCProcessor, process_nsidc_file
from data_ingestion.nsidc.validator import NSIDCValidator
from data_ingestion.nsidc.interface import NSIDCSeaIceInterface

__all__ = [
    "NSIDCDownloader",
    "download_nsidc",
    "NSIDCCoordinateTransformer",
    "default_transformer",
    "NSIDCReader",
    "NSIDCProcessor",
    "process_nsidc_file",
    "NSIDCValidator",
    "NSIDCSeaIceInterface",
]
