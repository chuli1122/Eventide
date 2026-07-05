from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Dict, Optional

from .config import DEFAULT_CONFIG, BODY_FIELDS, PhysiologyConfig
from .models import BodyDeltas, BodyState
from .settings import EngineSettings


MAX_TICK_SEGMENTS = 48
APPROACH_FACTORS = {
    "heat": 0.18,
    "pressure": 0.14,
    "sensitivity": 0.12,
    "control": 0.16,
    "possessiveness": 0.10,
}


def create_initial_state(
    now: datetime,
    *,
    cycle_key: str = "stable",
    config: PhysiologyConfig = DEFAULT_CONFIG,
    rng: Optional[random.Random] = None,
) -> BodyState:
    state = BodyState(
        cycle_key=cycle_key,
        cycle_started_at=now,
        cycle_min_expires_at=now,
        cycle_expires_at=now,
        values=dict(config.initial_values),
        last_tick_at=now,
    )
    enter_cycle(state, cycle_key, now, config=config, rng=rng, reason="initial")
    return state


def enter_cycle(
    state: BodyState,
    cycle_key: str,
    now: datetime,
    *,
    config: PhysiologyConfig = DEFAULT_CONFIG,
    rng: Optional[random.Random] = None,
    reason: str = "cycle_expired",
) -> None:
    cycle = config.cycles.get(cycle_key, config.cycles["stable"])
    roller = rng or random
    min_hours, max_hours = cycle.duration_hours
    duration_hours = roller.uniform(float(min_hours), float(max_hours))
    state.cycle_key = cycle.key
    state.cycle_started_at = now
    state.cycle_min_expires_at = now + timedelta(hours=float(min_hours))
    state.cycle_expires_at = now + timedelta(hours=duration_hours)
    state.meta["last_cycle_reason"] = reason


def advance_state(
    state: BodyState,
    now: datetime,
    *,
    config: PhysiologyConfig = DEFAULT_CONFIG,
    settings: Optional[EngineSettings] = None,
    last_counterpart_message_at: Optional[datetime] = None,
    rng: Optional[random.Random] = None,
) -> bool:
    settings = settings or EngineSettings()
    if not settings.body_cycle_enabled:
        return False

    last_tick_at = state.last_tick_at or now
    if last_tick_at.tzinfo is None and now.tzinfo is not None:
        last_tick_at = last_tick_at.replace(tzinfo=now.tzinfo)
    if now <= last_tick_at:
        state.last_tick_at = now
        return False

    changed = False
    cursor = last_tick_at
    max_step = timedelta(hours=float(config.max_tick_hours))
    segments = 0
    while cursor < now and segments < MAX_TICK_SEGMENTS:
        _finish_expired_event_if_needed(state, cursor, config=config)
        _advance_cycle_if_needed(state, cursor, config=config, rng=rng)

        segment_end = min(now, cursor + max_step)
        for boundary in (state.cycle_expires_at, state.active_event_expires_at):
            if boundary and cursor < boundary < segment_end:
                segment_end = boundary

        elapsed_hours = max(0.0, (segment_end - cursor).total_seconds() / 3600.0)
        if elapsed_hours > 0:
            _advance_values(state, elapsed_hours, segment_end, last_counterpart_message_at, config=config)
            changed = True
        cursor = segment_end
        state.last_tick_at = cursor
        segments += 1

    if cursor >= now:
        state.last_tick_at = now
    return changed


def start_event(
    state: BodyState,
    event_key: str,
    now: datetime,
    *,
    config: PhysiologyConfig = DEFAULT_CONFIG,
    rng: Optional[random.Random] = None,
) -> bool:
    if state.active_event_key and state.active_event_expires_at and now < state.active_event_expires_at:
        return False
    event = config.events[event_key]
    roller = rng or random
    min_minutes, max_minutes = event.duration_minutes
    duration_minutes = roller.randint(int(min_minutes), int(max_minutes))
    state.active_event_key = event.key
    state.active_event_started_at = now
    state.active_event_expires_at = now + timedelta(minutes=duration_minutes)
    return True


def apply_interaction_delta(
    state: BodyState,
    deltas: BodyDeltas,
    *,
    config: PhysiologyConfig = DEFAULT_CONFIG,
) -> Dict[str, int]:
    applied = {}
    for field, delta in deltas.items():
        if field not in config.body_fields:
            continue
        next_value = clamp_body_field(field, state.values.get(field, 0) + int(delta), config=config)
        applied[field] = next_value - state.values.get(field, 0)
        state.values[field] = next_value
    return applied


def clamp_body_value(value: float) -> int:
    return max(0, min(100, int(round(float(value)))))


def clamp_body_field(field: str, value: float, *, config: PhysiologyConfig = DEFAULT_CONFIG) -> int:
    definition = config.body_fields.get(field)
    minimum = definition.minimum if definition else 0
    return max(minimum, clamp_body_value(value))


