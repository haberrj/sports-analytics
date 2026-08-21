from enum import Enum


class IngestionResult(Enum):
    INGESTED = "ingested"
    ALREADY_COMPLETE = "already_complete"
    UNAVAILABLE = "unavailable"
