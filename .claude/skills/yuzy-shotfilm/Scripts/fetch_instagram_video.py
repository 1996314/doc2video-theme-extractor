"""
Instagram Video Fetcher — CDP + Headless Hybrid

最优方案：
  1. CDP（登录态）获取帖子链接 + 文案/评论（24+ 帖子）
  2. Headless（无登录）下载完整 MP4 视频文件（12 个）

CDP 启动方式（需先关闭所有 Chrome 窗口）：
    /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\
        --remote-debugging-port=9222 \\
        --user-data-dir="/tmp/chrome_cdp_data" \\
        --no-first-run

Usage:
    # 完整流程：CDP 元数据 + Headless 视频
    python fetch_instagram_video.py seedance --num 5

    # 仅 Headless（无需 Chrome）
    python fetch_instagram_video.py seedance --num 3 --headless-only

    # 仅 CDP 元数据（不下载视频）
    python fetch_instagram_video.py seedance --cdp-only
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional


def _download_video(src: str, filepath: str) -> int:
    req = urllib.request.Request(
        src,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.instagram.com/",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
        with open(filepath, "wb") as f:
            f.write(data)
    return len(data)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CDP: 登录态获取帖子链接 + 文案
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def fetch_cdp_metadata(
    tag: str,
    cdp_url: str = "http://localhost:9222",
    scroll_count: int = 3,
    caption_count: int = 5,
) -> Dict:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(cdp_url)
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page()

        page.goto(
            f"https://www.instagram.com/explore/tags/{tag}/",
            wait_until="networkidle",
            timeout=20000,
        )
        page.wait_for_timeout(3000)

        for i in range(scroll_count):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)

        post_links = page.evaluate(
            """() => {
            const links = [];
            document.querySelectorAll('a').forEach(a => {
                if (a.href && (a.href.includes('/reel/') || a.href.includes('/p/')))
                    links.push(a.href);
            });
            return [...new Set(links)];
        }"""
        )

        captions = []
        for i, link in enumerate(post_links[:caption_count]):
            try:
                page.goto(link, wait_until="networkidle", timeout=15000)
                page.wait_for_timeout(2000)
                caption = page.evaluate(
                    """() => {
                    const spans = document.querySelectorAll('span');
                    let longest = '';
                    spans.forEach(s => {
                        const t = s.innerText || '';
                        if (t.length > longest.length && t.length > 20) longest = t;
                    });
                    return longest.substring(0, 500);
                }"""
                )
                captions.append({"url": link, "caption": caption})
            except Exception:
                captions.append({"url": link, "caption": ""})

        page.close()

    return {"tag": tag, "post_links": post_links, "captions": captions}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Headless: 无登录下载完整 MP4
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def fetch_headless_videos(
    tag: str,
    num_videos: int = 5,
    output_dir: str = "ig_videos",
) -> List[Dict]:
    from playwright.sync_api import sync_playwright

    os.makedirs(output_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})
        page.goto(
            f"https://www.instagram.com/explore/tags/{tag}/",
            wait_until="domcontentloaded",
            timeout=15000,
        )
        page.wait_for_timeout(3000)

        video_srcs = page.evaluate(
            """() => {
            const vids = [];
            document.querySelectorAll('video').forEach(v => {
                if (v.src) vids.push(v.src);
            });
            return vids;
        }"""
        )

        results = []
        for i, src in enumerate(video_srcs[:num_videos]):
            filepath = os.path.join(output_dir, f"{tag}_{i}.mp4")
            try:
                size = _download_video(src, filepath)
                results.append({"index": i, "path": filepath, "size_kb": round(size / 1024)})
                print(f"  [{i}] {size / 1024:.0f}KB -> {filepath}")
            except Exception as e:
                print(f"  [{i}] Failed: {e}")

        browser.close()

    return results


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 组合流程
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def fetch_hybrid(
    tag: str,
    num_videos: int = 5,
    output_dir: str = "ig_videos",
    cdp_url: str = "http://localhost:9222",
    scroll_count: int = 3,
    caption_count: int = 5,
) -> Dict:
    """
    Step 1: CDP 获取帖子链接 + 文案（需要已启动带 debug 端口的 Chrome）
    Step 2: 关闭 CDP 连接
    Step 3: Headless 下载完整视频
    """
    metadata = None
    try:
        print(f"[CDP] Fetching metadata for #{tag}...")
        metadata = fetch_cdp_metadata(tag, cdp_url, scroll_count, caption_count)
        print(f"[CDP] {len(metadata['post_links'])} posts, {len(metadata['captions'])} captions")
    except Exception as e:
        print(f"[CDP] Not available ({e}), using headless only")

    print(f"\n[Headless] Downloading {num_videos} videos for #{tag}...")
    videos = fetch_headless_videos(tag, num_videos, output_dir)
    print(f"[Headless] {len(videos)} videos downloaded")

    result = {
        "tag": tag,
        "metadata": metadata,
        "videos": videos,
    }

    output_json = os.path.join(output_dir, f"{tag}_data.json")
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n[Saved] {output_json}")

    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CLI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Instagram videos (hybrid)")
    parser.add_argument("tag", help="Instagram tag")
    parser.add_argument("--num", type=int, default=5, help="Number of videos to download")
    parser.add_argument("--output", default="ig_videos", help="Output directory")
    parser.add_argument("--cdp-url", default="http://localhost:9222")
    parser.add_argument("--scroll", type=int, default=3)
    parser.add_argument("--captions", type=int, default=5, help="Number of captions to fetch")
    parser.add_argument("--headless-only", action="store_true", help="Skip CDP, headless only")
    parser.add_argument("--cdp-only", action="store_true", help="Only fetch CDP metadata")
    args = parser.parse_args()

    if args.headless_only:
        videos = fetch_headless_videos(args.tag, args.num, args.output)
        print(f"Done. {len(videos)} videos.")
    elif args.cdp_only:
        meta = fetch_cdp_metadata(args.tag, args.cdp_url, args.scroll, args.captions)
        print(json.dumps(meta, ensure_ascii=False, indent=2))
    else:
        fetch_hybrid(
            args.tag, args.num, args.output,
            args.cdp_url, args.scroll, args.captions,
        )
