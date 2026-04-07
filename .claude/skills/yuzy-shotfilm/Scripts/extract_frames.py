"""
Extract keyframes from video files using OpenCV.

IMPORTANT: This script only processes videos that were downloaded by
fetch_visual_references.py, which enforces the allowed sources rule:
    1. Instagram (instagram.com)
    2. Higgsfield (higgsfield.ai)
    3. Freepik (freepik.com)

Videos from any other source will be rejected by the fetch stage
before they reach this script.
"""

import cv2
import os


def extract_frames(video_path, num_frames=9, save_dir="frames"):
    os.makedirs(save_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total / fps if fps > 0 else 0

    frames = []
    for i in range(num_frames):
        pos = int(total * i / num_frames)
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ret, frame = cap.read()
        if ret:
            basename = os.path.basename(video_path).rsplit(".", 1)[0]
            frame_path = os.path.join(save_dir, f"{basename}_frame{i}.jpg")
            cv2.imwrite(frame_path, frame)
            frames.append(frame_path)

    cap.release()

    print(f"  Extracted {len(frames)} frames from {os.path.basename(video_path)} "
          f"({total}f {fps:.0f}fps {w}x{h} {duration:.1f}s)")

    return frames


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "video_0.mp4"
    frames = extract_frames(path)
    print("Frames:", frames)
