# SPDX-FileCopyrightText: 2026 Chuli (@chuli1122) <https://github.com/chuli1122>
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

from datetime import datetime, timedelta, timezone

from eventide import EventideRuntime


def main() -> None:
    runtime = EventideRuntime()
    now = datetime.now(timezone.utc)
    state = runtime.create_state(now)

    state_card = runtime.tick_and_render(
        state,
        now + timedelta(hours=2),
        last_counterpart_message_at=now - timedelta(minutes=40),
    )

    # Put this string into your model's hidden/system context.
    print(state_card)

    # Save this dict in your database, JSON file, or app state.
    print(runtime.dump_state(state))


if __name__ == "__main__":
    main()
