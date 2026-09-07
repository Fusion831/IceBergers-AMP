import os
import json
from datetime import datetime, timezone
from typing import List, Optional
from ecmwf.opendata import Client


def download_ecmwf_wind_data(
    output_dir: str = "data/raw/ecmwf/wind",
    filename: str = "ecmwf_wind_surface_0_48h.grib2",
    params: Optional[List[str]] = None,
    steps: Optional[List[int]] = None,
    source: str = "ecmwf"
) -> str:
    """Download ECMWF Open Data surface winds (10u, 10v) and temperature (2t)."""
    os.makedirs(output_dir, exist_ok=True)
    target_path = os.path.join(output_dir, filename)

    if params is None:
        params = ["10u", "10v", "2t"]
    if steps is None:
        steps = list(range(0, 49, 3))

    client = Client(source=source)
    client.retrieve(
        type="fc",
        stream="oper",
        resol="0p25",
        param=params,
        step=steps,
        target=target_path
    )
    return target_path
