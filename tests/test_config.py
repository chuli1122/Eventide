import unittest

from eventide import DEFAULT_CONFIG


class ConfigTests(unittest.TestCase):
    def test_default_config_keeps_full_cycle_and_event_table(self):
        self.assertEqual(
            list(DEFAULT_CONFIG.cycles),
            [
                "stable",
                "building",
                "preheat",
                "sensitive",
                "ebb",
                "recovery",
            ],
        )
        self.assertEqual(
            list(DEFAULT_CONFIG.events),
            [
                "morning_arousal",
                "night_heat",
                "cycle_surge",
                "holding_back",
                "demanding",
                "marking_impulse",
                "nesting",
                "scent_aftereffect",
                "voice_or_name_trigger",
                "dream_afterglow",
                "control_slip",
                "closeness_hunger",
                "pheromone_disorder",
                "delayed_heat",
                "low_fever_cling",
                "waiting_restless",
                "restraint_rebound",
                "strange_calm",
            ],
        )

    def test_default_events_have_runtime_effects(self):
        for event in DEFAULT_CONFIG.events.values():
            with self.subTest(event=event.key):
                self.assertLessEqual(event.duration_minutes[0], event.duration_minutes[1])
                self.assertTrue(event.category)
                self.assertTrue(event.tick_deltas)
                self.assertTrue(event.end_deltas)

    def test_default_possessiveness_floor_matches_runtime_system(self):
        self.assertEqual(DEFAULT_CONFIG.body_fields["possessiveness"].minimum, 40)

    def test_default_response_rules_are_left_for_host_customization(self):
        self.assertEqual(DEFAULT_CONFIG.prompt_options.response_rules, "")


if __name__ == "__main__":
    unittest.main()
