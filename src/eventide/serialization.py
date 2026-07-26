# SPDX-FileCopyrightText: 2026 Chuli (@chuli1122) <https://github.com/chuli1122>
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from .models import BodyState


def body_state_to_dict(state: BodyState) -> Dict[str, Any]:
    return {
        "cycle_key": state.cycle_key,
        "cycle_started_at": _datetime_to_str(state.cycle_started_at),
        "cycle_min_expires_at": _datetime_to_str(state.cycle_min_expires_at),
        "cycle_expires_at": _datetime_to_str(state.cycle_expires_at),
        "values": {str(key): int(value) for key, value in state.values.items()},
        "active_event_key": state.active_event_key,
        "active_event_started_at": _datetime_to_str(state.active_event_started_at),
        "active_event_expires_at": _datetime_to_str(state.active_event_expires_at),
        "last_tick_at": _datetime_to_str(state.last_tick_at),
        "last_dream_card_created_at": _datetime_to_str(state.last_dream_card_created_at),
        "meta": dict(state.meta or {}),
    }


def body_state_from_dict(data: Dict[str, Any]) -> BodyState:
    return BodyState(
        cycle_key=str(data.get("cycle_key") or "stable"),
        cycle_started_at=_datetime_from_str(data.get("cycle_started_at")),
        cycle_min_expires_at=_datetime_from_str(data.get("cycle_min_expires_at")),
        cycle_expires_at=_datetime_from_str(data.get("cycle_expires_at")),
        values=_values_from_dict(data.get("values")),
        active_event_key=_optional_str(data.get("active_event_key")),
        active_event_started_at=_optional_datetime_from_str(data.get("active_event_started_at")),
        active_event_expires_at=_optional_datetime_from_str(data.get("active_event_expires_at")),
        last_tick_at=_optional_datetime_from_str(data.get("last_tick_at")),
        last_dream_card_created_at=_optional_datetime_from_str(data.get("last_dream_card_created_at")),
        meta=dict(data.get("meta") if isinstance(data.get("meta"), dict) else {}),
    )


def _datetime_to_str(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value else None


def _datetime_from_str(value: Any) -> datetime:
    parsed = _optional_datetime_from_str(value)
    if parsed is None:
        raise ValueError("required datetime field is missing")
    return parsed


def _optional_datetime_from_str(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text)


def _values_from_dict(value: Any) -> Dict[str, int]:
    if not isinstance(value, dict):
        return {}
    values: Dict[str, int] = {}
    for key, raw in value.items():
        try:
            values[str(key)] = int(raw)
        except (TypeError, ValueError):
            continue
    return values


def _optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
