from pydantic import BaseModel, ConfigDict
from typing import Optional
from src.legacy_v1.models.schemas import BatchRecord


class BatchRecordContract(BaseModel):
    """
    Canonical contract for inbound batch records.
    This layer ensures strict type and schema validity (e.g. types are correct)
    without prematurely enforcing business rules (like waste <= production)
    which are handled downstream by the data quality engine.
    """
    model_config = ConfigDict(coerce_numbers_to_str=False)

    batch_id: str
    machine_id: str
    fabric_type: str
    operator: str
    shift: str
    production_quantity: float
    production_speed: float
    waste_quantity: float
    machine_age: float
    last_maintenance_date: str
    humidity: Optional[float] = None
    temperature: Optional[float] = None

    def to_v1_record(self) -> BatchRecord:
        """
        Maps the validated canonical contract into the V1 domain schema,
        preserving backward compatibility with existing tests.
        """
        return BatchRecord(
            batch_id=self.batch_id,
            machine_id=self.machine_id,
            fabric_type=self.fabric_type,
            operator=self.operator,
            shift=self.shift,
            production_quantity=self.production_quantity,
            production_speed=self.production_speed,
            waste_quantity=self.waste_quantity,
            machine_age=self.machine_age,
            last_maintenance_date=self.last_maintenance_date,
            humidity=self.humidity,
            temperature=self.temperature,
        )
