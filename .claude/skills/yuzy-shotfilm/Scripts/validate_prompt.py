"""
Prompt Validator for Seedance 2.0 / Storyboard prompts.

Checks: length, temporal keywords, camera consistency, conflicts, style tags.
"""

from __future__ import annotations

import re
from typing import Dict


TEMPORAL_KEYWORDS = [
    "then", "next", "after", "before", "suddenly", "meanwhile",
    "first", "finally", "continuous", "seamless", "transition",
    "然后", "接着", "随后", "突然", "最后", "连续", "转场",
]

CAMERA_KEYWORDS = [
    "close-up", "medium", "wide", "aerial", "tracking", "dolly",
    "pan", "tilt", "orbit", "static", "push-in", "pull-back",
    "特写", "中景", "全景", "航拍", "跟拍", "推", "拉", "固定",
]

STYLE_TAGS = [
    "photorealistic", "cinematic", "film grain", "shallow",
    "4K", "35mm", "storyboard", "grid",
]

CONFLICT_PAIRS = [
    ("static", "tracking"),
    ("close-up", "aerial"),
    ("bright", "dark"),
    ("固定", "跟拍"),
]


def validate_prompt(prompt: str, lang: str = "cn") -> Dict:
    text = prompt.lower()
    word_count = len(prompt.split()) if lang == "en" else len(prompt)

    temporal = [kw for kw in TEMPORAL_KEYWORDS if kw in text]
    cameras = [kw for kw in CAMERA_KEYWORDS if kw in text]
    styles = [kw for kw in STYLE_TAGS if kw in text]

    conflicts = []
    for a, b in CONFLICT_PAIRS:
        if a in text and b in text:
            conflicts.append(f"{a} vs {b}")

    length_ok = 50 < word_count < 2000 if lang == "en" else 30 < word_count < 3000

    return {
        "length": word_count,
        "length_ok": length_ok,
        "temporal_keywords": temporal,
        "temporal_count": len(temporal),
        "camera_keywords": cameras,
        "camera_count": len(cameras),
        "style_tags": styles,
        "conflicts": conflicts,
        "conflict_free": len(conflicts) == 0,
        "overall": "✅" if (length_ok and len(conflicts) == 0 and len(temporal) > 0) else "⚠️",
    }
