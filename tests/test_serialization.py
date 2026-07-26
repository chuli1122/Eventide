# SPDX-FileCopyrightText: 2026 Chuli (@chuli1122) <https://github.com/chuli1122>
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from eventide import body_state_from_dict, body_state_to_dict, create_initial_state


class SerializationTests(unittest.TestCase):
    def test_body_state_round_trips_through_dict(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        state = create_initial_state(now)
        state.active_event_key = "voice_or_name_trigger"
        state.active_event_started_at = now
        state.active_event_expires_at = now
        state.last_dream_card_created_at = now
        state.meta["note"] = "saved"

        restored = body_state_from_dict(body_state_to_dict(state))

        self.assertEqual(restored.cycle_key, state.cycle_key)
        self.assertEqual(restored.values, state.values)
        self.assertEqual(restored.active_event_key, "voice_or_name_trigger")
        self.assertEqual(restored.last_dream_card_created_at, now)
        self.assertEqual(restored.meta["note"], "saved")

    def test_body_state_from_dict_accepts_z_suffix(self):
        restored = body_state_from_dict({
            "cycle_key": "stable",
            "cycle_started_at": "2026-01-01T00:00:00Z",
            "cycle_min_expires_at": "2026-01-01T00:00:00Z",
            "cycle_expires_at": "2026-01-02T00:00:00Z",
            "values": {"heat": "30"},
        })

        self.assertEqual(restored.cycle_started_at.tzinfo, timezone.utc)
        self.assertEqual(restored.values["heat"], 30)


if __name__ == "__main__":
    unittest.main()
