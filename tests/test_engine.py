# SPDX-FileCopyrightText: 2026 Chuli (@chuli1122) <https://github.com/chuli1122>
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

from datetime import datetime, timedelta, timezone
import random
import unittest

from eventide import (
    EngineSettings,
    advance_state,
    create_initial_state,
    render_state_card,
    start_event,
)


class EngineTests(unittest.TestCase):
    def test_advance_state_moves_values_toward_cycle_and_waiting_pressure(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        state = create_initial_state(now, cycle_key="sensitive", rng=random.Random(1))
        before_pressure = state.values["pressure"]

        advance_state(
            state,
            now + timedelta(hours=3),
            last_counterpart_message_at=now - timedelta(hours=3),
        )

        self.assertGreaterEqual(state.values["pressure"], before_pressure)
        self.assertGreater(state.values["reserve"], 20)

    def test_start_event_adds_active_event_to_state_card(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        state = create_initial_state(now, rng=random.Random(2))

        started = start_event(state, "voice_or_name_trigger", now, rng=random.Random(3))
        card = render_state_card(state, now)

        self.assertTrue(started)
        self.assertIn('<active_event id="voice_or_name_trigger"', card)
        self.assertIn("声音 / 称呼触发", card)

    def test_injection_switch_hides_prompt_without_stopping_state(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        state = create_initial_state(now)

        card = render_state_card(
            state,
            now,
            settings=EngineSettings(body_cycle_enabled=True, inject_body_state_context=False),
        )

        self.assertIsNone(card)


if __name__ == "__main__":
    unittest.main()
