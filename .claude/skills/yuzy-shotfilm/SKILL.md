---
name: "Doc2Video Theme Extractor"
description: "解析文档 → 按产品类型自动选择视觉来源 → Playwright 抓取视频 → OpenCV 抽帧 → Vision 帧分析 → 主视觉 prompt → 九宫格连续叙事 → Seedance 2.0 极简 prompt。中英双语。"
---

# Doc2Video Skill

## 流程

```
文档 URL
  │ WebFetch → export?format=txt
  ▼
[Step 1] 提取功能点
  │
  ▼
[Step 2] detect_product_type(doc_text)
  │ 根据关键词判断产品类型:
  │ ai_video_generation / ai_portrait_headshot / ai_image_generation
  │ ai_background_removal / ai_avatar / ai_audio_music
  │ → 自动选择最佳视觉来源（品牌官网优先，Instagram 标签补充）
  ▼
[Step 3] Playwright headless 抓取视频
  │ 品牌官网: Higgsfield / Aragon / Secta / Dreamwave / etc.
  │ Instagram: #seedance / #aibeauty / #aiportrait / etc.
  │ → 下载 .mp4 到 visual_refs/
  ▼
[Step 4] OpenCV 抽帧 → 9 帧/视频
  ▼
[Step 5] Vision 帧分析 → 视觉结构 JSON
  │ Cursor agent 用 Read 工具查看 .jpg 帧
  │ 输出: subject, transformation, camera_path, lighting, style
  ▼
[Step 6] generate_main_visual() → 中英双语 prompt
  ▼
[Step 7] generate_storyboard() → 九宫格连续叙事 prompt
  ▼
[Step 8] ⏸ 人工确认风格
  ▼
[Step 9] generate_seedance_prompt() → Seedance 2.0 极简 prompt
  │ Popcorn 长 prompt (图片) + Seedance 短 prompt (视频)
  ▼
Production-Ready Output
```

## 输入

| 输入 | 类型 | 描述 |
|------|------|------|
| 文档 URL | Google Doc URL | 待解析的产品页内容 |
| 视频文件 | .mp4 | 可选：用户直接提供视频，跳过抓取 |
| 风格 | str | 可选：视频整体风格 |
| 驱动逻辑 | str | 空间 / 动作 / 动能 / 形态 / 意识 |

## 输出

| 输出 | 类型 | 描述 |
|------|------|------|
| 视觉结构 | JSON | 帧分析: subject, camera, lighting, style |
| 主视觉 prompt | {cn, en} | 中英双语主视觉描述 |
| 九宫格 prompt | {cn, en} | 连续叙事，16:9 分镜图用 |
| Seedance prompt | str | 极简格式 (camera + subject + action) |
| 校验报告 | JSON | 长度/时序/镜头/冲突检查 |

## 脚本

| 文件 | 功能 |
|------|------|
| `run_pipeline.py` | 全流程编排，CLI 入口 |
| `fetch_visual_references.py` | 统一抓取：品牌官网 + Instagram（Playwright） |
| `extract_frames.py` | OpenCV 抽帧 |
| `analyze_frames.py` | 帧分析结构 + Vision 辅助接口 |
| `generate_main_visual.py` | 视觉结构 → 主视觉 prompt |
| `generate_storyboard.py` | 主视觉 → 九宫格连续叙事 |
| `generate_seedance_prompt.py` | 九宫格 → Seedance 2.0 prompt |
| `validate_prompt.py` | prompt 校验（长度/时序/镜头/冲突） |

## 允许的视频来源（仅限 3 个平台）

所有视频素材只能从以下 3 个平台抓取，其他来源会被自动拒绝：

| # | 平台 | 域名 | 用途 |
|---|------|------|------|
| 1 | **Instagram** | instagram.com | 标签页热门视频（Playwright headless） |
| 2 | **Higgsfield** | higgsfield.ai | Seedance 2.0 showcase、社区精选、Popcorn、Recast |
| 3 | **Freepik** | freepik.com | AI 图像/视频/音频生成器产品页 |

## 动态搜索策略（限定在 3 个平台内）

| 产品类型 | 来源 |
|---------|------|
| ai_video_generation | Higgsfield Seedance 2.0 → Higgsfield Community → Freepik AI Video → #seedance → #aicinematic |
| ai_portrait_headshot | Higgsfield Popcorn → Higgsfield Recast → Freepik AI Portrait → #aibeauty → #aiportrait |
| ai_image_generation | Higgsfield Popcorn → Freepik AI Image → #aiart → #midjourney |
| ai_background_removal | Freepik BG Remover → Higgsfield Recast → #backgroundremover |
| ai_avatar | Higgsfield Influencer Studio → Freepik AI Avatar → #aiavatar |
| ai_audio_music | Higgsfield Audio → Freepik AI Audio → #aimusic |

## 安装

```bash
pip install playwright opencv-python-headless
python -m playwright install chromium
```

## CLI 示例

```bash
# 从文档 URL 自动跑全流程
python Scripts/run_pipeline.py \
  --doc-url "https://docs.google.com/document/d/xxx/edit" \
  --num 3 --theme "AI Headshot" --driver "形态驱动"

# 直接抓取指定 Instagram 标签
python Scripts/fetch_visual_references.py --tag seedance --num 5

# 直接抓取指定网站
python Scripts/fetch_visual_references.py --url https://www.aragon.ai --num 3

# 使用本地视频跳过抓取
python Scripts/run_pipeline.py --video path/to/video.mp4 --theme "my theme"
```

## Seedance 2.0 Prompt 规范

1. **Seedance prompt 极简** — 仅 camera + subject + action
2. **复杂描述放 Popcorn** — 图片阶段锁定构图/色调/材质
3. **@Reference 系统** — 最多 9 图 + 3 视频 + 3 音频
4. **风格锚点** — "35mm film, shallow DOF, Roger Deakins"
