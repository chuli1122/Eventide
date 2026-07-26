# SPDX-FileCopyrightText: 2026 Chuli (@chuli1122) <https://github.com/chuli1122>
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

from __future__ import annotations

import json
from dataclasses import dataclass
from html import escape
from typing import Any, Dict

from .config import DEFAULT_CONFIG, BODY_FIELDS, PhysiologyConfig
from .engine import apply_interaction_delta
from .models import BodyDeltas, BodyState
from .prompt import body_state_payload


SETTLEMENT_RESULTS = {
    "neutral",
    "continued",
    "escalated",
    "interrupted",
    "cooled_down",
    "released",
}

DELTA_FIELDS = tuple(f"{field}_delta" for field in BODY_FIELDS)


@dataclass(frozen=True)
class SettlementResult:
    settlement_result: str = "neutral"
    ejaculated: bool = False
    heat_delta: int = 0
    pressure_delta: int = 0
    control_delta: int = 0
    sensitivity_delta: int = 0
    reserve_delta: int = 0
    possessiveness_delta: int = 0
    fatigue_delta: int = 0
    settlement_reason: str = ""


def settlement_json_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "settlement_reason",
            "settlement_result",
            "ejaculated",
            *DELTA_FIELDS,
        ],
        "properties": {
            "settlement_reason": {"type": "string"},
            "settlement_result": {
                "type": "string",
                "enum": sorted(SETTLEMENT_RESULTS),
            },
            "ejaculated": {"type": "boolean"},
            **{field: {"type": "integer"} for field in DELTA_FIELDS},
        },
    }


def render_settlement_prompt(
    state: BodyState,
    message_window_text: str,
    *,
    config: PhysiologyConfig = DEFAULT_CONFIG,
) -> str:
    cycle = config.cycles.get(state.cycle_key, config.cycles["stable"])
    active_event = "无"
    if state.active_event_key and state.active_event_key in config.events:
        active_event = config.events[state.active_event_key].label
    body_lines = []
    for item in body_state_payload(state, config=config).values():
        body_lines.append(f"{item['label']}：{item['level']}，{item['description']}")
    fields = ", ".join(["settlement_reason", "settlement_result", "ejaculated", *DELTA_FIELDS])
    schema = json.dumps(settlement_json_schema(), ensure_ascii=False, separators=(",", ":"))
    parts = [
        "<settlement_task>",
        "  <instruction>",
        "    你是内部身体状态的互动窗口结算器，只输出合法 JSON。",
        "    只判断这段已经发生的互动如何影响当前 AI 伴侣的身体状态；不要续写内容，不要替任何人继续说话。",
        "    消息窗口由宿主系统提供，本模块不决定窗口边界。",
        "  </instruction>",
        "",
        "  <current_body_state>",
        f"    当前周期：{escape(cycle.label)}",
        f"    当前主身体事件：{escape(active_event)}",
        f"    当前身体状态：{escape('；'.join(body_lines))}",
        "  </current_body_state>",
        "",
        "  <message_window>",
        *[f"    {escape(line)}" if line else "" for line in str(message_window_text or "").splitlines()],
        "  </message_window>",
        "",
        "  <rules>",
        "    所有 delta 都表示本窗口造成的变化量，0 表示本窗口不调整该字段。",
        "    普通互动每项 delta 建议在 -3 到 +3；强刺激或事件期间可以到 -4 到 +4。",
        "    ejaculated=false 时，reserve_delta 不应小于 0；没有释放时，蓄积感不因为亲密互动自动下降。",
        "    ejaculated=true 时，reserve_delta 需要为负数；写回函数会按当前周期补足或截断扣减。",
        "    cooled_down 只用于身体反应明确退下去；普通转话题、等待或被打断不等于冷却。",
        "  </rules>",
        "",
        "  <output>",
        f"    只输出 JSON，字段：{escape(fields)}。",
        f"    JSON schema：{escape(schema)}",
        "  </output>",
        "</settlement_task>",
    ]
    return "\n".join(parts)


