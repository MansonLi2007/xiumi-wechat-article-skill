# 配图：决策、尺寸、prompt、版权

## 1. 先决策：这篇要不要图

| 情况 | 方案 |
|---|---|
| 用户提供了图 | 直接用，先查尺寸/清晰度/授权 |
| 有数据或流程 | 优先做图表/示意图（matplotlib 或 HTML 表格），**不要用 AI 画图** |
| 概念/氛围类 | AI 生成 1 张封面 + 2–3 张正文图 |
| 没有任何素材且不配图 | 纯排版方案：用卡片、引用、分割线、大字号做视觉节奏，明确告诉用户「无图版」 |

一篇文章只用一种图类型（摄影 / 插画 / 图表），混用最显廉价。

## 2. 尺寸

| 用途 | 比例 | 像素 | 说明 |
|---|---|---|---|
| 封面主图 | 2.35:1 | 900×383 或 1080×460 | 转发卡片、列表页 |
| 分享小图 | 1:1 | 1080×1080 | 会话/朋友圈分享 |
| 正文横图 | 16:9 | 1080×608（最低 900×506） | 最通用 |
| 正文方图 | 4:3 | 900×675 | 并排双图时用 |
| 并排小图 | 1:1 | 600×600 | 双栏各一张 |
| 二维码 | 1:1 | ≥ 300×300 | 太小扫不出 |

体积：单图 ≤ 500KB（硬上限 2MB）。gif 控制在 3MB 内且不超过 1 张。

## 3. 图注

- ≤ 15 字，写信息不写指认：「2024 年打开率变化」✅，「如上图所示」❌。
- 有数字来源就写来源：「数据：新榜，2025」。
- 多图时编号：图 1 / 图 2，正文里可以引用编号。
- 图注字号 13px、灰、居中，上下留 8px。

## 4. AI 出图 prompt 模板

通用规则：**不让模型画中文字**（必然乱码）；封面文字用 HTML/秀米叠加。一条 prompt 只说一件事：主体、构图、留白位置、色板、风格、禁止项。

### 封面（2.35:1）

```
Wide editorial banner, 2.35:1. Subject: <一句话主体，如 "a tidy desk with a laptop and a paper notebook">.
Composition: single strong focal point on the right third, large calm empty space on the left for a headline.
Palette: warm paper white #FAF8F3, terracotta accent #B4552D, deep charcoal #2B2B2B.
Style: flat vector with subtle paper grain, generous negative space, high contrast silhouette.
No text, no letters, no numbers, no logo, no watermark, no UI mockup.
```

### 正文场景图（16:9）

```
16:9 photograph, soft natural window light, shallow depth of field. Scene: <具体场景>.
Muted warm color grading, uncluttered background, one clear subject.
No text, no watermark, no recognizable faces of real people.
```

### 概念/抽象图（16:9）

```
16:9 minimalist conceptual illustration. Idea: <概念，如 "three layers of a process stacked cleanly">.
Flat geometric shapes, two-color palette (#B4552D on #FAF8F3), lots of whitespace.
No text, no labels, no icons of well-known brands.
```

### 图表类（别用 AI）

数据图用 matplotlib 出 PNG（宽 900，字体用系统中文字体），或直接在 HTML 里用表格排。AI 生成的图表数字全是错的。

## 5. 后处理（统一风格 + 压体积）

```bash
python scripts/prep_images.py images/cover.png --out images/ --name cover
```

产出 `cover-235.jpg`（900×383）与 `cover-11.jpg`（1080×1080），居中裁切、转 sRGB、质量 82、尽量 ≤ 500KB。多张图用同一命令批量跑，保证色温与压缩一致。

## 6. 版权与风险

- AI 图也有平台规则与商用授权问题，别生成真实名人、品牌 logo、影视角色。
- 网图、影视截图、明星照、同行公众号的图：不要用。
- 人物正脸需授权；办公场景类 AI 图不要出现可识别真人。
- 字体商用需授权，封面别用未授权商业字体。
- 有疑问就在文末写图片来源，或直接换成纯排版。
