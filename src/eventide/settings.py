# SPDX-FileCopyrightText: 2026 Chuli (@chuli1122) <https://github.com/chuli1122>
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class TriggerWord:
    key: str
    text: str
    type: str = "nickname"
    enabled: bool = True


@dataclass
class EngineSettings:
    body_cycle_enabled: bool = True
    inject_body_state_context: bool = True
    adult_private_mode_enabled: bool = False
    safeword: str = ""
    trigger_words: List[TriggerWord] = field(default_factory=list)
    event_probability_multiplier: float = 1.0
