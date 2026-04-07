"""
Visual Reference Fetcher — Dynamic Strategy by Product Type

根据文档内容自动选择搜索策略：
  - 分析文档关键词 → 判断产品类型
  - 根据产品类型 → 选择最佳视觉来源（品牌官网 > Instagram 品牌账号 > 标签页）
  - 下载视频/图片 → 返回本地路径列表

Usage:
    from fetch_visual_references import fetch_references
    refs = fetch_references(doc_text, num=5, output_dir="refs")
"""

from __future__ import annotations

import os
import re
import urllib.request
from typing import Dict, List, Optional, Tuple


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 产品类型 → 搜索策略映射
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STRATEGY_MAP = {
    "ai_video_generation": {
        "keywords": ["video generat", "text-to-video", "image-to-video", "video model",
                     "motion control", "multi-shot", "video continuation", "temporal"],
        "sources": [
            {"type": "website", "name": "Higgsfield Seedance 2.0", "url": "https://www.higgsfield.ai/seedance/2.0"},
            {"type": "website", "name": "Higgsfield Community", "url": "https://www.higgsfield.ai/seedance-2-community"},
            {"type": "website", "name": "Runway Gen-4", "url": "https://runwayml.com/research/gen-4"},
            {"type": "instagram_tag", "name": "#seedance", "tag": "seedance"},
            {"type": "instagram_tag", "name": "#aicinematic", "tag": "aicinematic"},
        ],
    },
    "ai_portrait_headshot": {
        "keywords": ["headshot", "portrait", "selfie", "profile picture", "face smooth",
                     "skin smooth", "retouching", "blemish", "professional photo"],
        "sources": [
            {"type": "website", "name": "Facetune Features", "url": "https://facetuneapp.com/features"},
            {"type": "website", "name": "AirBrush AI", "url": "https://appairbrush.com"},
            {"type": "website", "name": "Freepik AI Portrait", "url": "https://www.freepik.com/ai/image-generator"},
            {"type": "instagram_tag", "name": "#aibeauty", "tag": "aibeauty"},
            {"type": "instagram_tag", "name": "#aiportrait", "tag": "aiportrait"},
            {"type": "instagram_tag", "name": "#glassskin", "tag": "glassskin"},
        ],
    },
    "ai_image_generation": {
        "keywords": ["image generat", "text-to-image", "art generat", "ai art",
                     "illustration", "design", "creative"],
        "sources": [
            {"type": "website", "name": "Midjourney Showcase", "url": "https://www.midjourney.com/showcase"},
            {"type": "website", "name": "Freepik AI", "url": "https://www.freepik.com/ai/image-generator"},
            {"type": "instagram_tag", "name": "#aiart", "tag": "aiart"},
            {"type": "instagram_tag", "name": "#midjourney", "tag": "midjourney"},
        ],
    },
    "ai_background_removal": {
        "keywords": ["background remov", "background replac", "bg remov", "cutout",
                     "transparent", "background chang"],
        "sources": [
            {"type": "website", "name": "Remove.bg", "url": "https://www.remove.bg"},
            {"type": "website", "name": "Canva BG Remover", "url": "https://www.canva.com/features/background-remover/"},
            {"type": "instagram_tag", "name": "#backgroundremover", "tag": "backgroundremover"},
        ],
    },
    "ai_avatar": {
        "keywords": ["avatar", "character creat", "virtual", "anime", "cartoon",
                     "stylized", "3d character"],
        "sources": [
            {"type": "website", "name": "Higgsfield AI Influencer", "url": "https://www.higgsfield.ai/blog/AI-Influencer-Studio-Guide-Build-AI-Character"},
            {"type": "instagram_tag", "name": "#aiavatar", "tag": "aiavatar"},
            {"type": "instagram_tag", "name": "#aicharacter", "tag": "aicharacter"},
        ],
    },
    "ai_audio_music": {
        "keywords": ["audio", "music", "voice", "sound", "song", "singing",
                     "text-to-speech", "tts"],
        "sources": [
            {"type": "website", "name": "Suno AI", "url": "https://suno.com"},
            {"type": "website", "name": "ElevenLabs", "url": "https://elevenlabs.io"},
            {"type": "instagram_tag", "name": "#aimusic", "tag": "aimusic"},
        ],
    },
}


