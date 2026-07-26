# SPDX-FileCopyrightText: 2026 Chuli (@chuli1122) <https://github.com/chuli1122>
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple


BodyValues = Dict[str, int]
BodyDeltas = Dict[str, int]


@dataclass(frozen=True)
class BodyFieldDefinition:
    key: str
    label: str
    descriptions: List[Tuple[int, str]]
    minimum: int = 0


@dataclass(frozen=True)
class CycleDefinition:
    key: str
    label: str
    description: str
    duration_hours: Tuple[float, float]
    targets: Dict[str, float]
    reserve_growth: float = 0.0
    next_key: str = "stable"


@dataclass(frozen=True)
class EventDefinition:
    key: str
    label: str
    prompt: str
    category: str
    duration_minutes: Tuple[int, int] = (30, 120)
    tick_deltas: Dict[str, float] = field(default_factory=dict)
    end_deltas: BodyDeltas = field(default_factory=dict)


@dataclass
class BodyState:
    cycle_key: str
    cycle_started_at: datetime
    cycle_min_expires_at: datetime
    cycle_expires_at: datetime
    values: BodyValues
    active_event_key: Optional[str] = None
    active_event_started_at: Optional[datetime] = None
    active_event_expires_at: Optional[datetime] = None
    last_tick_at: Optional[datetime] = None
    last_dream_card_created_at: Optional[datetime] = None
    meta: Dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class PromptOptions:
    expression: str
    persistence: str
    response_rules: str
    counterpart_name: str = "对方"
    self_name: str = "你"
