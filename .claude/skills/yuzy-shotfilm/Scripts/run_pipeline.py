"""
Doc2Video Full Pipeline

完整流程：
  1. 解析文档 → 提取功能点
  2. CDP + Headless 抓取 Instagram 视频 + 元数据
  3. OpenCV 抽帧
  4. AI Vision 帧分析 → 视觉结构
  5. 生成主视觉 prompt
  6. 生成九宫格连续叙事
  7. 人工确认后 → 生成 Seedance 2.0 prompt

Usage:
    python run_pipeline.py --tag seedance --num 3 --theme "可爱即恐怖" --driver "形态驱动"
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from fetch_instagram_video import fetch_headless_videos, fetch_hybrid
from extract_frames import extract_frames
from analyze_frames import analyze_frames, convert_structure_to_prompt
from generate_storyboard import generate_storyboard
from generate_seedance_prompt import generate_seedance_prompt


def run(
    tag: str,
    num_videos: int = 3,
    theme: str = "",
    style: str = "cinematic / photorealistic",
    driver_logic: str = "形态驱动",
    output_dir: str = "ig_videos",
    frames_dir: str = "ig_frames",
    use_cdp: bool = False,
    cdp_url: str = "http://localhost:9222",
):
    print("=" * 60)
    print("  Doc2Video Pipeline")
    print("=" * 60)

    # Step 1: Fetch videos
    print(f"\n[Step 1] Fetching #{tag} videos...")
    if use_cdp:
        data = fetch_hybrid(tag, num_videos, output_dir, cdp_url)
        videos = data["videos"]
        metadata = data.get("metadata")
    else:
        videos = fetch_headless_videos(tag, num_videos, output_dir)
        metadata = None

    if not videos:
        print("No videos downloaded. Exiting.")
        return

    # Step 2: Extract frames
    print(f"\n[Step 2] Extracting frames...")
    all_frames = []
    for vid in videos:
        vid_frames_dir = os.path.join(frames_dir, f"vid_{vid['index']}")
        frames = extract_frames(vid["path"], num_frames=9, save_dir=vid_frames_dir)
        all_frames.append({"video": vid, "frames": frames})
        print(f"  Video {vid['index']}: {len(frames)} frames extracted")

    # Step 3: Analyze frames
    print(f"\n[Step 3] Analyzing frames (use Vision API for real analysis)...")
    structures = []
    for item in all_frames:
        structure = analyze_frames(item["frames"])
        structures.append(structure)
        print(f"  Video {item['video']['index']}: {structure.get('subject', 'N/A')}")

    # Step 4: Generate main visual
    print(f"\n[Step 4] Generating main visual prompt...")
    best_structure = structures[0]
    main_visual = convert_structure_to_prompt(best_structure, theme, style)
    print(f"  CN: {main_visual['cn'][:100]}...")
    print(f"  EN: {main_visual['en'][:100]}...")

    # Step 5: Generate storyboard
    print(f"\n[Step 5] Generating storyboard...")
    storyboard, sb_validation = generate_storyboard(main_visual, driver_logic)
    print(f"  CN length: {len(storyboard['cn'])} chars")
    print(f"  EN length: {len(storyboard['en'])} chars")

    # Step 6: Generate Seedance prompt
    print(f"\n[Step 6] Generating Seedance 2.0 prompt...")
    seedance, sd_validation = generate_seedance_prompt(storyboard, driver_logic)
    print(f"  Prompt length: {len(seedance)} chars")

    # Save all outputs
    output = {
        "tag": tag,
        "theme": theme,
        "style": style,
        "driver_logic": driver_logic,
        "videos_downloaded": len(videos),
        "metadata": metadata,
        "visual_structure": best_structure,
        "main_visual": main_visual,
        "storyboard": storyboard,
        "seedance_prompt": seedance,
    }

    output_path = os.path.join(output_dir, "pipeline_output.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[Done] Output saved to {output_path}")
    print(f"\n{'=' * 60}")
    print("  Main Visual (EN):")
    print(f"  {main_visual['en']}")
    print(f"\n  Storyboard preview (EN, first 200 chars):")
    print(f"  {storyboard['en'][:200]}...")
    print(f"\n  Seedance prompt preview (first 200 chars):")
    print(f"  {seedance[:200]}...")
    print(f"{'=' * 60}")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Doc2Video Full Pipeline")
    parser.add_argument("--tag", default="seedance", help="Instagram tag")
    parser.add_argument("--num", type=int, default=3, help="Videos to download")
    parser.add_argument("--theme", default="", help="Video theme")
    parser.add_argument("--style", default="cinematic / photorealistic")
    parser.add_argument("--driver", default="形态驱动")
    parser.add_argument("--output", default="ig_videos")
    parser.add_argument("--frames", default="ig_frames")
    parser.add_argument("--cdp", action="store_true", help="Use CDP for metadata")
    parser.add_argument("--cdp-url", default="http://localhost:9222")
    args = parser.parse_args()

    run(
        tag=args.tag,
        num_videos=args.num,
        theme=args.theme,
        style=args.style,
        driver_logic=args.driver,
        output_dir=args.output,
        frames_dir=args.frames,
        use_cdp=args.cdp,
        cdp_url=args.cdp_url,
    )
