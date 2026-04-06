"""
Doc2Video Theme Extractor - Document Parser & Trend Integrator

解析 Google Doc 文档并整合 Instagram 趋势数据，输出结构化的视频主题生成素材。

Instagram 标签页需通过 Cursor 的 WebFetch 工具抓取（JS 渲染页面），
抓取结果保存为 JSON 后传入本脚本进行整合分析。

Usage:
  # 仅解析文档
  python run_skill.py <google_doc_url>

  # 解析文档 + 整合已抓取的趋势数据
  python run_skill.py <google_doc_url> --trends trend_data.json

  # 解析文档 + 指定风格
  python run_skill.py <google_doc_url> --style "赛博朋克"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


GOOGLE_DOC_EXPORT = "https://docs.google.com/document/d/{doc_id}/export?format=txt"

INSTAGRAM_TAG_URLS = {
    "aivideo": "https://www.instagram.com/explore/tags/aivideo/",
    "aicinematic": "https://www.instagram.com/explore/tags/aicinematic/",
    "aifilmmaking": "https://www.instagram.com/explore/tags/aifilmmaking/",
    "aiart": "https://www.instagram.com/explore/tags/aiart/",
}


@dataclass
class DocFeature:
    name: str
    description: str


@dataclass
class DocAnalysis:
    title: str
    meta_description: str
    features: List[DocFeature]
    bullet_points: List[str]
    use_cases: List[str]
    word_count: int


@dataclass
class VideoTheme:
    title_cn: str
    title_en: str
    visual_description: str
    character_style: str
    keywords: List[str]
    mapped_feature: str
    trend_source: str


def fetch_url(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_doc_id(url: str) -> str:
    m = re.search(r"/document/d/([a-zA-Z0-9_-]+)", url)
    if not m:
        raise ValueError(f"Cannot extract doc ID from: {url}")
    return m.group(1)


def fetch_google_doc(url: str) -> str:
    doc_id = extract_doc_id(url)
    export_url = GOOGLE_DOC_EXPORT.format(doc_id=doc_id)
    print(f"  Fetching: {export_url}")
    return fetch_url(export_url)


def analyze_document(text: str) -> DocAnalysis:
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    title = ""
    meta_desc = ""
    for i, line in enumerate(lines):
        if "meta title" in line.lower() and i + 1 < len(lines):
            title = lines[i + 1] if i + 1 < len(lines) else ""
        if "meta description" in line.lower() and i + 1 < len(lines):
            meta_desc = lines[i + 1] if i + 1 < len(lines) else ""

    if not title:
        for line in lines[:10]:
            if len(line) > 10 and not line.lower().startswith("meta"):
                title = line
                break

    features = []
    bullet_points = []
    for line in lines:
        if line.startswith("* ") or line.startswith("- "):
            content = line.lstrip("*- ").strip()
            if ":" in content:
                name, desc = content.split(":", 1)
                features.append(DocFeature(name=name.strip(), description=desc.strip()))
            bullet_points.append(content)

    use_cases = []
    in_use_case = False
    for line in lines:
        if any(kw in line.lower() for kw in ["use case", "how to use", "best results"]):
            in_use_case = True
            continue
        if in_use_case and (line.startswith(("1.", "2.", "3.", "4.", "5."))):
            use_cases.append(line.lstrip("0123456789. "))
        if in_use_case and line.startswith("#"):
            in_use_case = False

    return DocAnalysis(
        title=title,
        meta_description=meta_desc,
        features=features,
        bullet_points=bullet_points,
        use_cases=use_cases,
        word_count=len(text.split()),
    )


def load_trend_data(path: str) -> Optional[Dict]:
    p = Path(path)
    if not p.exists():
        print(f"  Trend file not found: {path}")
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_output(
    doc: DocAnalysis,
    trends: Optional[Dict] = None,
    style: Optional[str] = None,
) -> Dict:
    output = {
        "document_analysis": {
            "title": doc.title,
            "meta_description": doc.meta_description,
            "features": [asdict(f) for f in doc.features],
            "bullet_points": doc.bullet_points,
            "use_cases": doc.use_cases,
            "word_count": doc.word_count,
        },
        "target_style": style,
        "instagram_tag_urls": INSTAGRAM_TAG_URLS,
        "trends": trends,
        "instructions_for_claude": (
            "Use the document_analysis and trends data above to generate "
            "6 video themes. Each theme should map to one document feature "
            "and incorporate a current trend. Output: title (CN+EN), "
            "visual description (20-50 words), character style, keywords."
        ),
    }
    return output


def main():
    parser = argparse.ArgumentParser(description="Doc2Video Theme Extractor")
    parser.add_argument("url", help="Google Doc URL")
    parser.add_argument("--trends", help="Path to pre-scraped trend data JSON")
    parser.add_argument("--style", help="Target visual style")
    parser.add_argument(
        "--output", default="skill_output.json", help="Output file path"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Doc2Video Theme Extractor")
    print("=" * 60)

    print("\n[Step 1] Fetching & analyzing document...")
    doc_text = fetch_google_doc(args.url)
    doc = analyze_document(doc_text)
    print(f"  Title: {doc.title}")
    print(f"  Features: {len(doc.features)}")
    print(f"  Bullet points: {len(doc.bullet_points)}")
    print(f"  Use cases: {len(doc.use_cases)}")
    print(f"  Word count: {doc.word_count}")

    print("\n[Step 2] Loading trend data...")
    trends = None
    if args.trends:
        trends = load_trend_data(args.trends)
        if trends:
            print(f"  Loaded trends from: {args.trends}")
        else:
            print("  No trend data loaded.")
    else:
        print("  No --trends file provided. Skipping.")
        print("  Tip: Use Cursor's WebFetch to scrape these Instagram tag pages:")
        for tag, url in INSTAGRAM_TAG_URLS.items():
            print(f"    #{tag}: {url}")

    print("\n[Step 3] Generating output...")
    output = generate_output(doc, trends, args.style)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"  Saved to: {args.output}")

    print("\n[Step 4] Summary")
    print("-" * 40)
    print(f"  Document: {doc.title}")
    print(f"  Features extracted: {len(doc.features)}")
    for i, feat in enumerate(doc.features, 1):
        print(f"    {i}. {feat.name}")
    print(f"  Trends loaded: {'Yes' if trends else 'No'}")
    print(f"  Target style: {args.style or 'Auto'}")
    print(f"\n  Next: Feed {args.output} to Claude for theme generation.")

    return output


if __name__ == "__main__":
    main()
