"""
Frame Analyzer — extracts visual structure from video keyframes.

Two modes:
  1. Stub mode (default): returns a placeholder structure for pipeline testing.
  2. Claude Vision mode: reads actual frame images and returns a real analysis.
     This mode is used when running inside Cursor with Claude as the agent —
     Claude can directly read .jpg files via the Read tool and fill in the structure.

The pipeline calls analyze_frames() which returns the stub.
When running through Cursor agent, the agent reads frames with Vision,
then calls build_structure_from_vision() with the real observations.
"""

from __future__ import annotations

from typing import Dict, List, Optional


def analyze_frames(frames: List[str]) -> Dict:
    """
    Stub: returns a placeholder visual structure.
    In production, replace with Vision API call or use build_structure_from_vision().
    """
    return {
        "subject": "(pending Vision analysis)",
        "transformation": [],
        "camera_path": [],
        "lighting": [],
        "style": "",
        "frames_analyzed": len(frames),
        "frame_paths": frames,
        "note": "Stub output. Use Cursor agent Vision to analyze frames, then call build_structure_from_vision().",
    }


def build_structure_from_vision(
    subject: str,
    transformation: List[str],
    camera_path: List[str],
    lighting: List[str],
    style: str,
    setting: Optional[str] = None,
    narrative_arc: Optional[str] = None,
    skin_detail: Optional[str] = None,
    ui_elements: Optional[List[str]] = None,
    source: Optional[str] = None,
) -> Dict:
    """
    Build a visual structure dict from real Vision analysis observations.
    Call this after the Cursor agent has read and analyzed the frame images.
    """
    structure = {
        "subject": subject,
        "transformation": transformation,
        "camera_path": camera_path,
        "lighting": lighting,
        "style": style,
    }
    if setting:
        structure["setting"] = setting
    if narrative_arc:
        structure["narrative_arc"] = narrative_arc
    if skin_detail:
        structure["skin_detail"] = skin_detail
    if ui_elements:
        structure["ui_elements"] = ui_elements
    if source:
        structure["source"] = source
    return structure


def convert_structure_to_prompt(visual_structure: Dict, theme: str, style: str) -> Dict:
    """Convert a visual structure dict into CN/EN prompt pair."""
    subject = visual_structure.get("subject", "")
    transformations = visual_structure.get("transformation", [])
    cameras = visual_structure.get("camera_path", [])
    lights = visual_structure.get("lighting", [])
    setting = visual_structure.get("setting", "")
    narrative = visual_structure.get("narrative_arc", "")

    prompt_cn = f"主题：{theme}；风格：{style}；"
    prompt_en = f"Theme: {theme}; Style: {style};"

    if subject:
        prompt_cn += f"主体：{subject}；"
        prompt_en += f" Subject: {subject};"
    if transformations:
        prompt_cn += f"形态演变：{', '.join(transformations)}；"
        prompt_en += f" Transformations: {', '.join(transformations)};"
    if cameras:
        prompt_cn += f"镜头路径：{', '.join(cameras)}；"
        prompt_en += f" Camera path: {', '.join(cameras)};"
    if lights:
        prompt_cn += f"光线：{', '.join(lights)}；"
        prompt_en += f" Lighting: {', '.join(lights)};"
    if setting:
        prompt_cn += f"场景：{setting}；"
        prompt_en += f" Setting: {setting};"
    if narrative:
        prompt_cn += f"叙事：{narrative}；"
        prompt_en += f" Narrative: {narrative};"

    return {"cn": prompt_cn, "en": prompt_en}
