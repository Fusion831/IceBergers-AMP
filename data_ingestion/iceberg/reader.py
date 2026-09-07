"""
Data parsers for BYU historical consolidated database and USNIC operational observations.
Standardizes heterogeneous raw tables into normalized IcebergObservationRecord instances.
"""

import csv
from pathlib import Path
from typing import List, Optional, Union, Dict, Any
from datetime import datetime, timezone
from core.logging import get_logger
from data_ingestion.iceberg.metadata import (
    IcebergObservationRecord,
    IcebergSource,
)

logger = get_logger("data_ingestion.iceberg.reader")


class IcebergReader:
    """Parses BYU historical CSVs and USNIC operational iceberg files."""

    @staticmethod
    def parse_byu_date(date_int_or_str: Union[int, str]) -> datetime:
        """
        Parses BYU YYYYDDD date format (e.g. 2000125 -> Year 2000, Day 125).
        """
        s = str(date_int_or_str).strip()
        year = int(s[:4])
        day_of_year = int(s[4:])
        dt = datetime.strptime(f"{year}_{day_of_year}", "%Y_%j")
        return dt.replace(tzinfo=timezone.utc)

    def read_byu_single_iceberg(self, csv_path: Path) -> List[IcebergObservationRecord]:
        """
        Parses an individual BYU iceberg CSV file (e.g. updated7_consol/b15a.csv).
        """
        iceberg_id = csv_path.stem.upper()
        records: List[IcebergObservationRecord] = []

        with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            fieldnames = [fn.strip() for fn in (reader.fieldnames or [])]

            # Detect sensors present in the file
            # Column pattern: <sensor>_1 (lat), <sensor>_2 (lon), <sensor>_3 (flag)
            sensors = set()
            for col in fieldnames:
                if col.endswith("_1") and not col.startswith("size"):
                    sensors.add(col[:-2])

            has_size = "size_1" in fieldnames and "size_2" in fieldnames

            for row_idx, row in enumerate(reader):
                date_str = row.get("date", "").strip()
                if not date_str or not date_str.isdigit():
                    continue

                try:
                    obs_time = self.parse_byu_date(date_str)
                except Exception:
                    continue

                # Parse dimensions if present (values in NM)
                length_km = None
                width_km = None
                area_sqkm = None
                if has_size:
                    try:
                        s1 = float(row.get("size_1", 0))
                        s2 = float(row.get("size_2", 0))
                        if s1 > 0:
                            length_km = round(s1 * 1.852, 2)
                        if s2 > 0:
                            width_km = round(s2 * 1.852, 2)
                        if length_km and width_km:
                            area_sqkm = round(length_km * width_km, 2)
                    except ValueError:
                        pass

                # Extract observations for each sensor
                for sensor in sorted(sensors):
                    lat_col = f"{sensor}_1"
                    lon_col = f"{sensor}_2"
                    flag_col = f"{sensor}_3"

                    try:
                        lat = float(row.get(lat_col, 0))
                        lon = float(row.get(lon_col, 0))
                    except ValueError:
                        continue

                    # Filter out zero coordinates (BYU's convention for no observation)
                    if abs(lat) < 1e-4 and abs(lon) < 1e-4:
                        continue

                    flag = row.get(flag_col, "1").strip()
                    is_interpolated = (flag == "0")

                    rec = IcebergObservationRecord(
                        iceberg_id=iceberg_id,
                        source=IcebergSource.BYU_HISTORICAL,
                        observation_time=obs_time,
                        latitude=round(lat, 5),
                        longitude=round(lon, 5),
                        length_km=length_km,
                        width_km=width_km,
                        area_sqkm=area_sqkm,
                        sensor=sensor.upper(),
                        is_interpolated=is_interpolated,
                        is_valid=True,
                        source_file=csv_path.name,
                        source_record_id=f"{csv_path.stem}_{date_str}_{sensor}",
                    )
                    records.append(rec)

        return records

    def read_byu_directory(
        self,
        byu_dir: Path,
        max_icebergs: Optional[int] = None,
    ) -> List[IcebergObservationRecord]:
        """
        Reads all iceberg CSVs from the BYU extracted directory.
        """
        csv_files = sorted(byu_dir.rglob("*.csv"))
        all_records = []
        count = 0
        for p in csv_files:
            if p.name.startswith("#") or p.name.startswith("."):
                continue
            recs = self.read_byu_single_iceberg(p)
            all_records.extend(recs)
            count += 1
            if max_icebergs and count >= max_icebergs:
                break
        logger.info("Parsed BYU database", icebergs=count, total_records=len(all_records))
        return all_records

    def read_usnic_csv(self, csv_path: Path) -> List[IcebergObservationRecord]:
        """
        Parses USNIC operational Antarctic icebergs CSV (e.g. AntarcticIcebergs_20260904.csv).
        """
        records: List[IcebergObservationRecord] = []
        with open(csv_path, "r", encoding="utf-8-sig", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader):
                iceberg_id = row.get("Iceberg", "").strip().upper()
                if not iceberg_id:
                    continue

                lat_str = row.get("Latitude", "").strip()
                lon_str = row.get("Longitude", "").strip()
                date_str = row.get("Last Update", "").strip()

                try:
                    lat = float(lat_str)
                    lon = float(lon_str)
                except ValueError:
                    continue

                # Parse date (format MM/DD/YYYY)
                try:
                    obs_time = datetime.strptime(date_str, "%m/%d/%Y").replace(tzinfo=timezone.utc)
                except Exception:
                    obs_time = datetime.now(timezone.utc)

                length_km = None
                width_km = None
                area_sqkm = None

                try:
                    l_nm = float(row.get("Length (NM)", 0))
                    if l_nm > 0:
                        length_km = round(l_nm * 1.852, 2)
                except ValueError:
                    pass

                try:
                    w_nm = float(row.get("Width (NM)", 0))
                    if w_nm > 0:
                        width_km = round(w_nm * 1.852, 2)
                except ValueError:
                    pass

                try:
                    a_km = float(row.get("Area (sqKM)", 0))
                    if a_km > 0:
                        area_sqkm = round(a_km, 2)
                except ValueError:
                    pass

                rec = IcebergObservationRecord(
                    iceberg_id=iceberg_id,
                    source=IcebergSource.USNIC_OPERATIONAL,
                    observation_time=obs_time,
                    latitude=round(lat, 5),
                    longitude=round(lon, 5),
                    length_km=length_km,
                    width_km=width_km,
                    area_sqkm=area_sqkm,
                    sensor="USNIC_ANALYST",
                    is_interpolated=False,
                    is_valid=True,
                    source_file=csv_path.name,
                    source_record_id=f"USNIC_{iceberg_id}_{date_str}",
                )
                records.append(rec)

        logger.info("Parsed USNIC operational file", path=csv_path.name, records=len(records))
        return records
