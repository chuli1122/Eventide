# SPDX-FileCopyrightText: 2026 Chuli (@chuli1122) <https://github.com/chuli1122>
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

from __future__ import annotations

import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import DEFAULT_CONFIG, PhysiologyConfig
from .dreams import (
    DreamSeed,
    DreamSettings,
    DreamTrigger,
    apply_dream_after_effect,
    maybe_create_dream_trigger,
)
from .engine import (
    advance_state,
    apply_interaction_delta,
    create_initial_state,
    enter_cycle,
    start_event,
)
from .models import BodyDeltas, BodyState
from .prompt import body_state_payload, render_state_card
from .serialization import body_state_from_dict, body_state_to_dict
from .settings import EngineSettings
from .settlement import (
    apply_settlement_result,
    parse_settlement_result,
    render_settlement_prompt,
)


class EventideRuntime:
    """Convenience wrapper for the common host-app integration flow."""

    def __init__(
        self,
        *,
        config: PhysiologyConfig = DEFAULT_CONFIG,
        settings: Optional[EngineSettings] = None,
        dream_settings: Optional[DreamSettings] = None,
        rng: Optional[random.Random] = None,
    ) -> None:
        self.config = config
        self.settings = settings or EngineSettings()
        self.dream_settings = dream_settings or DreamSettings()
        self.rng = rng

    def create_state(self, now: datetime, *, cycle_key: str = "stable") -> BodyState:
        return create_initial_state(now, cycle_key=cycle_key, config=self.config, rng=self.rng)

    def load_state(self, data: Dict[str, Any]) -> BodyState:
        return body_state_from_dict(data)

    def dump_state(self, state: BodyState) -> Dict[str, Any]:
        return body_state_to_dict(state)

    def tick(
        self,
        state: BodyState,
        now: datetime,
        *,
        last_counterpart_message_at: Optional[datetime] = None,
    ) -> bool:
        return advance_state(
            state,
            now,
            config=self.config,
            settings=self.settings,
            last_counterpart_message_at=last_counterpart_message_at,
            rng=self.rng,
        )

    def render_card(self, state: BodyState, now: datetime) -> Optional[str]:
        return render_state_card(state, now, config=self.config, settings=self.settings)

    def tick_and_render(
        self,
        state: BodyState,
        now: datetime,
        *,
        last_counterpart_message_at: Optional[datetime] = None,
    ) -> Optional[str]:
        self.tick(state, now, last_counterpart_message_at=last_counterpart_message_at)
        return self.render_card(state, now)

    def enter_cycle(self, state: BodyState, cycle_key: str, now: datetime) -> None:
        enter_cycle(state, cycle_key, now, config=self.config, rng=self.rng, reason="manual")

    def start_event(self, state: BodyState, event_key: str, now: datetime) -> bool:
        return start_event(state, event_key, now, config=self.config, rng=self.rng)

    def apply_delta(self, state: BodyState, deltas: BodyDeltas) -> Dict[str, int]:
        return apply_interaction_delta(state, deltas, config=self.config)

    def settlement_prompt(self, state: BodyState, message_window_text: str) -> str:
        return render_settlement_prompt(state, message_window_text, config=self.config)

    def settle(self, state: BodyState, result: Any) -> BodyDeltas:
        return apply_settlement_result(state, parse_settlement_result(result), config=self.config)

    def maybe_dream(
        self,
        seed: Optional[DreamSeed],
        state: Optional[BodyState],
        now: datetime,
        *,
        last_counterpart_message_at: Optional[datetime],
    ) -> Optional[DreamTrigger]:
        return maybe_create_dream_trigger(
            seed,
            state,
            now,
            last_counterpart_message_at=last_counterpart_message_at,
            engine_settings=self.settings,
            dream_settings=self.dream_settings,
            config=self.config,
            rng=self.rng,
        )

    def apply_dream_tags(self, state: Optional[BodyState], tags: List[str]) -> Dict[str, int]:
        return apply_dream_after_effect(
            state,
            tags,
            body_enabled=self.settings.body_cycle_enabled,
            config=self.config,
        )

    def payload(self, state: BodyState) -> Dict[str, Dict[str, object]]:
        return body_state_payload(state, config=self.config)
