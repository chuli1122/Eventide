# SPDX-FileCopyrightText: 2026 Chuli (@chuli1122) <https://github.com/chuli1122>
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Dict, Optional

from .config import DEFAULT_CONFIG, BODY_FIELDS, PhysiologyConfig
from .models import BodyState
from .settings import EngineSettings


BODY_LEVELS = {"低", "中低", "中", "中高", "高"}


def render_state_card(
    state: BodyState,
    now: datetime,
    *,
    config: PhysiologyConfig = DEFAULT_CONFIG,
    settings: Optional[EngineSettings] = None,
) -> Optional[str]:
    settings = settings or EngineSettings()
    if not settings.body_cycle_enabled or not settings.inject_body_state_context:
        return None

    cycle = config.cycles.get(state.cycle_key, config.cycles["stable"])
    cycle_line = f"你处在{escape(cycle.label)}"
    if cycle.description:
        cycle_line += f"：{escape(cycle.description)}"
    cycle_line += f"，预计还剩 {_format_remaining(state.cycle_expires_at, now)}。"
    parts = [
        '<ephemeral_state kind="body_cycle" scope="current_turn">',
        "  <cycle>",
        f"    {cycle_line}",
        "  </cycle>",
        "",
    ]

    if state.active_event_key:
        event = config.events.get(state.active_event_key)
        if event:
            parts.extend([
                f'  <active_event id="{escape(event.key)}" expires_at="{escape(state.active_event_expires_at.isoformat() if state.active_event_expires_at else "")}">',
                f"    当前事件：{escape(event.label)}，预计还剩 {_format_remaining(state.active_event_expires_at, now)}。",
                *[f"    {escape(line)}" for line in event.prompt.splitlines()],
                "  </active_event>",
                "",
            ])

    prompt = config.prompt_options
    parts.extend([
        "  <body_state>",
        *[f"    {line}" for line in _body_state_lines(state, config)],
        "  </body_state>",
        "",
        "  <expression>",
        *[f"    {escape(line)}" for line in prompt.expression.splitlines()],
        "  </expression>",
        "",
        "  <persistence>",
        *[f"    {escape(line)}" for line in prompt.persistence.splitlines()],
        "  </persistence>",
        "",
        "  <response_rules>",
        *[f"    {escape(line)}" if line else "" for line in prompt.response_rules.splitlines()],
        "  </response_rules>",
        "</ephemeral_state>",
    ])
    return "\n".join(parts)


def body_state_payload(
    state: BodyState,
    *,
    config: PhysiologyConfig = DEFAULT_CONFIG,
) -> Dict[str, Dict[str, object]]:
    payload = {}
    for field in BODY_FIELDS:
        definition = config.body_fields[field]
        value = max(0, min(100, int(state.values.get(field, 0))))
        description = body_description(field, value, config=config)
        level, detail = split_level_description(value, description)
        payload[field] = {
            "value": value,
            "level": level,
            "description": detail,
            "label": definition.label,
        }
    return payload


def body_level(value: int) -> str:
    if value < 20:
        return "低"
    if value < 40:
        return "中低"
    if value < 60:
        return "中"
    if value < 80:
        return "中高"
    return "高"


def body_description(field: str, value: int, *, config: PhysiologyConfig = DEFAULT_CONFIG) -> str:
    entries = config.body_fields[field].descriptions
    chosen = entries[0][1]
    for threshold, description in entries:
        if value >= threshold:
            chosen = description
    return chosen


def split_level_description(value: int, description: str) -> tuple:
    if "，" in description:
        level, detail = description.split("，", 1)
        level = level.strip()
        if level in BODY_LEVELS:
            return level, detail.strip()
    return body_level(value), description


def _body_state_lines(state: BodyState, config: PhysiologyConfig) -> list:
    lines = []
    for field in BODY_FIELDS:
        definition = config.body_fields[field]
        value = max(0, min(100, int(state.values.get(field, 0))))
        lines.append(f"{escape(definition.label)}：{escape(body_description(field, value, config=config))}")
    return lines


def _format_remaining(expires_at: Optional[datetime], now: datetime) -> str:
    if not expires_at:
        return "未知"
    seconds = max(0, int((expires_at - now).total_seconds()))
    minutes = max(1, round(seconds / 60))
    if minutes < 90:
        return f"{minutes} 分钟"
    hours = round(minutes / 60)
    if hours < 48:
        return f"{hours} 小时"
    days = round(hours / 24)
    return f"{days} 天"
