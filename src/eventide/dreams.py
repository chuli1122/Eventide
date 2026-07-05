from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from html import escape
from typing import Dict, List, Optional

from .config import DEFAULT_CONFIG, PhysiologyConfig
from .engine import apply_interaction_delta
from .models import BodyState
from .prompt import body_state_payload
from .settings import EngineSettings


@dataclass
class DreamSettings:
    dream_enabled: bool = True
    dream_silence_min_minutes: int = 120
    dream_card_min_chars: int = 2000
    dream_window_start: str = "00:00"
    dream_window_end: str = "08:30"
    dream_probability_multiplier: float = 1.0
    cooldown_hours: int = 24


@dataclass
class DreamSeed:
    theme: str
    intensity: str = "medium"
    enabled: bool = True
    expires_at: Optional[datetime] = None
    min_chars: Optional[int] = None
    seed_id: Optional[str] = None


@dataclass
class DreamTrigger:
    seed: DreamSeed
    probability: float
    roll: float
    trigger_content: str
    body_state_snapshot: Optional[Dict[str, object]]
    created_at: datetime


@dataclass
class DreamCard:
    title: str
    content: str
    summary: str
    after_effect_tags: List[str]
    body_state_snapshot: Optional[Dict[str, object]] = None
    meta: Dict[str, object] = field(default_factory=dict)


def maybe_create_dream_trigger(
    seed: Optional[DreamSeed],
    state: Optional[BodyState],
    now: datetime,
    *,
    last_counterpart_message_at: Optional[datetime],
    engine_settings: Optional[EngineSettings] = None,
    dream_settings: Optional[DreamSettings] = None,
    config: PhysiologyConfig = DEFAULT_CONFIG,
    rng: Optional[random.Random] = None,
) -> Optional[DreamTrigger]:
    engine_settings = engine_settings or EngineSettings()
    dream_settings = dream_settings or DreamSettings()
    if not seed or not seed.enabled or not dream_settings.dream_enabled:
        return None
    if seed.expires_at and _with_tz(seed.expires_at, now) <= now:
        return None
    if seed.intensity == "explicit" and not engine_settings.adult_private_mode_enabled:
        return None
    if not _in_time_window(now, dream_settings.dream_window_start, dream_settings.dream_window_end):
        return None
    if not last_counterpart_message_at:
        return None
    silence_minutes = (now - _with_tz(last_counterpart_message_at, now)).total_seconds() / 60.0
    if silence_minutes < dream_settings.dream_silence_min_minutes:
        return None
    if state and state.last_dream_card_created_at:
        last_dream = _with_tz(state.last_dream_card_created_at, now)
        if now - last_dream < timedelta(hours=dream_settings.cooldown_hours):
            return None

    probability = dream_probability(
        state,
        seed,
        engine_settings=engine_settings,
        dream_settings=dream_settings,
        config=config,
    )
    roller = rng or random
    roll = float(roller.random())
    if roll >= probability:
        return None

    snapshot = _body_snapshot(state, config=config) if state and engine_settings.body_cycle_enabled else None
    min_chars = int(seed.min_chars or dream_settings.dream_card_min_chars)
    return DreamTrigger(
        seed=seed,
        probability=probability,
        roll=roll,
        trigger_content=render_dream_trigger(seed, state, min_chars=min_chars, config=config, body_enabled=engine_settings.body_cycle_enabled),
        body_state_snapshot=snapshot,
        created_at=now,
    )


def dream_probability(
    state: Optional[BodyState],
    seed: DreamSeed,
    *,
    engine_settings: Optional[EngineSettings] = None,
    dream_settings: Optional[DreamSettings] = None,
    config: PhysiologyConfig = DEFAULT_CONFIG,
) -> float:
    engine_settings = engine_settings or EngineSettings()
    dream_settings = dream_settings or DreamSettings()
    cycle = state.cycle_key if state and engine_settings.body_cycle_enabled else "dream_only"
    if cycle == "dream_only":
        probability = 0.20
    elif cycle in {"stable", "recovery"}:
        probability = 0.12
    elif cycle in {"building", "ebb"}:
        probability = 0.20
    else:
        probability = 0.32

    active_event = config.events.get(state.active_event_key) if state and state.active_event_key else None
    if active_event and active_event.category in {"strong_physical", "possessive"}:
        probability += 0.08
    if seed.intensity == "medium":
        probability += 0.03
    elif seed.intensity == "explicit":
        probability += 0.08
    probability *= float(dream_settings.dream_probability_multiplier)
    return max(0.0, min(0.45, probability))