def detect_product_type(doc_text: str) -> Tuple[str, float]:
    text_lower = doc_text.lower()
    scores = {}
    for ptype, config in STRATEGY_MAP.items():
        score = sum(1 for kw in config["keywords"] if kw in text_lower)
        scores[ptype] = score

    best = max(scores, key=scores.get)
    confidence = scores[best] / max(len(STRATEGY_MAP[best]["keywords"]), 1)
    return best, confidence


def get_sources_for_doc(doc_text: str) -> Tuple[str, List[Dict]]:
    product_type, confidence = detect_product_type(doc_text)
    sources = STRATEGY_MAP[product_type]["sources"]
    return product_type, sources


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 从网站抓取视频
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _fetch_website_videos(url: str, num: int = 3) -> List[str]:
    from playwright.sync_api import sync_playwright

    video_urls = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(3000)
            for _ in range(2):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1500)

            video_urls = page.evaluate(
                """() => {
                const vids = new Set();
                document.querySelectorAll('video, video source').forEach(v => {
                    const src = v.src || v.getAttribute('src') || '';
                    if (src && src.includes('.mp4')) vids.add(src);
                });
                return [...vids];
            }"""
            )
        except Exception:
            pass
        browser.close()

    return video_urls[:num]


def _fetch_instagram_tag_videos(tag: str, num: int = 3) -> List[str]:
    from playwright.sync_api import sync_playwright

    video_urls = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})
        try:
            page.goto(
                f"https://www.instagram.com/explore/tags/{tag}/",
                wait_until="domcontentloaded",
                timeout=12000,
            )
            page.wait_for_timeout(3000)
            video_urls = page.evaluate(
                """() => {
                const vids = [];
                document.querySelectorAll('video').forEach(v => {
                    if (v.src) vids.push(v.src);
                });
                return vids;
            }"""
            )
        except Exception:
            pass
        browser.close()

    return video_urls[:num]


def _download(url: str, filepath: str) -> bool:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        if "instagram" in url:
            headers["Referer"] = "https://www.instagram.com/"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(filepath, "wb") as f:
                f.write(resp.read())
        return True
    except Exception:
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 主入口
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def fetch_references(
    doc_text: str,
    num: int = 5,
    output_dir: str = "visual_refs",
) -> Dict:
    os.makedirs(output_dir, exist_ok=True)

    product_type, sources = get_sources_for_doc(doc_text)
    print(f"[Strategy] Product type: {product_type}")
    print(f"[Strategy] Sources: {len(sources)}")

    downloaded = []
    source_log = []

    for source in sources:
        if len(downloaded) >= num:
            break

        remaining = num - len(downloaded)
        print(f"\n  Fetching from: {source['name']} ({source['type']})...")

        if source["type"] == "website":
            urls = _fetch_website_videos(source["url"], remaining)
        elif source["type"] == "instagram_tag":
            urls = _fetch_instagram_tag_videos(source["tag"], remaining)
        else:
            continue

        print(f"    Found {len(urls)} video URLs")

        for i, url in enumerate(urls):
            idx = len(downloaded)
            filepath = os.path.join(output_dir, f"ref_{idx}.mp4")
            if _download(url, filepath):
                size_kb = os.path.getsize(filepath) / 1024
                downloaded.append(filepath)
                source_log.append({"source": source["name"], "path": filepath, "size_kb": round(size_kb)})
                print(f"    [{idx}] {size_kb:.0f}KB -> {filepath}")

    return {
        "product_type": product_type,
        "sources_tried": [s["name"] for s in sources],
        "downloaded": downloaded,
        "source_log": source_log,
    }


if __name__ == "__main__":
    import sys

    doc_text = sys.argv[1] if len(sys.argv) > 1 else input("Paste document text: ")
    result = fetch_references(doc_text, num=5)
    print(f"\nProduct type: {result['product_type']}")
    print(f"Downloaded: {len(result['downloaded'])} videos")
    for item in result["source_log"]:
        print(f"  {item['source']}: {item['path']} ({item['size_kb']}KB)")
