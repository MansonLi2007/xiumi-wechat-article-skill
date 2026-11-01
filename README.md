# 秀米公众号推文技能 · Xiumi WeChat Article Skill

**中文** | [English](#english)

> 把一篇文章变成可直接粘贴进微信公众号的图文 —— 简报、标题、摘要、排版、封面、质检，一条流水线走完。
> An agent skill that turns a rough idea into a publish-ready WeChat article: brief → copy → layout → images → single-file HTML → QA.

---

## ⬇️ 下载 / Download

| | 链接 |
|---|---|
| **完整安装包 v1.2.0** | [xiumi-wechat-article-skill-1.2.0.zip](https://github.com/MansonLi2007/xiumi-wechat-article-skill/releases/latest/download/xiumi-wechat-article-skill-1.2.0.zip) |
| **最新源码** | [main.zip](https://github.com/MansonLi2007/xiumi-wechat-article-skill/archive/refs/heads/main.zip) |
| **Git 克隆** | `git clone https://github.com/MansonLi2007/xiumi-wechat-article-skill.git` |

下载后解压，Windows 双击 `install.cmd`，macOS / Linux 运行 `sh install.sh`。
Unzip, then run `install.cmd` on Windows or `sh install.sh` on macOS / Linux.


## 中文说明

### 这是什么

一个纯文件形式的 agent skill（无需安装包、无网络请求、不依赖 npm），按「SKILL.md + 目录」的约定组织，DSH、Claude Code 等支持该约定的 agent 都能直接加载。

### 它解决什么问题

公众号排版最耗时的不是写字，是「写完还要手工调格式」。这个技能把流程拆成 7 步，每步给出默认值和验收标准，最后产出可直接粘贴进秀米/公众号的单文件 HTML（内联样式、≤677px、无外链、无 JS），粘贴后版式不跑版。

### 七步流水线

| 步骤 | 做什么 | 产出 |
|---|---|---|
| 1 简报 | 账号类型、读者、篇幅、语气、目的、主题、图源，默认值优先，只问两个关键项 | 一行假设说明 |
| 2 文案 | 标题 3 选 1（≤24 字）、摘要（≤60 字）、正文骨架 A–E、高亮/引用/卡片 | `article.md` |
| 3 排版 | 选主题、定视觉节奏、用指令块标注区块，样式由脚本统一生成 | 区块计划 |
| 4 配图 | 封面 2.35:1 + 1:1、正文 16:9；无图源时给配图 prompt 清单 | `images/` |
| 5 出 HTML | markdown → 全内联样式的公众号 HTML | `article.html` |
| 6 进微信/秀米 | 四条落地路线：直接粘贴、秀米导入、源码模式、图片单独上传 | 可发布的图文 |
| 7 质检 | 脚本查尺寸/外链/JS/字号/图片体积 + 人工检查项 | `QA.md` |

### 快速开始

```bash
# Windows
install.cmd
# macOS / Linux
sh install.sh
```

默认安装到用户级目录（所有项目可用）：

```
Windows:      %USERPROFILE%\.dsh\skills\xiumi-wechat-article\
macOS/Linux:  ~/.dsh/skills/xiumi-wechat-article/
```

装到当前项目（可随仓库提交）：`install.cmd project` / `sh install.sh project`
装到别处：`install.cmd -Target "D:\my\skills"` / `sh install.sh /my/skills`

安装脚本会顺带备份同名旧版、检查目录层级，并用示例稿跑一遍自检。

### 目录结构

```
xiumi-wechat-article/
├── SKILL.md                  # 技能入口：7 步流水线
├── INSTALL.md                # 安装细则
├── references/               # 五份细则
│   ├── copywriting.md        # 标题 10 公式、摘要 3 式、正文骨架、金句、合规红线
│   ├── layout-blueprint.md   # 设计 token、3 套主题、12 个区块规格、封面规范
│   ├── image-brief.md        # 配图决策表、尺寸表、图注规范、出图 prompt
│   ├── wechat-spec.md        # 微信硬限制、编辑器行为、内容合规
│   └── xiumi-workflow.md     # 秀米真机实测：登录、编辑器结构、四条落地路线
├── assets/
│   ├── themes.json           # paper / ink / mint 三套主题
│   ├── template.html         # 双栏、双图、分割线、图注片段
│   ├── sample-article.md     # 可直接跑通的示例稿
│   └── images/               # 示例封面与正文图
└── scripts/
    ├── build_wechat.py       # markdown → 全内联样式公众号 HTML
    ├── check_article.py      # 发布前质检，输出 QA.md，有错误退出码 1
    └── prep_images.py        # 裁封面、分享图、正文图，压到 ≤500KB
```

### 依赖

| 用途 | 需要 |
|---|---|
| 读技能、出 HTML、质检 | Python 3.10+（仅标准库） |
| 裁封面 / 配图尺寸 | 额外 `pip install Pillow` |

没有 Python 也能用，只是三个脚本跑不了，agent 会改为手写 HTML。

### 自检

```bash
python scripts/build_wechat.py assets/sample-article.md -o test.html
# 看到 [ok] theme=paper blocks_html=19 即环境正常
```

### 兼容性

只依赖「目录 + SKILL.md + frontmatter」约定，不依赖 DSH 私有 API。Claude Code 等 agent 把文件夹放进各自的 skills 目录（如 `~/.claude/skills/`）即可；脚本内的数据路径都从脚本自身位置推导，换工作目录也能跑。

### 版本

v1.2.0 · MIT License

---

<a id="english"></a>
## English

### What it is

A pure-file agent skill — no package install, no network calls, no npm — organized around the `SKILL.md + directory` convention, so any agent that understands that convention (DSH, Claude Code, …) can load it.

### Why it exists

The slow part of publishing on WeChat isn't writing; it's re-styling everything by hand afterwards. This skill splits the work into 7 steps with sensible defaults and acceptance criteria, and emits a single-file HTML (inline styles, ≤677px wide, no external links, no JS) that survives a copy-paste into Xiumi or the WeChat editor without breaking layout.

### The 7-step pipeline

| Step | What happens | Output |
|---|---|---|
| 1 Brief | Audience, length, tone, goal, theme, image source — defaults first, only two blocking questions | One-line assumption note |
| 2 Copy | 3 headline options (≤24 chars), a ≤60-char summary, body skeletons A–E, highlights / quotes / cards | `article.md` |
| 3 Layout | Pick a theme, set visual rhythm, mark blocks with directive syntax; styles are generated, never hand-written | Block plan |
| 4 Images | 2.35:1 cover, 1:1 share card, 16:9 body images; prompt list when no art is available | `images/` |
| 5 HTML | Markdown → fully inline-styled WeChat HTML | `article.html` |
| 6 Publish | Four routes into WeChat / Xiumi: direct paste, Xiumi import, source mode, images uploaded separately | Publishable article |
| 7 QA | Script checks size, external links, JS, font sizes, image weight + manual checklist | `QA.md` |

### Quick start

```bash
# Windows
install.cmd
# macOS / Linux
sh install.sh
```

Default target is user-level (available to every project):

```
Windows:      %USERPROFILE%\.dsh\skills\xiumi-wechat-article\
macOS/Linux:  ~/.dsh/skills/xiumi-wechat-article/
```

Project-level install: `install.cmd project` / `sh install.sh project`
Custom target: `install.cmd -Target "D:\my\skills"` / `sh install.sh /my/skills`

The installer backs up an older copy, checks the directory depth (skills are scanned one level deep), and smoke-tests the scripts against the sample article.

### Dependencies

| Purpose | Requirement |
|---|---|
| Read the skill, build HTML, run QA | Python 3.10+ (standard library only) |
| Cover / image resizing | `pip install Pillow` |

Without Python the skill still works — the three scripts just don't run and the agent writes HTML by hand.

### Self-check

```bash
python scripts/build_wechat.py assets/sample-article.md -o test.html
# expect: [ok] theme=paper blocks_html=19
```

### License

MIT © 2026
