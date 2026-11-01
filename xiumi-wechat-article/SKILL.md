---
name: xiumi-wechat-article
description: 用秀米（xiumi.us）做微信公众号推文的完整流水线：简报→标题/摘要/正文→排版蓝图与主题 token→封面与配图→生成可直接粘贴进微信或秀米的单文件 HTML→发布前质检。当用户要写公众号推文、做秀米排版、公众号配图/封面、定标题摘要、把 markdown 文稿排成公众号版式时使用。
whenToUse: 用户提到公众号、推文、图文、秀米、排版、封面、摘要、标题、涨粉/转发/完读率，或要求把一段文稿变成可发布到公众号的版式。
metadata:
  version: 1.2.0
  license: MIT
  requires: python>=3.10, Pillow>=9（仅配图脚本需要）
---

# 秀米公众号推文流水线

把「一篇文章 → 可发布的公众号图文」拆成 7 步，每步都有默认值和验收标准。默认假设先做、再让用户改，不要用问题清单盘问用户。

典型触发：用户说「用秀米帮我写一篇公众号推文，主题是 XXX，配封面」→ 直接走 Step 1–7，最后交付 article.md + 预览版 HTML + 粘贴版 HTML + 图片 + QA。

## 交付物（默认全给，用户只要其中几件时按需裁剪）

1. `article.md` — 标题 3 选 1、摘要、正文（含小标题/高亮/引用/图注/结尾引导）
2. `article.html` — 微信兼容单文件 HTML（内联样式、≤677px、无外链、无 JS）
3. `images/` — 封面 2.35:1 与 1:1、正文图；无图源时给「配图 prompt 清单」代替
4. `QA.md` — `check_article.py` 结果 + 人工检查项结论
5. 一句话说明：用了哪套主题、假设了哪些简报项

## 工作流

### Step 1 简报（默认值优先）

| 项 | 默认 |
|---|---|
| 账号类型 | 个人知识/职场类 |
| 读者 | 25–35 岁上班族 |
| 篇幅 | 1200–1800 字 |
| 语气 | 克制、具体、少形容词 |
| 目的 | 收藏（其次转发，再次涨粉） |
| 主题 | `paper`（米白纸感，见 themes.json） |
| 图源 | 用户提供 → 否则 AI 生成 → 否则纯排版无图 |

只问两件缺了就没法开工的事：**主题/素材**、**目的**。其余用默认，开头一行写明「我按 X 假设来做，要改告诉我」。

### Step 2 文案

先读 `references/copywriting.md`，按里面的骨架产出。硬规则：

- 标题 3 个候选，**≤ 24 字**（平台上限 64，但列表页约 20 字就截断），每个标注所用公式。
- 摘要 **≤ 60 字**（上限 120），能独立成句，不复述标题，不写「点击查看」。
- 开头 3 行内必须让读者知道「能得到什么」。
- 小标题 ≤ 15 字，连起来能当目录被扫读。
- 每段 ≤ 4 行（手机 3–4 行），单句 ≤ 40 字。
- 至少 2 处 `==高亮==`、1 处引用块、1 处列表或卡片。
- 结尾 = 一句总结 + **一个**具体动作（在看 / 转发给某人 / 留言一个具体问题），不要「点赞关注在看」三连口号。

### Step 3 排版

读 `references/layout-blueprint.md`：选主题 → 定节奏（每 300 字一个视觉锚点）→ 用指令块标注区块，样式交给脚本统一出，**不要手写 style**。

```
:::lead  导语（浅底大字）
:::card 小标题     卡片（白底描边）
:::quote           金句引用
:::notice          提示条（重点色左边线）
:::end             结尾签名/引导
```

### Step 4 封面与配图

读 `references/image-brief.md`：

- 封面：主用 **2.35:1**（900×383 或 1080×460），同时出一张 **1:1**（1080×1080）；封面上的中文标题用 HTML/秀米叠加，**不要让 AI 画中文字**。
- 正文图：宽 ≥ 900px，16:9 或 4:3，单图建议 ≤ 500KB（上限 2MB）。
- 每图必须有 ≤ 15 字图注，图注写信息（「2024 年打开率变化」），不写「如上图所示」。
- AI 出图用 `generate_image`，prompt 模板见 image-brief；同一篇只用一种图类型（插画 or 摄影 or 图表），色温统一。
- 来源不明就用 AI 生成或纯排版无图，不要塞网图。

### Step 5 出 HTML

脚本在**技能目录**里，不在用户工作目录里。先定位技能目录：

```powershell
# Windows / PowerShell
$SKILL = "$HOME\.dsh\skills\xiumi-wechat-article"      # 项目内安装则改为 <项目>\.dsh\skills\xiumi-wechat-article
```
```bash
# macOS / Linux
export SKILL=~/.dsh/skills/xiumi-wechat-article
```

```bash
# 本地预览版：图片转成 file:// 绝对路径，浏览器打开就能看整体节奏
python "$SKILL/scripts/build_wechat.py" article.md --theme paper -o article.html

# 粘贴版：图片位置变成带图注的虚线占位块，避免粘进微信后一片破图
python "$SKILL/scripts/build_wechat.py" article.md -o article-paste.html --placeholder-images

python "$SKILL/scripts/check_article.py" article.md --html article.html -o QA.md
```

