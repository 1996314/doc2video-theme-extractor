"""
Generate main visual prompt from a visual structure dict.
Outputs CN/EN bilingual prompts with optional validation.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from analyze_frames import convert_structure_to_prompt
from validate_prompt import validate_prompt


def generate_main_visual(
    visual_structure: Dict, theme: str, style: str
) -> Tuple[Dict, Dict]:
    prompt = convert_structure_to_prompt(visual_structure, theme, style)
    validation = {
        "cn": validate_prompt(prompt["cn"], lang="cn"),
        "en": validate_prompt(prompt["en"], lang="en"),
    }
    return prompt, validation
