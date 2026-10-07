"""Pydantic models independent from the DuckDB representation."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Activity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    activity_id: str
    source_file: str
    start_time: datetime
    end_time: datetime | None = None
    sport: str
    sub_sport: str | None = None
    duration_seconds: float | None = None
    elapsed_seconds: float | None = None
    distance_m: float | None = None
    ascent_m: float | None = None
    descent_m: float | None = None
    min_altitude_m: float | None = None
    max_altitude_m: float | None = None
    avg_heart_rate: int | None = None
    min_heart_rate: int | None = None
    max_heart_rate: int | None = None
    avg_speed_m_s: float | None = None
    max_speed_m_s: float | None = None
    calories: int | None = None
    avg_temperature_c: float | None = None
    max_temperature_c: float | None = None
    avg_cadence: float | None = None
    max_cadence: float | None = None
    avg_power_w: float | None = None
    max_power_w: float | None = None
    normalized_power_w: float | None = None
    total_strides: int | None = None
    training_stress_score: float | None = None
    intensity_factor: float | None = None
    training_effect: float | None = None
    recovery_time_seconds: float | None = None
    peak_epoc: float | None = None
    estimated_vo2_max: float | None = None
    feeling: int | None = None
    avg_ngp_m_s: float | None = None
    hills: float | None = None


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    latitude: float | None = None
    longitude: float | None = None
    distance_m: float | None = None
    altitude_m: float | None = None
    speed_m_s: float | None = None
    heart_rate: int | None = None
    cadence: float | None = None
    power_w: float | None = None
    temperature_c: float | None = None
    vertical_speed_m_s: float | None = None
    ngp_m_s: float | None = None
    grade_pct: float | None = None


class Lap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_time: datetime | None = None
    end_time: datetime | None = None
    duration_seconds: float | None = None
    elapsed_seconds: float | None = None
    event: str | None = None
    event_type: str | None = None
    lap_trigger: str | None = None
    distance_m: float | None = None
    ascent_m: float | None = None
    descent_m: float | None = None
    min_altitude_m: float | None = None
    avg_altitude_m: float | None = None
    max_altitude_m: float | None = None
    min_heart_rate: int | None = None
    avg_heart_rate: int | None = None
    max_heart_rate: int | None = None
    avg_speed_m_s: float | None = None
    max_speed_m_s: float | None = None
    avg_cadence: float | None = None
    max_cadence: float | None = None
    avg_power_w: float | None = None
    max_power_w: float | None = None
    calories: int | None = None
    avg_temperature_c: float | None = None
    max_temperature_c: float | None = None
    swim_stroke: str | None = None
    total_strokes: int | None = None
    avg_swolf: float | None = None


class Interval(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sequence_number: int
    start_time: datetime
    end_time: datetime | None = None
    duration_seconds: float | None = None
    interval_type: str | None = None
    source: str
    event: str | None = None
    event_type: str | None = None
    lap_trigger: str | None = None
    target_type: str | None = None
    target_value: float | None = None
    target_value_high: float | None = None
    target_unit: str | None = None
    distance_m: float | None = None
    avg_heart_rate: int | None = None
    min_heart_rate: int | None = None
    max_heart_rate: int | None = None
    avg_speed_m_s: float | None = None
    max_speed_m_s: float | None = None
    avg_cadence: float | None = None
    max_cadence: float | None = None
    avg_power_w: float | None = None
    max_power_w: float | None = None
    ascent_m: float | None = None
    descent_m: float | None = None


class DeveloperField(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: datetime | None = None
    message_type: str
    developer_data_index: int | None = None
    field_definition_number: int | None = None
    field_name: str
    unit: str | None = None
    value_numeric: float | None = None
    value_text: str | None = None


class Length(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: datetime | None = None
    start_time: datetime | None = None
    duration_seconds: float | None = None
    elapsed_seconds: float | None = None
    length_type: str | None = None
    distance_m: float | None = None
    avg_speed_m_s: float | None = None
    avg_cadence: float | None = None
    swim_stroke: str | None = None
    total_strokes: int | None = None
    calories: int | None = None
    avg_swolf: float | None = None


class Event(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    event: str | None = None
    event_type: str | None = None
    timer_trigger: str | None = None


class ParsedActivity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    activity: Activity
    records: list[Record] = Field(default_factory=list)
    laps: list[Lap] = Field(default_factory=list)
    intervals: list[Interval] = Field(default_factory=list)
    developer_fields: list[DeveloperField] = Field(default_factory=list)
    lengths: list[Length] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)

    @property
    def activity_id(self) -> str:
        return self.activity.activity_id
