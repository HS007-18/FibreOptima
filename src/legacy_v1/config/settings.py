from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Settings:
    MIN_HISTORY: int = 8
    WARNING_Z_THRESHOLD: float = 1.5
    HIGH_RISK_Z_THRESHOLD: float = 2.5
    MAINTENANCE_OVERDUE_DAYS: int = 30
    SPEED_ANOMALY_Z_THRESHOLD: float = 2.0
    MACHINE_AGE_WARNING_YEARS: int = 10
    MAX_FILE_SIZE_MB: int = 10
    REFERENCE_DATE: str = "2024-12-31"

    REQUIRED_COLUMNS: tuple = (
        "batch_id",
        "machine_id",
        "fabric_type",
        "operator",
        "shift",
        "production_quantity",
        "production_speed",
        "waste_quantity",
        "machine_age",
        "last_maintenance_date",
        "humidity",
        "temperature",
    )

    COLUMN_ALIASES: dict = field(default_factory=lambda: {
        "Batch ID": "batch_id",
        "Machine ID": "machine_id",
        "Fabric Type": "fabric_type",
        "Fabric type": "fabric_type",
        "Operator": "operator",
        "Shift": "shift",
        "Production Quantity": "production_quantity",
        "Production quantity": "production_quantity",
        "Production Speed": "production_speed",
        "Production speed": "production_speed",
        "Waste Quantity": "waste_quantity",
        "Waste quantity": "waste_quantity",
        "Machine Age": "machine_age",
        "Machine age": "machine_age",
        "Last Maintenance Date": "last_maintenance_date",
        "Last maintenance date": "last_maintenance_date",
        "Humidity": "humidity",
        "Temperature": "temperature",
    })

    NUMERIC_COLUMNS: tuple = (
        "production_quantity",
        "production_speed",
        "waste_quantity",
        "machine_age",
        "humidity",
        "temperature",
    )

    @property
    def reference_date(self) -> datetime:
        return datetime.fromisoformat(self.REFERENCE_DATE)


SETTINGS = Settings()