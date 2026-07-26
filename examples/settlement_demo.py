# SPDX-FileCopyrightText: 2026 Chuli (@chuli1122) <https://github.com/chuli1122>
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

from datetime import datetime, timezone

from eventide import (
    SettlementResult,
    apply_settlement_result,
    create_initial_state,
    render_settlement_prompt,
)


def main() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    state = create_initial_state(now, cycle_key="sensitive")
    state.values["reserve"] = 70

    message_window_text = """
对方：还要继续吗
你：已经快忍不住了
""".strip()

    print(render_settlement_prompt(state, message_window_text))
    print()

    # In a host app, this result can come from an LLM call using the prompt above.
    applied = apply_settlement_result(
        state,
        SettlementResult(
            settlement_reason="窗口里明确发生了释放。",
            settlement_result="released",
            ejaculated=True,
            reserve_delta=0,
            fatigue_delta=3,
        ),
    )

    print({"applied": applied, "values": state.values})


if __name__ == "__main__":
    main()
