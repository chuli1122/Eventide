# SPDX-FileCopyrightText: 2026 Chuli (@chuli1122) <https://github.com/chuli1122>
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from eventide import EventideRuntime, SettlementResult


class EventideRuntimeTests(unittest.TestCase):
    def test_runtime_tick_and_render_returns_state_card(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        runtime = EventideRuntime()
        state = runtime.create_state(now)

        card = runtime.tick_and_render(
            state,
            now + timedelta(hours=2),
            last_counterpart_message_at=now,
        )

        self.assertIsNotNone(card)
        self.assertIn("<ephemeral_state", card)
        self.assertGreater(state.values["reserve"], 20)

    def test_runtime_wraps_events_settlement_dream_tags_and_serialization(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        runtime = EventideRuntime()
        state = runtime.create_state(now, cycle_key="sensitive")
        state.values["reserve"] = 70

        self.assertTrue(runtime.start_event(state, "voice_or_name_trigger", now))
        prompt = runtime.settlement_prompt(state, "对方：继续")
        self.assertIn("message_window", prompt)

        applied = runtime.settle(
            state,
            SettlementResult(
                settlement_result="released",
                ejaculated=True,
                reserve_delta=0,
            ),
        )
        self.assertLess(applied["reserve"], 0)

        dream_applied = runtime.apply_dream_tags(state, ["unfinished"])
        self.assertGreaterEqual(dream_applied["reserve"], 0)

        restored = runtime.load_state(runtime.dump_state(state))
        self.assertEqual(restored.values, state.values)


if __name__ == "__main__":
    unittest.main()
