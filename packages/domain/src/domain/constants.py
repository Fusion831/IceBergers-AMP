"""Physical, geographical, and operational constants for AMIP."""

# CRS Definitions
CRS_WGS84 = "EPSG:4326"
CRS_ANTARCTIC_POLAR_STEREOGRAPHIC = "EPSG:3031"

# Standard NCPOR Reference Locations
CAPE_TOWN_COORDS = (-33.9249, 18.4241)
BHARATI_STATION_COORDS = (-69.4068, 76.1953)
MAITRI_STATION_COORDS = (-70.7644, 11.7340)

# Antarctic Operational Spatial Bounding Box [min_lat, min_lon, max_lat, max_lon]
ANTARCTIC_OPERATIONAL_BBOX = (-80.0, -180.0, -50.0, 180.0)

# Physical Constants
SEA_WATER_DENSITY_KG_M3 = 1025.0
AIR_DENSITY_KG_M3 = 1.25
EARTH_ROTATION_RAD_S = 7.292115e-5  # For Coriolis computation

# Operational Default Thresholds (Configurable)
DEFAULT_MIN_DEPTH_MARGIN_M = 4.4
DEFAULT_MAX_SIC = 0.60
DEFAULT_ICEBERG_BUFFER_KM = 5.0
DEFAULT_ICEBERG_ENSEMBLE_SIZE = 50
