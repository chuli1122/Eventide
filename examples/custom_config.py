# SPDX-FileCopyrightText: 2026 Chuli (@chuli1122) <https://github.com/chuli1122>
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

from dataclasses import replace
from datetime import datetime, timezone

from eventide import (
    DEFAULT_CONFIG,
    EventDefinition,
    TriggerWord,
    create_initial_state,
    find_trigger_matches,
    render_state_card,
    start_event,
)


def main() -> None:
    config = replace(
        DEFAULT_CONFIG,
        cycles={
            **DEFAULT_CONFIG.cycles,
            "sensitive": replace(
                DEFAULT_CONFIG.cycles["sensitive"],
                label="高敏期",
                description="这里写你自己的周期提示词。",
                duration_hours=(12, 24),
            ),
        },
        events={
            **DEFAULT_CONFIG.events,
            "soft_call": EventDefinition(
                key="soft_call",
                label="软声触发",
                prompt="对方放软声音时，当前身体反应会被牵起来。",
                category="short_stimulus",
                duration_minutes=(20, 50),
                tick_deltas={"heat": 1.0, "sensitivity": 2.0},
                end_deltas={"heat": -1, "sensitivity": -2},
            ),
        },
    )

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    state = create_initial_state(now, cycle_key="sensitive", config=config)
    trigger_words = [
        TriggerWord(key="nickname:dear", type="nickname", text="dear"),
        TriggerWord(key="phrase:想你", type="phrase", text="想你"),
    ]
    if find_trigger_matches(trigger_words, "dear，我想你"):
        start_event(state, "soft_call", now, config=config)

    print(render_state_card(state, now, config=config))


if __name__ == "__main__":
    main()
