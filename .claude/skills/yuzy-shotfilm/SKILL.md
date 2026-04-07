---
name: "Doc2Video Theme Extractor"
description: "解析文档生成视频主题 → Playwright 抓取 Instagram 热门视频 → OpenCV 抽帧 → Vision 帧分析 → 主视觉 prompt → 九宫格连续描述 → Seedance 2.0 连续视频 prompt。全链路自动化，中英双语输出。"
---

# Doc2Video Skill（视觉驱动扩展版）

## 功能
1. 文档解析：提取主题、功能点、核心卖点
2. **Playwright 视频抓取**：Headless Chromium 访问 Instagram 标签页，无需登录直接获取视频 CDN 链接并下载
3. **OpenCV 抽帧**：每个视频提取 9 个关键帧
4. **Vision 帧分析**：用 AI Vision 分析帧内容，输出视觉结构（主体、镜头、光线、风格）
5. 主视觉 prompt：融合帧分析结果，输出中英双语 prompt
6. 九宫格连续文本 prompt：16:9 一张图，9 panel 连续叙事
7. Seedance 2.0 连续视频 prompt：极简格式（camera + subject + action），按 Higgsfield 官方规范
8. 校验：自动使用 `validate_prompt` 校验生成 prompt

## 完整链路

```
文档 URL
  │ WebFetch (export?format=txt)
  ▼
提取功能点
  │
  ▼
Playwright headless Chromium ──→ Instagram 标签页（无需登录）
  │ 获取视频 CDN 链接（12个/页）
  │ urllib 下载 .mp4
  ▼
OpenCV 抽帧 ──→ 9 帧/视频
  │
  ▼
Claude Vision 帧分析 ──→ 视觉结构 JSON
  │ (主体、镜头路径、光线、风格、叙事弧线)
  ▼
generate_main_visual() ──→ 中英双语 prompt
  ▼
generate_storyboard() ──→ 九宫格连续叙事 prompt
  ▼
人工确认风格 ✅
  ▼
generate_seedance_prompt() ──→ Seedance 2.0 极简 prompt
  │ Popcorn 长 prompt (图片) + Seedance 短 prompt (视频)
  │ @Image / @Video / @Audio 引用
  ▼
Production-Ready Output
```

## 输入
| 输入 | 类型 | 描述 |
|------|------|------|
| 文档 URL / 文件 | Google Doc / Word | 待解析主题 |
| 风格 | str | 视频整体风格 |
| 关键词 / 标签 | list | 用于 Instagram 抓取的标签（如 seedance, higgsfield） |
| 驱动逻辑 | str | 空间 / 动作 / 动能 / 形态 / 意识 |
| 视频文件 | .mp4 | 可选：用户直接提供视频跳过抓取步骤 |

## 输出
| 输出 | 类型 | 描述 |
|------|------|------|
| 视觉结构 | JSON | 帧分析结果：主体、镜头、光线、风格、叙事 |
| 主视觉 prompt | dict | {"cn": ..., "en": ...} |
| 九宫格 prompt | dict | {"cn": ..., "en": ...} — 一条连续叙事 |
| Seedance prompt | str | 极简格式：Popcorn 长 prompt + Seedance 短 prompt |
| 校验报告 | dict | 各阶段校验结果 |

## 脚本说明

| 脚本 | 功能 | 依赖 |
|------|------|------|
| `fetch_instagram_video.py` | Playwright headless 抓取 Instagram 视频 | playwright, chromium |
| `extract_frames.py` | OpenCV 抽取关键帧 | opencv-python-headless |
| `analyze_frames.py` | AI Vision 帧分析 → 视觉结构 | Claude Vision / OpenAI Vision |
| `generate_main_visual.py` | 帧分析 → 主视觉 prompt | validate_prompt |
| `generate_storyboard.py` | 主视觉 → 九宫格连续叙事 | validate_prompt |
| `generate_seedance_prompt.py` | 九宫格 → Seedance 2.0 连续 prompt | validate_prompt |
| `run_pipeline.py` | 全流程编排 | 以上所有 |

## Instagram 抓取能力

### 已验证（2026-04-07）
- **无需登录**即可从标签探索页获取视频 CDN 链接
- 每个标签页可获取 **12 个视频**的直接下载链接
- 下载速度：3 个视频 < 7 秒
- 抽帧速度：9帧/视频 < 1 秒

### Playwright 配置
```bash
pip install playwright opencv-python-headless
python -m playwright install chromium
```

### 使用示例
```bash
# 仅获取元数据
python Scripts/fetch_instagram_video.py seedance --metadata-only

# 下载前 3 个视频
python Scripts/fetch_instagram_video.py seedance --num 3 --output ig_videos

# 抽帧
python Scripts/extract_frames.py ig_videos/seedance_0.mp4
```

## Seedance 2.0 Prompt 规范

基于 Higgsfield 官方 Prompt Guide 的关键发现：

1. **Seedance prompt 应极简** — 仅包含 camera + subject + action
2. **复杂视觉描述放在 Popcorn** — 图片生成阶段用长 prompt 锁定构图/色调/材质
3. **@Reference 系统** — 最多 9 张图 + 3 个视频 + 3 个音频
4. **风格锚点** — "35mm film, shallow DOF, Roger Deakins" 为官方高频词
