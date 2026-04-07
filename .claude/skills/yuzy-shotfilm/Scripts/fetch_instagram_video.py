"""
Instagram Video Fetcher — Playwright Headless (No Login Required)

从 Instagram 标签探索页抓取热门视频，无需登录。
使用 Playwright headless Chromium 渲染 JS 页面，直接获取视频 CDN 链接。

Usage:
    python fetch_instagram_video.py seedance --num 3 --output ig_videos
"""

from __future__ import annotations

import argparse
import os
import urllib.request
from typing import List, Dict


def fetch_tag_videos(
    tag: str,
    num_videos: int = 3,
    output_dir: str = "ig_videos",
    timeout: int = 15000,
) -> List[Dict[str, str]]:
    from playwright.sync_api import sync_playwright

    os.makedirs(output_dir, exist_ok=True)
    results: List[Dict[str, str]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})

        url = f"https://www.instagram.com/explore/tags/{tag}/"
        page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        page.wait_for_timeout(3000)

        data = page.evaluate(
            """() => {
            const reels = [];
            document.querySelectorAll('a[href*="/reel/"], a[href*="/p/"]').forEach(a => {
                if (a.href) reels.push(a.href);
            });
            const videos = [];
            document.querySelectorAll('video').forEach(v => {
                videos.push({src: v.src || '', poster: v.poster || ''});
            });
            return {reels: [...new Set(reels)], videos};
        }"""
        )

        reel_links = data.get("reels", [])
        video_elements = data.get("videos", [])

        for i, vid in enumerate(video_elements[:num_videos]):
            src = vid.get("src", "")
            if not src:
                continue

            filename = f"{tag}_{i}.mp4"
            filepath = os.path.join(output_dir, filename)
            reel_url = reel_links[i] if i < len(reel_links) else ""

            try:
                req = urllib.request.Request(
                    src,
                    headers={
                        "User-Agent": "Mozilla/5.0",
                        "Referer": "https://www.instagram.com/",
                    },
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    with open(filepath, "wb") as f:
                        f.write(resp.read())

                size_kb = os.path.getsize(filepath) / 1024
                results.append(
                    {
                        "index": i,
                        "path": filepath,
                        "size_kb": round(size_kb),
                        "reel_url": reel_url,
                        "cdn_url": src[:80] + "...",
                    }
                )
                print(f"  [{i}] {size_kb:.0f}KB -> {filepath}")
            except Exception as e:
                print(f"  [{i}] Download failed: {e}")

        browser.close()

    return results


def fetch_tag_metadata(tag: str, timeout: int = 15000) -> Dict:
    """Fetch tag page metadata without downloading videos."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})

        url = f"https://www.instagram.com/explore/tags/{tag}/"
        page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        page.wait_for_timeout(3000)

        data = page.evaluate(
            """() => {
            const reels = [];
            document.querySelectorAll('a[href*="/reel/"], a[href*="/p/"]').forEach(a => {
                if (a.href) reels.push(a.href);
            });
            const videoCount = document.querySelectorAll('video').length;
            const title = document.title || '';
            return {reels: [...new Set(reels)], videoCount, title};
        }"""
        )

        browser.close()

    return {
        "tag": tag,
        "title": data.get("title", ""),
        "reel_count": len(data.get("reels", [])),
        "video_count": data.get("videoCount", 0),
        "reel_urls": data.get("reels", []),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Instagram videos by tag")
    parser.add_argument("tag", help="Instagram tag to search")
    parser.add_argument("--num", type=int, default=3, help="Number of videos")
    parser.add_argument("--output", default="ig_videos", help="Output directory")
    parser.add_argument("--metadata-only", action="store_true", help="Only fetch metadata")
    args = parser.parse_args()

    if args.metadata_only:
        meta = fetch_tag_metadata(args.tag)
        print(f"Tag: #{meta['tag']}")
        print(f"Title: {meta['title']}")
        print(f"Videos found: {meta['video_count']}")
        print(f"Reel links: {meta['reel_count']}")
        for url in meta["reel_urls"][:5]:
            print(f"  {url}")
    else:
        print(f"Fetching top {args.num} videos from #{args.tag}...")
        results = fetch_tag_videos(args.tag, args.num, args.output)
        print(f"\nDownloaded {len(results)} videos to {args.output}/")
