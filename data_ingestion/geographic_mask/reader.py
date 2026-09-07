"""
GeoPackage and Shapefile reader for SCAR ADD vector coastline polygons.
Safely reads vector layers with pyogrio/fiona, verifies CRS metadata,
and preserves original source attributes.
"""

from pathlib import Path
from typing import Union, Optional
import geopandas as gpd
import pyogrio
from core.logging import get_logger

logger = get_logger("data_ingestion.geographic_mask.reader")


class ADDReader:
    """Reads SCAR ADD vector datasets into GeoPandas GeoDataFrames."""

    def __init__(self, expected_crs: str = "EPSG:3031"):
        self.expected_crs = expected_crs

    def inspect_layers(self, filepath: Union[str, Path]):
        """Lists available layers in the vector file."""
        p = Path(filepath)
        layers = pyogrio.list_layers(str(p))
        logger.info("Found vector layers in file", path=str(p), layers=layers)
        return layers

    def read_dataset(
        self,
        filepath: Union[str, Path],
        layer: Optional[str] = None,
    ) -> gpd.GeoDataFrame:
        """
        Reads the vector dataset into a GeoDataFrame.
        
        Args:
            filepath: Path to .gpkg or .shp file.
            layer: Optional layer name if multiple layers exist in .gpkg.
            
        Returns:
            gpd.GeoDataFrame with EPSG:3031 CRS.
        """
        p = Path(filepath)
        if not p.exists():
            raise FileNotFoundError(f"ADD vector dataset does not exist: {p}")

        logger.info("Reading SCAR ADD dataset", path=str(p), layer=layer)
        if layer:
            gdf = gpd.read_file(str(p), layer=layer, engine="pyogrio")
        else:
            gdf = gpd.read_file(str(p), engine="pyogrio")

        if gdf.crs is None:
            logger.warning("CRS is missing in source file, explicitly setting to EPSG:3031")
            gdf.set_crs("EPSG:3031", inplace=True)
        else:
            epsg = gdf.crs.to_epsg()
            if epsg != 3031 and str(gdf.crs).lower() != "epsg:3031":
                logger.warning(
                    "Source dataset CRS is not EPSG:3031, reprojecting",
                    original_crs=str(gdf.crs),
                )
                gdf = gdf.to_crs("EPSG:3031")

        logger.info(
            "Successfully loaded ADD dataset",
            feature_count=len(gdf),
            columns=list(gdf.columns),
            crs=str(gdf.crs),
        )
        return gdf
