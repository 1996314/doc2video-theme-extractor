"""
Doc2Video Full Pipeline

Usage:
    # Auto-detect product type, fetch refs, extract frames, generate prompts
    python run_pipeline.py --doc-url "https://docs.google.com/document/d/.../export?format=txt" --num 3

    # With specific tag override
    python run_pipeline.py --tag seedance --num 3 --theme "可爱即恐怖" --driver "形态驱动"

    # With local video file (skip fetch)
    python run_pipeline.py --video path/to/video.mp4 --theme "my theme"
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.request

from fetch_visual_references import fetch_references, fetch_instagram, fetch_website
from extract_frames import extract_frames
from analyze_frames import analyze_frames, convert_structure_to_prompt
from generate_main_visual import generate_main_visual
from generate_storyboard import generate_storyboard
from generate_seedance_prompt import generate_seedance_prompt


def fetch_google_doc(url: str) -> str:
    import re
    m = re.search(r"/document/d/([a-zA-Z0-9_-]+)", url)
    if m:
        export_url = f"https://docs.google.com/document/d/{m.group(1)}/export?format=txt"
    else:
        export_url = url
    req = urllib.request.Request(export_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def run(
    doc_url: str = "",
    doc_text: str = "",
    tag: str = "",
    video_path: str = "",
    num_videos: int = 3,
    theme: str = "",
    style: str = "cinematic / photorealistic",
    driver_logic: str = "形态驱动",
    output_dir: str = "pipeline_output",
):
    os.makedirs(output_dir, exist_ok=True)
    print("=" * 60)
    print("  Doc2Video Pipeline")
    print("=" * 60)

    # ── Step 1: Parse document ──
    if doc_url:
        print(f"\n[Step 1] Fetching document...")
        doc_text = fetch_google_doc(doc_url)
        print(f"  Document: {len(doc_text)} chars")

    # ── Step 2: Fetch visual references ──
    print(f"\n[Step 2] Fetching visual references...")
    video_paths = []

    if video_path:
        print(f"  Using provided video: {video_path}")
        video_paths = [video_path]
    elif doc_text:
        refs = fetch_references(doc_text, num=num_videos, output_dir=os.path.join(output_dir, "refs"))
        video_paths = refs["downloaded"]
        print(f"  Strategy: {refs['product_type']} ({refs['confidence']:.0%})")
        print(f"  Downloaded: {len(video_paths)} videos")
    elif tag:
        video_paths = fetch_instagram(tag, num=num_videos, output_dir=os.path.join(output_dir, "refs"))
        print(f"  Tag #{tag}: {len(video_paths)} videos")
    else:
        print("  No source provided. Skipping.")

    # ── Step 3: Extract frames ──
    print(f"\n[Step 3] Extracting frames...")
    all_frames = []
    for i, vp in enumerate(video_paths):
        frames_dir = os.path.join(output_dir, "frames", f"vid_{i}")
        frames = extract_frames(vp, num_frames=9, save_dir=frames_dir)
        all_frames.append({"video": vp, "frames": frames})
        print(f"  Video {i}: {len(frames)} frames -> {frames_dir}")

    # ── Step 4: Analyze frames (stub — use Cursor Vision for real analysis) ──
    print(f"\n[Step 4] Analyzing frames...")
    structures = []
    for item in all_frames:
        structure = analyze_frames(item["frames"])
        structures.append(structure)
    print(f"  {len(structures)} structures generated (stub — use Vision for real data)")
    print(f"  Frame paths saved for Vision analysis:")
    for i, item in enumerate(all_frames):
        for fp in item["frames"][:3]:
            print(f"    V{i}: {fp}")

    # ── Step 5: Generate main visual ──
    print(f"\n[Step 5] Generating main visual prompt...")
    best_structure = structures[0] if structures else {"subject": theme}
    main_visual, mv_validation = generate_main_visual(best_structure, theme, style)
    print(f"  EN: {main_visual['en'][:120]}...")

    # ── Step 6: Generate storyboard ──
    print(f"\n[Step 6] Generating storyboard prompt...")
    storyboard, sb_validation = generate_storyboard(main_visual, driver_logic)
    print(f"  CN: {len(storyboard['cn'])} chars")
    print(f"  EN: {len(storyboard['en'])} chars")

    # ── Step 7: Await human confirmation ──
    print(f"\n[Step 7] ⏸ Storyboard ready for human confirmation.")
    print(f"  Review the storyboard prompt and frame images above.")
    print(f"  After Vision analysis, generate final Seedance prompt.")

    # ── Step 8: Generate Seedance prompt ──
    print(f"\n[Step 8] Generating Seedance 2.0 prompt...")
    seedance, sd_validation = generate_seedance_prompt(storyboard, driver_logic)
    print(f"  Prompt: {len(seedance)} chars")

    # ── Save output ──
    output = {
        "doc_url": doc_url,
        "theme": theme,
        "style": style,
        "driver_logic": driver_logic,
        "video_paths": video_paths,
        "frame_paths": [item["frames"] for item in all_frames],
        "visual_structures": structures,
        "main_visual": main_visual,
        "main_visual_validation": mv_validation,
        "storyboard": storyboard,
        "storyboard_validation": sb_validation,
        "seedance_prompt": seedance,
        "seedance_validation": sd_validation,
    }

    output_path = os.path.join(output_dir, "output.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n[Done] All output saved to {output_path}")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Doc2Video Pipeline")
    parser.add_argument("--doc-url", help="Google Doc URL")
    parser.add_argument("--doc-text", help="Document text directly")
    parser.add_argument("--tag", help="Instagram tag (skip auto-detect)")
    parser.add_argument("--video", help="Local video file (skip fetch)")
    parser.add_argument("--num", type=int, default=3)
    parser.add_argument("--theme", default="")
    parser.add_argument("--style", default="cinematic / photorealistic")
    parser.add_argument("--driver", default="形态驱动")
    parser.add_argument("--output", default="pipeline_output")
    args = parser.parse_args()

    run(
        doc_url=args.doc_url or "",
        doc_text=args.doc_text or "",
        tag=args.tag or "",
        video_path=args.video or "",
        num_videos=args.num,
        theme=args.theme,
        style=args.style,
        driver_logic=args.driver,
        output_dir=args.output,
    )