def parse_settlement_result(raw: Any) -> SettlementResult:
    if isinstance(raw, SettlementResult):
        return raw
    if isinstance(raw, str):
        data = json.loads(raw)
    elif isinstance(raw, dict):
        data = raw
    else:
        raise TypeError("settlement result must be a dict, JSON string, or SettlementResult")
    return SettlementResult(
        settlement_reason=str(data.get("settlement_reason") or ""),
        settlement_result=str(data.get("settlement_result") or "neutral"),
        ejaculated=_bool_value(data.get("ejaculated")),
        heat_delta=_int_value(data.get("heat_delta")),
        pressure_delta=_int_value(data.get("pressure_delta")),
        control_delta=_int_value(data.get("control_delta")),
        sensitivity_delta=_int_value(data.get("sensitivity_delta")),
        reserve_delta=_int_value(data.get("reserve_delta")),
        possessiveness_delta=_int_value(data.get("possessiveness_delta")),
        fatigue_delta=_int_value(data.get("fatigue_delta")),
    )


def normalize_settlement_result(
    state: BodyState,
    result: Any,
    *,
    config: PhysiologyConfig = DEFAULT_CONFIG,
    delta_limit: int = 4,
) -> SettlementResult:
    parsed = parse_settlement_result(result)
    settlement_result = parsed.settlement_result if parsed.settlement_result in SETTLEMENT_RESULTS else "neutral"
    deltas = settlement_result_deltas(parsed)
    normalized = {}
    for field in BODY_FIELDS:
        value = int(deltas.get(field, 0))
        if field == "reserve":
            normalized[field] = _normalize_reserve_delta(
                state,
                value,
                ejaculated=parsed.ejaculated,
            )
        else:
            normalized[field] = _clamp(value, -int(delta_limit), int(delta_limit))
    return SettlementResult(
        settlement_reason=parsed.settlement_reason,
        settlement_result=settlement_result,
        ejaculated=parsed.ejaculated,
        heat_delta=normalized["heat"],
        pressure_delta=normalized["pressure"],
        control_delta=normalized["control"],
        sensitivity_delta=normalized["sensitivity"],
        reserve_delta=normalized["reserve"],
        possessiveness_delta=normalized["possessiveness"],
        fatigue_delta=normalized["fatigue"],
    )


def apply_settlement_result(
    state: BodyState,
    result: Any,
    *,
    config: PhysiologyConfig = DEFAULT_CONFIG,
    delta_limit: int = 4,
) -> BodyDeltas:
    normalized = normalize_settlement_result(
        state,
        result,
        config=config,
        delta_limit=delta_limit,
    )
    applied = apply_interaction_delta(state, settlement_result_deltas(normalized), config=config)
    state.meta["last_settlement"] = {
        "settlement_result": normalized.settlement_result,
        "ejaculated": normalized.ejaculated,
        "settlement_reason": normalized.settlement_reason,
        "normalized_deltas": settlement_result_deltas(normalized),
        "applied_deltas": applied,
    }
    return applied


def settlement_result_deltas(result: SettlementResult) -> BodyDeltas:
    return {
        "heat": int(result.heat_delta),
        "pressure": int(result.pressure_delta),
        "control": int(result.control_delta),
        "sensitivity": int(result.sensitivity_delta),
        "reserve": int(result.reserve_delta),
        "possessiveness": int(result.possessiveness_delta),
        "fatigue": int(result.fatigue_delta),
    }


def _normalize_reserve_delta(state: BodyState, value: int, *, ejaculated: bool) -> int:
    if not ejaculated:
        return _clamp(value, 0, 4)
    low, high = _ejaculated_reserve_limits(state)
    return _clamp(value, low, high)


def _ejaculated_reserve_limits(state: BodyState) -> tuple:
    if state.cycle_key in {"stable", "recovery"}:
        return -10, -6
    return -7, -4


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, int(value)))