def render_dream_trigger(
    seed: DreamSeed,
    state: Optional[BodyState],
    *,
    min_chars: int = 2000,
    config: PhysiologyConfig = DEFAULT_CONFIG,
    body_enabled: bool = True,
) -> str:
    if state and body_enabled:
        cycle = config.cycles.get(state.cycle_key, config.cycles["stable"])
        active_event = "无"
        if state.active_event_key and state.active_event_key in config.events:
            active_event = config.events[state.active_event_key].label
        body_lines = []
        for item in body_state_payload(state, config=config).values():
            body_lines.append(f"{item['label']}：{item['level']}，{item['description']}")
        body_context = [
            f"    当前周期：{escape(cycle.label)}",
            f"    当前主身体事件：{escape(active_event)}",
            f"    当前身体状态：{escape('；'.join(body_lines))}",
        ]
    else:
        body_context = [
            "    当前周期：未提供",
            "    当前主身体事件：无",
            "    当前身体状态：本次为纯梦境生成，不读取或结算身体数值",
        ]
    parts = [
        '<random_output_event kind="dream_card">',
        "  <instruction>",
        f"    这是一次梦境卡片事件，不是普通聊天回复。写一段不少于 {int(min_chars)} 个中文字符的完整梦境。",
        "    不要解释系统规则，不要提到工具、事件或字段。",
        "  </instruction>",
        "",
        "  <dream_seed>",
        f"    你梦到了：{escape(seed.theme)}",
        f"    强度：{escape(seed.intensity)}",
        "  </dream_seed>",
        "",
        "  <current_body_context>",
        *body_context,
        "  </current_body_context>",
        "",
        "  <after_effect_rules>",
        "    结尾给出 after_effect_tags，至少选择 released / unfinished / aroused / possessive / tender 中的 1 个。",
        "    tags 只描述梦后余波，身体数值由宿主系统结算。",
        "  </after_effect_rules>",
        "</random_output_event>",
    ]
    return "\n".join(parts)


def apply_dream_after_effect(
    state: Optional[BodyState],
    tags: List[str],
    *,
    body_enabled: bool,
    config: PhysiologyConfig = DEFAULT_CONFIG,
) -> Dict[str, int]:
    if not state or not body_enabled:
        return {}
    deltas = {"heat": 0, "pressure": 0, "control": 0, "sensitivity": 0, "reserve": 0, "possessiveness": 0, "fatigue": 0}
    for tag in [str(tag).strip().lower() for tag in tags[:3]]:
        if tag == "aroused":
            deltas["heat"] += 12
            deltas["pressure"] += 7
            deltas["sensitivity"] += 5
        elif tag == "released":
            deltas["heat"] -= 10
            deltas["reserve"] -= 18
            deltas["pressure"] -= 6
            deltas["fatigue"] += 5
        elif tag == "unfinished":
            deltas["heat"] += 8
            deltas["pressure"] += 12
            deltas["reserve"] += 3
            deltas["control"] -= 5
        elif tag == "possessive":
            deltas["possessiveness"] += 10
            deltas["pressure"] += 5
            deltas["control"] -= 4
        elif tag == "tender":
            deltas["sensitivity"] += 4
            deltas["pressure"] -= 3
            deltas["fatigue"] += 2
    return apply_interaction_delta(state, deltas, config=config)


def _body_snapshot(state: BodyState, *, config: PhysiologyConfig) -> Dict[str, object]:
    cycle = config.cycles.get(state.cycle_key, config.cycles["stable"])
    return {
        "cycle_key": state.cycle_key,
        "cycle_label": cycle.label,
        "active_event_key": state.active_event_key,
        "values": dict(state.values),
    }


def _parse_time(value: str) -> time:
    hour, minute = value.split(":", 1)
    return time(int(hour), int(minute))


def _in_time_window(current: datetime, start: str, end: str) -> bool:
    current_time = current.time().replace(second=0, microsecond=0)
    start_time = _parse_time(start)
    end_time = _parse_time(end)
    if start_time <= end_time:
        return start_time <= current_time <= end_time
    return current_time >= start_time or current_time <= end_time


def _with_tz(value: datetime, reference: datetime) -> datetime:
    if value.tzinfo is None and reference.tzinfo is not None:
        return value.replace(tzinfo=reference.tzinfo)
    return value
