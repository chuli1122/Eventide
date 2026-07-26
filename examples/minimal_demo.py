# SPDX-FileCopyrightText: 2026 Chuli (@chuli1122) <https://github.com/chuli1122>
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

from datetime import datetime, timedelta, timezone

from eventide import (
    DreamSeed,
    DreamSettings,
    EngineSettings,
    advance_state,
    create_initial_state,
    maybe_create_dream_trigger,
    render_state_card,
    start_event,
)


class AlwaysRollIn:
    def random(self) -> float:
        return 0.0


def main() -> None:
    now = datetime(2026, 1, 1, 0, 30, tzinfo=timezone.utc)
    state = create_initial_state(now, cycle_key="building")
    later = now + timedelta(hours=2)
    advance_state(state, later, last_counterpart_message_at=now - timedelta(hours=2))
    start_event(state, "voice_or_name_trigger", later)

    print(render_state_card(state, later, settings=EngineSettings(adult_private_mode_enabled=True)))
    print()

    dream = maybe_create_dream_trigger(
        DreamSeed(theme="一次被靠近、被撩拨却没有完全醒来的梦", intensity="medium"),
        state,
        later + timedelta(hours=2),
        last_counterpart_message_at=later - timedelta(hours=1),
        engine_settings=EngineSettings(adult_private_mode_enabled=True),
        dream_settings=DreamSettings(dream_probability_multiplier=2.0),
        rng=AlwaysRollIn(),
    )
    if dream:
        print(dream.trigger_content)
    else:
        print("No dream trigger this time.")


if __name__ == "__main__":
    main()
