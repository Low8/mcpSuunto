"""Parse and persist Suunto FIT activities."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import fitdecode

from mcpSuunto.models import (
    Activity,
    DeveloperField,
    Event,
    Interval,
    Lap,
    Length,
    ParsedActivity,
    Record,
)

SEMICIRCLES_TO_DEGREES = 180 / 2**31


def _message_values(message: fitdecode.FitDataMessage) -> dict[str, Any]:
    return {field.name: field.value for field in message.fields}


def _first(values: dict[str, Any], *names: str) -> Any:
    for name in names:
        value = values.get(name)
        if value is not None:
            return value
    return None


def _number(value: Any) -> int | float | None:
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _coordinate(value: Any) -> float | None:
    number = _number(value)
    return number * SEMICIRCLES_TO_DEGREES if number is not None else None


def _id_for_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_fit(path: Path, source_file: str | None = None) -> ParsedActivity:
    """Parse one FIT file, retaining all supported summary and time-series data."""
    activity_id = _id_for_file(path)
    source = source_file or path.name
    session: dict[str, Any] | None = None
    records: list[dict[str, Any]] = []
    laps: list[dict[str, Any]] = []
    lengths: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    developer_fields: list[dict[str, Any]] = []
    descriptions: dict[tuple[int, int], tuple[str, str | None]] = {}

    with fitdecode.FitReader(path) as reader:
        for frame in reader:
            if not isinstance(frame, fitdecode.FitDataMessage):
                continue
            values = _message_values(frame)

            if frame.name == "session":
                session = values
            elif frame.name == "field_description":
                index = values.get("developer_data_index")
                number = values.get("field_definition_number")
                name = values.get("field_name")
                if index is not None and number is not None and name:
                    descriptions[(int(index), int(number))] = (
                        str(name),
                        values.get("units"),
                    )
            elif frame.name == "record" and values.get("timestamp") is not None:
                records.append(
                    {
                        "timestamp": values["timestamp"],
                        "latitude": _coordinate(values.get("position_lat")),
                        "longitude": _coordinate(values.get("position_long")),
                        "distance_m": _first(values, "distance"),
                        "altitude_m": _first(values, "enhanced_altitude", "altitude"),
                        "speed_m_s": _first(values, "enhanced_speed", "speed"),
                        "heart_rate": values.get("heart_rate"),
                        "cadence": values.get("cadence"),
                        "power_w": values.get("power"),
                        "temperature_c": values.get("temperature"),
                        "vertical_speed_m_s": values.get("vertical_speed"),
                        "ngp_m_s": values.get("ngp"),
                        "grade_pct": values.get("grd_pct"),
                    }
                )
                for field in frame.fields:
                    if field.field_type != "devfield" or field.field is None:
                        continue
                    developer_data_index = field.field.dev_data_index
                    field_definition_number = field.field.def_num
                    field_name, unit = descriptions.get(
                        (
                            int(developer_data_index),
                            int(field_definition_number),
                        ),
                        (field.name, field.units),
                    )
                    numeric = _number(field.value)
                    developer_fields.append(
                        {
                            "timestamp": values["timestamp"],
                            "message_type": "record",
                            "developer_data_index": int(developer_data_index),
                            "field_definition_number": int(field_definition_number),
                            "field_name": field_name,
                            "unit": unit,
                            "value_numeric": float(numeric) if numeric is not None else None,
                            "value_text": None if numeric is not None else str(field.value),
                        }
                    )
            elif frame.name == "lap":
                laps.append(_lap_values(values))
            elif frame.name == "length":
                lengths.append(_length_values(values))
            elif frame.name == "event" and values.get("timestamp") is not None:
                events.append(
                    {
                        "timestamp": values["timestamp"],
                        "event": values.get("event"),
                        "event_type": values.get("event_type"),
                        "timer_trigger": values.get("timer_trigger"),
                    }
                )

    if session is None:
        start_time = records[0]["timestamp"] if records else None
        if start_time is None:
            raise ValueError(f"FIT file has no session or record timestamp: {path}")
        session = {"start_time": start_time, "timestamp": records[-1]["timestamp"]}

    start_time = _first(session, "start_time") or records[0]["timestamp"]
    end_time = session.get("timestamp") or (records[-1]["timestamp"] if records else None)
    activity = {
        "activity_id": activity_id,
        "source_file": source,
        "start_time": start_time,
        "end_time": end_time,
        "sport": str(_first(session, "sport") or path.stem.split("-")[-1]),
        "sub_sport": session.get("sub_sport"),
        "duration_seconds": _first(session, "total_timer_time"),
        "elapsed_seconds": _first(session, "total_elapsed_time"),
        "distance_m": _first(session, "total_distance"),
        "ascent_m": _first(session, "total_ascent"),
        "descent_m": _first(session, "total_descent"),
        "min_altitude_m": _first(session, "enhanced_min_altitude", "min_altitude"),
        "max_altitude_m": _first(session, "enhanced_max_altitude", "max_altitude"),
        "avg_heart_rate": session.get("avg_heart_rate"),
        "min_heart_rate": session.get("min_heart_rate"),
        "max_heart_rate": session.get("max_heart_rate"),
        "avg_speed_m_s": _first(session, "enhanced_avg_speed", "avg_speed"),
        "max_speed_m_s": _first(session, "enhanced_max_speed", "max_speed"),
        "calories": session.get("total_calories"),
        "avg_temperature_c": session.get("avg_temperature"),
        "max_temperature_c": session.get("max_temperature"),
        "avg_cadence": _first(session, "avg_running_cadence", "avg_cadence"),
        "max_cadence": _first(session, "max_running_cadence", "max_cadence"),
        "avg_power_w": session.get("avg_power"),
        "max_power_w": session.get("max_power"),
        "normalized_power_w": session.get("normalized_power"),
        "total_strides": session.get("total_strides"),
        "training_stress_score": session.get("training_stress_score"),
        "intensity_factor": session.get("intensity_factor"),
        "training_effect": session.get("total_training_effect"),
        "recovery_time_seconds": session.get("recovery_time"),
        "peak_epoc": session.get("peak_epoc"),
        "estimated_vo2_max": session.get("estimated_vo2_max"),
        "feeling": session.get("feeling"),
        "avg_ngp_m_s": session.get("avg_ngp"),
        "hills": session.get("hills"),
    }
    intervals = [
        {
            "sequence_number": sequence_number,
            "start_time": lap["start_time"],
            "end_time": lap["end_time"],
            "duration_seconds": lap["duration_seconds"],
            "interval_type": None,
            "source": "workout",
            "event": lap["event"],
            "event_type": lap["event_type"],
            "lap_trigger": lap["lap_trigger"],
            "distance_m": lap["distance_m"],
            "avg_heart_rate": lap["avg_heart_rate"],
            "min_heart_rate": lap["min_heart_rate"],
            "max_heart_rate": lap["max_heart_rate"],
            "avg_speed_m_s": lap["avg_speed_m_s"],
            "max_speed_m_s": lap["max_speed_m_s"],
            "avg_cadence": lap["avg_cadence"],
            "max_cadence": lap["max_cadence"],
            "avg_power_w": lap["avg_power_w"],
            "max_power_w": lap["max_power_w"],
            "ascent_m": lap["ascent_m"],
            "descent_m": lap["descent_m"],
        }
        for sequence_number, lap in enumerate(
            (
                lap for lap in laps
                if lap["event"] == "workout_step"
                and lap["lap_trigger"] == "fitness_equipment"
            ),
            start=1,
        )
    ]
    return ParsedActivity(
        activity=Activity.model_validate(activity),
        records=[Record.model_validate(record) for record in records],
        laps=[Lap.model_validate(lap) for lap in laps],
        intervals=[Interval.model_validate(interval) for interval in intervals],
        lengths=[Length.model_validate(length) for length in lengths],
        events=[Event.model_validate(event) for event in events],
        developer_fields=[
            DeveloperField.model_validate(field) for field in developer_fields
        ],
    )


def _lap_values(values: dict[str, Any]) -> dict[str, Any]:
    return {
        "start_time": values.get("start_time"),
        "end_time": values.get("timestamp"),
        "duration_seconds": values.get("total_timer_time"),
        "elapsed_seconds": values.get("total_elapsed_time"),
        "event": values.get("event"),
        "event_type": values.get("event_type"),
        "lap_trigger": values.get("lap_trigger"),
        "distance_m": values.get("total_distance"),
        "ascent_m": values.get("total_ascent"),
        "descent_m": values.get("total_descent"),
        "min_altitude_m": _first(values, "enhanced_min_altitude", "min_altitude"),
        "avg_altitude_m": _first(values, "enhanced_avg_altitude", "avg_altitude"),
        "max_altitude_m": _first(values, "enhanced_max_altitude", "max_altitude"),
        "min_heart_rate": values.get("min_heart_rate"),
        "avg_heart_rate": values.get("avg_heart_rate"),
        "max_heart_rate": values.get("max_heart_rate"),
        "avg_speed_m_s": _first(values, "enhanced_avg_speed", "avg_speed"),
        "max_speed_m_s": _first(values, "enhanced_max_speed", "max_speed"),
        "avg_cadence": values.get("avg_cadence"),
        "max_cadence": values.get("max_cadence"),
        "avg_power_w": values.get("avg_power"),
        "max_power_w": values.get("max_power"),
        "calories": values.get("total_calories"),
        "avg_temperature_c": values.get("avg_temperature"),
        "max_temperature_c": values.get("max_temperature"),
        "swim_stroke": values.get("swim_stroke"),
        "total_strokes": values.get("total_strokes"),
        "avg_swolf": values.get("avg_swolf"),
    }


def _length_values(values: dict[str, Any]) -> dict[str, Any]:
    return {
        "timestamp": values.get("timestamp"),
        "start_time": values.get("start_time"),
        "duration_seconds": values.get("total_timer_time"),
        "elapsed_seconds": values.get("total_elapsed_time"),
        "length_type": values.get("length_type"),
        "distance_m": values.get("total_distance"),
        "avg_speed_m_s": values.get("avg_speed"),
        "avg_cadence": values.get("avg_swimming_cadence"),
        "swim_stroke": values.get("swim_stroke"),
        "total_strokes": values.get("total_strokes"),
        "calories": values.get("total_calories"),
        "avg_swolf": values.get("avg_swolf"),
    }

