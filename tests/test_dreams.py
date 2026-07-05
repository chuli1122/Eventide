from datetime import datetime, timedelta, timezone
import random
import unittest

from eventide import (
    DreamSeed,
    DreamSettings,
    EngineSettings,
    apply_dream_after_effect,
    create_initial_state,
    maybe_create_dream_trigger,
)


class LowRoll(random.Random):
    def random(self):
        return 0.0


class DreamsTests(unittest.TestCase):
    def test_dream_trigger_carries_body_context_when_body_is_enabled(self):
        now = datetime(2026, 1, 1, 2, 0, tzinfo=timezone.utc)
        state = create_initial_state(now - timedelta(hours=4), cycle_key="sensitive", rng=random.Random(1))

        trigger = maybe_create_dream_trigger(
            DreamSeed(theme="一次没有完全醒来的梦", intensity="medium"),
            state,
            now,
            last_counterpart_message_at=now - timedelta(hours=3),
            engine_settings=EngineSettings(adult_private_mode_enabled=True),
            dream_settings=DreamSettings(dream_probability_multiplier=2.0),
            rng=LowRoll(),
        )

        self.assertIsNotNone(trigger)
        assert trigger is not None
        self.assertIn("当前周期：易感期", trigger.trigger_content)
        self.assertIsNotNone(trigger.body_state_snapshot)

    def test_dream_after_effect_does_not_apply_when_body_disabled(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        state = create_initial_state(now)
        before = dict(state.values)

        applied = apply_dream_after_effect(state, ["aroused", "unfinished"], body_enabled=False)

        self.assertEqual({}, applied)
        self.assertEqual(before, state.values)

    def test_dream_after_effect_applies_first_three_default_tags(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        state = create_initial_state(now)

        applied = apply_dream_after_effect(
            state,
            ["aroused", "unfinished", "possessive", "released"],
            body_enabled=True,
        )

        self.assertEqual(applied["heat"], 20)
        self.assertEqual(applied["pressure"], 24)
        self.assertEqual(applied["sensitivity"], 5)
        self.assertEqual(applied["reserve"], 3)
        self.assertEqual(applied["control"], -9)
        self.assertEqual(applied["possessiveness"], 10)
        self.assertEqual(applied["fatigue"], 0)


if __name__ == "__main__":
    unittest.main()
