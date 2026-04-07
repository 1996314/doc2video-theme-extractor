"""
Generate a 9-panel continuous storyboard narrative prompt.
One paragraph describing 9 panels for a 16:9 storyboard image.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from validate_prompt import validate_prompt


def generate_storyboard(
    main_visual_prompt: Dict,
    driver_logic: str,
    web_refs: Optional[List[str]] = None,
) -> Tuple[Dict, Dict]:
    prefix_cn = main_visual_prompt["cn"] + f" 驱动逻辑：{driver_logic}；"
    prefix_en = main_visual_prompt["en"] + f" Driver: {driver_logic};"

    if web_refs:
        prefix_cn += f" 参考视觉：{', '.join(web_refs)}；"
        prefix_en += f" Visual references: {', '.join(web_refs)};"

    suffix_cn = (
        "九宫格连续描述，每个 panel 自然衔接，动作、光线、构图一致，"
        "转场有动机，节奏收放，主体一致性。"
        "Style: photorealistic, cinematic lighting; "
        "Layout: clean storyboard grid, thin white borders, no text."
    )
    suffix_en = (
        "Continuous 9-panel description, naturally connected, "
        "consistent action, lighting, composition, transitions motivated, "
        "pacing dynamic, subject consistency maintained. "
        "Style: photorealistic, cinematic lighting; "
        "Layout: clean storyboard grid, thin white borders, no text."
    )

    cn_prompt = prefix_cn + suffix_cn
    en_prompt = prefix_en + suffix_en

    validation = {
        "cn": validate_prompt(cn_prompt, lang="cn"),
        "en": validate_prompt(en_prompt, lang="en"),
    }
    return {"cn": cn_prompt, "en": en_prompt}, validation
