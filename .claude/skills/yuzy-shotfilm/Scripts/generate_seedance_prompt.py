"""
Generate Seedance 2.0 continuous video prompt from storyboard.

Per Higgsfield official guide:
  - Seedance prompts should be SHORT (camera + subject + action)
  - Complex visual descriptions belong in Popcorn (image generation stage)
"""

from __future__ import annotations

from typing import Dict, Tuple

from validate_prompt import validate_prompt


def generate_seedance_prompt(
    storyboard_prompt: Dict,
    driver_logic: str,
    language: str = "cn",
) -> Tuple[str, Dict]:
    if language == "cn":
        base = storyboard_prompt["cn"]
    else:
        base = storyboard_prompt["en"]

    seedance_suffix = (
        " 镜头路径连续，转场有动机，节奏收放，主体一致，"
        "从局部到整体、从主观到空间、从现实到强化连续演变，"
        "适用于 Seedance 2.0 连续视频生成。"
    )

    seedance_prompt = base + seedance_suffix
    validation = validate_prompt(seedance_prompt, lang=language)

    return seedance_prompt, validation
