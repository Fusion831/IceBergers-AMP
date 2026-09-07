"""
Vessel configuration loader supporting dynamic multi-vessel definitions.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from core.logging import get_logger
from vessel.models import VesselProfile

logger = get_logger("vessel.config")

DEFAULT_VESSEL_CONFIG_DIR = Path("data/config/vessels")


def get_vessel_config_dir() -> Path:
    """Returns directory containing vessel JSON definitions."""
    return DEFAULT_VESSEL_CONFIG_DIR


def list_available_vessels(config_dir: Optional[Path] = None) -> List[str]:
    """Returns list of vessel configuration IDs found in the config directory."""
    cdir = config_dir or get_vessel_config_dir()
    if not cdir.exists():
        return []
    return [p.stem for p in cdir.glob("*.json")]


def load_vessel_profile(
    source: Union[str, Path],
    config_dir: Optional[Path] = None,
) -> VesselProfile:
    """
    Loads and validates a VesselProfile from a JSON file path or a vessel ID.
    
    Examples:
        load_vessel_profile("sagar_kanya")
        load_vessel_profile(Path("data/config/vessels/sagar_kanya.json"))
    """
    cdir = config_dir or get_vessel_config_dir()
    
    if isinstance(source, Path) or ("/" in str(source) or "\\" in str(source)):
        file_path = Path(source)
    else:
        # Check standard conventions: id directly or id.json
        candidate = cdir / f"{source}.json"
        if not candidate.exists():
            candidate = cdir / f"{source.replace('-', '_')}.json"
        if not candidate.exists():
            # If still not found, search in cdir
            matches = list(cdir.glob(f"*{source}*.json"))
            if matches:
                candidate = matches[0]
        file_path = candidate

    if not file_path.exists():
        logger.warning(
            "Vessel config file not found, creating default Sagar Kanya profile",
            requested_path=str(file_path),
        )
        return get_sagar_kanya_profile()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return VesselProfile.model_validate(data)
    except Exception as e:
        logger.error("Failed to parse vessel config, falling back to defaults", error=str(e), path=str(file_path))
        return get_sagar_kanya_profile()


def get_sagar_kanya_profile() -> VesselProfile:
    """Returns the default authoritative ORV Sagar Kanya vessel profile."""
    default_path = get_vessel_config_dir() / "sagar_kanya.json"
    if default_path.exists():
        return load_vessel_profile(default_path)
    return VesselProfile()
