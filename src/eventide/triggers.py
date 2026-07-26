# SPDX-FileCopyrightText: 2026 Chuli (@chuli1122) <https://github.com/chuli1122>
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Mapping, Union

from .settings import TriggerWord


TriggerWordInput = Union[TriggerWord, Mapping[str, object]]


@dataclass(frozen=True)
class TriggerMatch:
    key: str
    text: str
    type: str
    count: int
    input_type: str = "text"
    voice: bool = False


def normalize_trigger_words(items: Iterable[TriggerWordInput]) -> List[TriggerWord]:
    normalized = []
    seen = set()
    for item in items:
        if isinstance(item, TriggerWord):
            trigger = item
        else:
            text = str(item.get("text") or "").strip()
            trigger_type = str(item.get("type") or "nickname").strip() or "nickname"
            key = str(item.get("key") or f"{trigger_type}:{text}").strip()
            enabled = bool(item.get("enabled", True))
            trigger = TriggerWord(key=key, text=text, type=trigger_type, enabled=enabled)
        if not trigger.key or not trigger.text or trigger.key in seen:
            continue
        seen.add(trigger.key)
        normalized.append(trigger)
    return normalized


def find_trigger_matches(
    trigger_words: Iterable[TriggerWordInput],
    text: str | None,
    *,
    input_type: str | None = None,
    transcript: str | None = None,
) -> List[TriggerMatch]:
    body = "\n".join(part for part in (text or "", transcript or "") if part).lower()
    if not body:
        return []
    matches = []
    for trigger in normalize_trigger_words(trigger_words):
        if not trigger.enabled:
            continue
        hit_count = body.count(trigger.text.lower())
        if hit_count <= 0:
            continue
        matches.append(
            TriggerMatch(
                key=trigger.key,
                text=trigger.text,
                type=trigger.type,
                count=hit_count,
                input_type=input_type or "text",
                voice=input_type == "voice" and bool(transcript),
            )
        )
    return matches
