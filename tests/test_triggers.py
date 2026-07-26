# SPDX-FileCopyrightText: 2026 Chuli (@chuli1122) <https://github.com/chuli1122>
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

import unittest

from eventide import TriggerWord, find_trigger_matches, normalize_trigger_words


class TriggerTests(unittest.TestCase):
    def test_find_trigger_matches_uses_configured_words(self):
        matches = find_trigger_matches(
            [
                TriggerWord(key="nickname:daddy", type="nickname", text="daddy"),
                {"key": "phrase:想你", "type": "phrase", "text": "想你", "enabled": True},
            ],
            "daddy，我想你，daddy",
        )

        self.assertEqual([match.key for match in matches], ["nickname:daddy", "phrase:想你"])
        self.assertEqual(matches[0].count, 2)

    def test_normalize_trigger_words_drops_disabled_or_duplicate_empty_keys(self):
        triggers = normalize_trigger_words([
            {"key": "nickname:a", "text": "a"},
            {"key": "nickname:a", "text": "a again"},
            {"key": "", "text": ""},
        ])

        self.assertEqual([trigger.key for trigger in triggers], ["nickname:a"])


if __name__ == "__main__":
    unittest.main()
