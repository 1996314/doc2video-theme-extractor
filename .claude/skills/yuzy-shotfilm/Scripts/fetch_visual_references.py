"""
Visual Reference Fetcher — unified entry point for all video/image sources.

Combines:
  1. Dynamic strategy: detect product type → select best sources
  2. Website scraping: Playwright headless fetches .mp4 from brand showcase sites
  3. Instagram tags: Playwright headless fetches videos from explore/tags pages
  4. Instagram CDP: optional logged-in mode for metadata (captions, post links)

Usage:
    # Auto-detect product type from document text
    from fetch_visual_references import fetch_references
    refs = fetch_references(doc_text, num=5)

    # Direct Instagram tag fetch
    from fetch_visual_references import fetch_instagram
    vids = fetch_instagram("seedance", num=3)

    # Direct website fetch
    from fetch_visual_references import fetch_website
    vids = fetch_website("https://www.higgsfield.ai/seedance/2.0", num=3)

    # CLI
    python fetch_visual_references.py --doc "AI headshot generator selfie portrait" --num 5
    python fetch_visual_references.py --tag seedance --num 3
    python fetch_visual_references.py --url https://www.higgsfield.ai/seedance/2.0 --num 3
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from typing import Dict, List, Optional, Tuple


STRATEGY_MAP = {
    "ai_video_generation": {
        "keywords": ["video generat", "text-to-video", "image-to-video", "video model",
                     "motion control", "multi-shot", "video continuation", "temporal"],
        "sources": [
            {"type": "website", "name": "Higgsfield Seedance 2.0", "url": "https://www.higgsfield.ai/seedance/2.0"},
            {"type": "website", "name": "Higgsfield Community", "url": "https://www.higgsfield.ai/seedance-2-community"},
            {"type": "instagram_tag", "tag": "seedance"},
            {"type": "instagram_tag", "tag": "aicinematic"},
        ],
    },
    "ai_portrait_headshot": {
        "keywords": ["headshot", "portrait", "selfie", "profile picture", "face smooth",
                     "skin smooth", "retouching", "blemish", "professional photo"],
        "sources": [
            {"type": "website", "name": "HeadshotPro", "url": "https://www.headshotpro.com"},
            {"type": "website", "name": "Aragon AI", "url": "https://www.aragon.ai"},
            {"type": "website", "name": "Secta AI", "url": "https://secta.ai"},
            {"type": "website", "name": "Dreamwave AI", "url": "https://dreamwave.ai"},
            {"type": "website", "name": "Facetune", "url": "https://facetuneapp.com/features"},
            {"type": "instagram_tag", "tag": "aibeauty"},
            {"type": "instagram_tag", "tag": "aiportrait"},
        ],
    },
    "ai_image_generation": {
        "keywords": ["image generat", "text-to-image", "art generat", "ai art",
                     "illustration", "design", "creative"],
        "sources": [
            {"type": "website", "name": "Midjourney Showcase", "url": "https://www.midjourney.com/showcase"},
            {"type": "website", "name": "Freepik AI", "url": "https://www.freepik.com/ai/image-generator"},
            {"type": "instagram_tag", "tag": "aiart"},
        ],
    },
    "ai_background_removal": {
        "keywords": ["background remov", "background replac", "bg remov", "cutout",
                     "transparent", "background chang"],
        "sources": [
            {"type": "website", "name": "Remove.bg", "url": "https://www.remove.bg"},
            {"type": "website", "name": "Canva BG Remover", "url": "https://www.canva.com/features/background-remover/"},
            {"type": "instagram_tag", "tag": "backgroundremover"},
        ],
    },
    "ai_avatar": {
        "keywords": ["avatar", "character creat", "virtual", "anime", "cartoon",
                     "stylized", "3d character"],
        "sources": [
            {"type": "website", "name": "Higgsfield Influencer", "url": "https://www.higgsfield.ai/blog/AI-Influencer-Studio-Guide-Build-AI-Character"},
            {"type": "instagram_tag", "tag": "aiavatar"},
        ],
    },
    "ai_audio_music": {
        "keywords": ["audio", "music", "voice", "sound", "song", "singing",
                     "text-to-speech", "tts"],
        "sources": [
            {"type": "website", "name": "Suno AI", "url": "https://suno.com"},
            {"type": "website", "name": "ElevenLabs", "url": "https://elevenlabs.io"},
            {"type": "instagram_tag", "tag": "aimusic"},
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


def fetch_website(url: str, num: int = 3, output_dir: str = "visual_refs") -> List[str]:
    from playwright.sync_api import sync_playwright

    os.makedirs(output_dir, exist_ok=True)
    downloaded = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(3000)
            for _ in range(2):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1500)

            video_urls = page.evaluate("""() => {
                const vids = new Set();
                document.querySelectorAll('video, video source').forEach(v => {
                    const s = v.src || v.getAttribute('src') || '';
                    if (s && (s.includes('.mp4') || s.includes('.webm'))) vids.add(s);
                });
                return [...vids];
            }""")

            for i, src in enumerate(video_urls[:num]):
                idx = len(downloaded)
                filepath = os.path.join(output_dir, f"web_{idx}.mp4")
                if _download(src, filepath):
                    downloaded.append(filepath)
                    print(f"    [{idx}] {os.path.getsize(filepath)/1024:.0f}KB -> {filepath}")
        except Exception as e:
            print(f"    Error: {str(e)[:60]}")
        browser.close()

    return downloaded


def fetch_instagram(tag: str, num: int = 3, output_dir: str = "visual_refs") -> List[str]:
    from playwright.sync_api import sync_playwright

    os.makedirs(output_dir, exist_ok=True)
    downloaded = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})
        try:
            page.goto(
                f"https://www.instagram.com/explore/tags/{tag}/",
                wait_until="domcontentloaded", timeout=12000,
            )
            page.wait_for_timeout(3000)
            video_urls = page.evaluate("""() => {
                const vids = [];
                document.querySelectorAll('video').forEach(v => { if(v.src) vids.push(v.src); });
                return vids;
            }""")

            for i, src in enumerate(video_urls[:num]):
                idx = len(downloaded)
                filepath = os.path.join(output_dir, f"ig_{tag}_{idx}.mp4")
                if _download(src, filepath):
                    downloaded.append(filepath)
                    print(f"    [{idx}] {os.path.getsize(filepath)/1024:.0f}KB -> {filepath}")
        except Exception as e:
            print(f"    Error: {str(e)[:60]}")
        browser.close()

    return downloaded


def fetch_instagram_cdp(
    tag: str, cdp_url: str = "http://localhost:9222", caption_count: int = 5,
) -> Dict:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(cdp_url)
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page()
        page.goto(
            f"https://www.instagram.com/explore/tags/{tag}/",
            wait_until="networkidle", timeout=20000,
        )
        page.wait_for_timeout(3000)
        for _ in range(3):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)

        post_links = page.evaluate("""() => {
            const links = [];
            document.querySelectorAll('a').forEach(a => {
                if (a.href && (a.href.includes('/reel/') || a.href.includes('/p/')))
                    links.push(a.href);
            });
            return [...new Set(links)];
        }""")

        captions = []
        for link in post_links[:caption_count]:
            try:
                page.goto(link, wait_until="networkidle", timeout=15000)
                page.wait_for_timeout(2000)
                caption = page.evaluate("""() => {
                    let longest = '';
                    document.querySelectorAll('span').forEach(s => {
                        const t = s.innerText || '';
                        if (t.length > longest.length && t.length > 20) longest = t;
                    });
                    return longest.substring(0, 500);
                }""")
                captions.append({"url": link, "caption": caption})
            except Exception:
                captions.append({"url": link, "caption": ""})
        page.close()

    return {"tag": tag, "post_count": len(post_links), "captions": captions}


def fetch_references(
    doc_text: str, num: int = 5, output_dir: str = "visual_refs",
) -> Dict:
    """Main entry: detect product type → fetch from best sources."""
    os.makedirs(output_dir, exist_ok=True)

    product_type, confidence = detect_product_type(doc_text)
    sources = STRATEGY_MAP[product_type]["sources"]
    print(f"[Strategy] Product: {product_type} ({confidence:.0%})")

    downloaded = []
    source_log = []

    for source in sources:
        if len(downloaded) >= num:
            break
        remaining = num - len(downloaded)
        name = source.get("name", source.get("tag", ""))
        print(f"\n  [{source['type']}] {name}...")

        if source["type"] == "website":
            paths = fetch_website(source["url"], remaining, output_dir)
        elif source["type"] == "instagram_tag":
            paths = fetch_instagram(source["tag"], remaining, output_dir)
        else:
            continue

        for p in paths:
            source_log.append({"source": name, "path": p, "size_kb": round(os.path.getsize(p) / 1024)})
        downloaded.extend(paths)

    return {
        "product_type": product_type,
        "confidence": confidence,
        "sources_tried": [s.get("name", s.get("tag", "")) for s in sources],
        "downloaded": downloaded,
        "source_log": source_log,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch visual references")
    parser.add_argument("--doc", help="Document text for auto-detection")
    parser.add_argument("--tag", help="Instagram tag (direct)")
    parser.add_argument("--url", help="Website URL (direct)")
    parser.add_argument("--num", type=int, default=5)
    parser.add_argument("--output", default="visual_refs")
    args = parser.parse_args()

    if args.doc:
        result = fetch_references(args.doc, args.num, args.output)
        print(f"\nProduct: {result['product_type']}, Downloaded: {len(result['downloaded'])}")
    elif args.tag:
        paths = fetch_instagram(args.tag, args.num, args.output)
        print(f"\nDownloaded: {len(paths)} from #{args.tag}")
    elif args.url:
        paths = fetch_website(args.url, args.num, args.output)
        print(f"\nDownloaded: {len(paths)} from {args.url}")
    else:
        parser.print_help()
