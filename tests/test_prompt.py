# SPDX-FileCopyrightText: 2026 Chuli (@chuli1122) <https://github.com/chuli1122>
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

from datetime import datetime, timezone
import random
import unittest

from eventide import create_initial_state, render_state_card


class PromptTests(unittest.TestCase):
    def test_state_card_contains_cycle_description_and_no_private_name(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        state = create_initial_state(now, cycle_key="ebb", rng=random.Random(1))

        card = render_state_card(state, now)

        self.assertIn('<ephemeral_state kind="body_cycle" scope="current_turn">', card)
        self.assertIn("退潮期", card)
        self.assertIn("没要够的感觉还堵着", card)
        self.assertIn("<body_state>", card)
        self.assertIn("对方", card)


if __name__ == "__main__":
    unittest.main()
