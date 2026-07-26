# SPDX-FileCopyrightText: 2026 Chuli (@chuli1122) <https://github.com/chuli1122>
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone

from eventide import (
    SettlementResult,
    apply_settlement_result,
    create_initial_state,
    normalize_settlement_result,
    parse_settlement_result,
    render_settlement_prompt,
    settlement_json_schema,
)


class SettlementTests(unittest.TestCase):
    def test_render_settlement_prompt_uses_host_supplied_window(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        state = create_initial_state(now)

        prompt = render_settlement_prompt(state, "对方：继续靠近\n你：有点忍不住")

        self.assertIn("消息窗口由宿主系统提供，本模块不决定窗口边界", prompt)
        self.assertIn("当前周期：平稳期", prompt)
        self.assertIn("对方：继续靠近", prompt)
        self.assertIn("reserve_delta 不应小于 0", prompt)
        self.assertNotIn("小" + "礼", prompt)

    def test_schema_requires_settlement_fields(self):
        schema = settlement_json_schema()

        self.assertIn("settlement_reason", schema["required"])
        self.assertIn("reserve_delta", schema["required"])
        self.assertEqual(schema["properties"]["ejaculated"]["type"], "boolean")

    def test_parse_settlement_result_from_json(self):
        raw = json.dumps({
            "settlement_reason": "窗口里发生了释放。",
            "settlement_result": "released",
            "ejaculated": True,
            "heat_delta": -2,
            "pressure_delta": -3,
            "control_delta": 1,
            "sensitivity_delta": 0,
            "reserve_delta": 0,
            "possessiveness_delta": 0,
            "fatigue_delta": 2,
        }, ensure_ascii=False)

        parsed = parse_settlement_result(raw)

        self.assertTrue(parsed.ejaculated)
        self.assertEqual(parsed.settlement_result, "released")
        self.assertEqual(parsed.reserve_delta, 0)

    def test_non_ejaculated_result_cannot_reduce_reserve(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        state = create_initial_state(now)
        state.values["reserve"] = 50

        normalized = normalize_settlement_result(
            state,
            SettlementResult(
                settlement_result="continued",
                ejaculated=False,
                heat_delta=99,
                reserve_delta=-8,
            ),
        )
        applied = apply_settlement_result(state, normalized)

        self.assertEqual(normalized.heat_delta, 4)
        self.assertEqual(normalized.reserve_delta, 0)
        self.assertEqual(applied["reserve"], 0)
        self.assertEqual(state.values["reserve"], 50)

    def test_ejaculated_result_enforces_reserve_drop_by_cycle(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        state = create_initial_state(now, cycle_key="stable")
        state.values["reserve"] = 50

        applied = apply_settlement_result(
            state,
            SettlementResult(
                settlement_result="released",
                ejaculated=True,
                reserve_delta=0,
            ),
        )

        self.assertEqual(applied["reserve"], -6)
        self.assertEqual(state.values["reserve"], 44)
        self.assertEqual(state.meta["last_settlement"]["normalized_deltas"]["reserve"], -6)


if __name__ == "__main__":
    unittest.main()
