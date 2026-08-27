from dataclasses import dataclass, field


@dataclass
class BatchRecord:
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
    humidity: float | None
    temperature: float | None

    waste_pct: float = 0.0
    days_since_maintenance: int = 0
    humidity_imputed: bool = False
    baseline_waste_pct: float = 0.0
    baseline_source: str = ""
    history_count: int = 0
    waste_deviation: float = 0.0
    waste_z_score: float | None = None

    maintenance_signal: bool = False
    speed_signal: bool = False
    environment_signal: bool = False
    limited_history: bool = False

    risk_level: str = "NORMAL"
    reasons: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)

    is_valid: bool = True
    is_duplicate: bool = False
    zero_production: bool = False
    humidity_missing: bool = False
    invalid_value: bool = False
    data_quality_reason: str = ""


@dataclass
class BaselineResult:
    mean_waste_pct: float
    std_waste_pct: float
    median_waste_pct: float
    history_count: int
    source: str
    primary_available: bool = False


@dataclass
class ValidationReport:
    total_records: int = 0
    valid_records: int = 0
    data_issues: int = 0
    duplicates: int = 0
    missing_values: int = 0
    zero_production: int = 0
    invalid_values: int = 0
    imputed_values: int = 0
    details: list = field(default_factory=list)