def _advance_cycle_if_needed(
    state: BodyState,
    now: datetime,
    *,
    config: PhysiologyConfig,
    rng: Optional[random.Random],
) -> None:
    while state.cycle_expires_at and now >= state.cycle_expires_at:
        current = config.cycles.get(state.cycle_key, config.cycles["stable"])
        next_key = current.next_key
        if current.key == "ebb" and state.values.get("fatigue", 0) >= 70 and "recovery" in config.cycles:
            next_key = "recovery"
        enter_cycle(state, next_key, state.cycle_expires_at, config=config, rng=rng)


def _finish_expired_event_if_needed(state: BodyState, now: datetime, *, config: PhysiologyConfig) -> None:
    if not state.active_event_key or not state.active_event_expires_at:
        return
    if now < state.active_event_expires_at:
        return
    event = config.events.get(state.active_event_key)
    if event:
        apply_interaction_delta(state, event.end_deltas, config=config)
    state.meta["last_active_event_key"] = state.active_event_key
    state.active_event_key = None
    state.active_event_started_at = None
    state.active_event_expires_at = None


def _advance_values(
    state: BodyState,
    elapsed_hours: float,
    segment_end: datetime,
    last_counterpart_message_at: Optional[datetime],
    *,
    config: PhysiologyConfig,
) -> None:
    cycle = config.cycles.get(state.cycle_key, config.cycles["stable"])
    for field in BODY_FIELDS:
        if field == "reserve":
            state.values[field] = clamp_body_field(
                field,
                state.values.get(field, 0) + cycle.reserve_growth * elapsed_hours,
                config=config,
            )
            continue
        if field == "fatigue":
            state.values[field] = _relieve_high_body_field(
                field,
                state.values.get(field, 0),
                cycle.targets.get(field, 15),
                _fatigue_relief_factor(segment_end, last_counterpart_message_at),
                elapsed_hours,
                config=config,
            )
            continue
        target = cycle.targets.get(field, state.values.get(field, 0))
        factor = APPROACH_FACTORS.get(field, 0.15)
        state.values[field] = _approach_body_field(
            field,
            state.values.get(field, 0),
            target,
            factor,
            elapsed_hours,
            config=config,
        )

    _apply_waiting_pressure(state, elapsed_hours, segment_end, last_counterpart_message_at, config=config)
    if state.active_event_key:
        event = config.events.get(state.active_event_key)
        if event:
            for field, rate in event.tick_deltas.items():
                state.values[field] = clamp_body_field(
                    field,
                    state.values.get(field, 0) + float(rate) * elapsed_hours,
                    config=config,
                )


def _approach_body_field(
    field: str,
    current: int,
    target: float,
    factor: float,
    elapsed_hours: float,
    *,
    config: PhysiologyConfig,
) -> int:
    return clamp_body_field(field, current + (target - current) * factor * elapsed_hours, config=config)


def _relieve_high_body_field(
    field: str,
    current: int,
    target: float,
    factor: float,
    elapsed_hours: float,
    *,
    config: PhysiologyConfig,
) -> int:
    if current <= target:
        return clamp_body_field(field, current, config=config)
    ratio = max(0.0, min(1.0, factor * elapsed_hours))
    return clamp_body_field(field, current + (target - current) * ratio, config=config)


def _fatigue_relief_factor(segment_end: datetime, last_counterpart_message_at: Optional[datetime]) -> float:
    if not last_counterpart_message_at:
        return 0.12
    if last_counterpart_message_at.tzinfo is None and segment_end.tzinfo is not None:
        last_counterpart_message_at = last_counterpart_message_at.replace(tzinfo=segment_end.tzinfo)
    silence_minutes = (segment_end - last_counterpart_message_at).total_seconds() / 60.0
    if silence_minutes < 30:
        return 0.12
    if silence_minutes < 120:
        return 0.16
    if silence_minutes < 360:
        return 0.22
    return 0.30


def _apply_waiting_pressure(
    state: BodyState,
    elapsed_hours: float,
    segment_end: datetime,
    last_counterpart_message_at: Optional[datetime],
    *,
    config: PhysiologyConfig,
) -> None:
    if not last_counterpart_message_at:
        return
    if last_counterpart_message_at.tzinfo is None and segment_end.tzinfo is not None:
        last_counterpart_message_at = last_counterpart_message_at.replace(tzinfo=segment_end.tzinfo)
    silence_minutes = (segment_end - last_counterpart_message_at).total_seconds() / 60.0
    if silence_minutes < 30:
        return
    if silence_minutes < 60:
        pressure_rate, possessive_rate, control_rate = 0.8, 0.3, 0.0
    elif silence_minutes < 120:
        pressure_rate, possessive_rate, control_rate = 1.5, 0.6, 0.0
    else:
        pressure_rate, possessive_rate, control_rate = 2.0, 0.9, -0.6
    state.values["pressure"] = clamp_body_field(
        "pressure", state.values.get("pressure", 0) + pressure_rate * elapsed_hours, config=config
    )
    state.values["possessiveness"] = clamp_body_field(
        "possessiveness", state.values.get("possessiveness", 0) + possessive_rate * elapsed_hours, config=config
    )
    state.values["control"] = clamp_body_field(
        "control", state.values.get("control", 0) + control_rate * elapsed_hours, config=config
    )
