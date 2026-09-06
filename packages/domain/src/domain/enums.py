"""Enumerations for AMIP domain objects."""
from enum import Enum, IntEnum


class RouteObjective(str, Enum):
    SAFEST = "SAFEST"
    FASTEST = "FASTEST"
    FUEL_EFFICIENT = "FUEL_EFFICIENT"
    BALANCED = "BALANCED"


class IceClass(str, Enum):
    POLAR_CLASS_1 = "PC1"
    POLAR_CLASS_2 = "PC2"
    POLAR_CLASS_3 = "PC3"
    POLAR_CLASS_4 = "PC4"
    POLAR_CLASS_5 = "PC5"
    POLAR_CLASS_6 = "PC6"
    POLAR_CLASS_7 = "PC7"
    ICE_STRENGTHENED_1A = "1A"
    ICE_CLASS_1A = "1A"
    ICE_CLASS_1B = "1B"
    ICE_CLASS_1C = "1C"
    UNSTRENGTHENED = "UNSTRENGTHENED"


class HorizonTier(str, Enum):
    TACTICAL_0_10_DAYS = "0-10_days"
    SUBSEASONAL_10_30_DAYS = "10-30_days"
    EXTENDED_30_90_DAYS = "30-90_days"


class HorizonDay(IntEnum):
    T_0 = 0
    T_7 = 7
    T_14 = 14
    T_30 = 30
    T_60 = 60
    T_90 = 90


class MissionStatus(str, Enum):
    DRAFT = "DRAFT"
    CONFIGURED = "CONFIGURED"
    ANALYZING = "ANALYZING"
    ANALYZED = "ANALYZED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MissionSeason(str, Enum):
    SUMMER_2025 = "2024-2025"
    SUMMER_2026 = "2025-2026"
    SUMMER_2027 = "2026-2027"


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