脚本只依赖标准库 + Pillow（`prep_images.py` 才需要 Pillow），没有第三方包、没有绝对路径，整个目录可以原样拷走。

`python` 不在 PATH 时，用 `load_workspace_dependencies` 返回的 python 绝对路径。产物必须是**片段**（`<section>` 开头），不能有 `<html>/<head>/<style>/<script>`。

为什么分两版：微信/秀米取不到 `file://` 的图，直接粘预览版一般会破图；`--placeholder-images` 版粘贴后文字版式完整，再在编辑器里逐张插图，最稳。想保留 `<img>` 就用 `--keep-relative`，并把图片放到与 HTML 同目录的 `images/`。

### Step 6 送进秀米或公众号

读 `references/xiumi-workflow.md`（内含 2026-10 真机实测的界面结构），给用户「四选一 + 一条兜底」：

- **A 秀米原生（最稳）**：照 layout-blueprint 当施工图，在秀米里搭：`布局 → 基础布局 / 左右图文`、`图片 → 单图 / 双图`、`组件 → 分割线 / 二维码 / 引导关注`。适合长期维护、要模板库风格的号。
- **B 复制粘贴（最快）**：浏览器打开 `article-paste.html` → 全选复制 → 公众号后台粘贴 → 再插图。本地图片地址微信抓不到，所以用占位版。
- **C 导入 HTML 代码（保留我们的版式，需 VIP）**：`更多 → 导入HTML代码` → 贴片段 → 右侧预览无损 → 导入。实测 LV.1 账号点导入无反应，没会员走 B。
- **D 同步到公众号**：`授权设置 → 点击开始微信公众授权`，**必须公众号管理员本人扫码**，运营者只能把二维码截图发管理员。
- **兜底**：都不通就 `更多 → 生成长图`，发图片版。

### Step 7 质检（必须做，输出结论）

`check_article.py` 自动查：标题/摘要字数、正文外链、禁用标签、图片路径是否存在、段落超长、全角空格、敏感词、emoji 数量。

人工项（逐条给结论，不要写「看起来没问题」）：

1. 封面在 2.35:1 裁切后主标题是否还在安全区
2. 首屏是否有「标题 + 一句价值 + 一张图」
3. 摘要脱离标题能否独立成立
4. 每屏是否至少一个视觉锚点（小标题/图/引用/卡片）
5. 手机预览三处断行是否难看（长英文、长数字、括号换行）
6. 引导（二维码/往期/关注）是否有效、是否过期

不合格就回去改，不要交付「差不多」。

## 铁律：微信兼容

- 只用**内联 style**；不要 `<style>` 标签、class、id、CSS 变量、`:hover`、`@media`（会被剥离）。
- 不要 `<script>`、`<iframe>`、`<video>`、外链字体、`position:fixed`。
- 不要 grid、flex + gap、负 margin（部分 Android WebView 会错位）。分栏用 `<table role="presentation">` 或 inline-block + 定宽。
- 图片块级用 `style="width:100%;display:block;"`，段落内的图用 `width:100%;vertical-align:middle;`，不要写死 px 宽。
- 列表不要用 `<ul>/<li>`（符号会被吃），用带符号的 `<section>/<p>`。
- 颜色写 hex；阴影只用 `box-shadow:0 2px 8px rgba(0,0,0,.06)`。
- 浅底卡片要给**不透明**背景色，透明底在深色模式下会反色错乱。

## 文件索引

- `references/copywriting.md` — 标题公式、摘要、开头钩子、5 种正文骨架、金句、结尾
- `references/layout-blueprint.md` — 设计 token、3 套主题、12 个区块规格（含秀米对应组件）
- `references/xiumi-workflow.md` — 秀米界面操作、三种导出、常见坑
- `references/wechat-spec.md` — 平台限制与合规
- `references/image-brief.md` — 配图决策、尺寸、prompt 模板、版权
- `assets/themes.json` — 主题 token（脚本读取）
- `assets/template.html` — 双栏/二维码/分割线等手拼片段参考
- `assets/sample-article.md` — 可直接跑的示例输入
- `assets/images/` — 示例图（已按 900×383 / 1080×608 预裁好）
- `scripts/build_wechat.py` — md → 微信兼容 HTML
- `scripts/check_article.py` — 质检
- `scripts/prep_images.py` — 封面/正文图裁切压缩

## 反模式

- 不要用「赋能/闭环/抓手/底层逻辑/颗粒度」，除非用户就要这种行话。
- 不要三个排比句堆成金句；一篇最多一个金句块。
- 不要每段加 emoji，全篇 ≤ 3 个。
- 不要交付「标题和正文气质不匹配」的组合（如标题党 + 学术正文）。
- 不要在没读 references 的情况下凭感觉排版——tokens 和区块规格都在里面。
- 不要把 `article.md` 直接丢进秀米「导入 Markdown」：实测整篇会变成一个纯文本块，`#`、`**`、`:::` 全变字面量。要进秀米就用导出的 HTML。
