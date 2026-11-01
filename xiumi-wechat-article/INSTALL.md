# 安装 / 迁移说明

这是一个**纯文件技能**：只有 Markdown 说明、一个 HTML 片段模板、三张示例图、三个 Python 脚本。
没有构建步骤、没有 npm 依赖、没有打包产物，整个目录拷到哪儿都能用。

- 技能入口：`SKILL.md`（YAML frontmatter 里的 `name` 必须叫 `xiumi-wechat-article`，与目录名一致）
- 运行时依赖：Python 3.10+；只有 `scripts/prep_images.py`（裁封面/配图）需要 Pillow，`build_wechat.py` 与 `check_article.py` 只用标准库

## 一、装进 DeepSeek Harness（三种位置，按优先级）

| 位置 | 路径 | 适用 |
|---|---|---|
| 项目级 | `<项目根>/.dsh/skills/xiumi-wechat-article/` | 只给某个项目用，可随仓库提交 |
| **用户级（推荐）** | `~/.dsh/skills/xiumi-wechat-article/` | 所有项目都能用 |
| 插件级 | `<插件包>/skills/xiumi-wechat-article/` | 想把技能连同插件一起分发（需要 pnpm 打包插件） |

Windows 上 `~` 就是 `C:\Users\<你的用户名>`，所以用户级路径是：

```
C:\Users\<你的用户名>\.dsh\skills\xiumi-wechat-article\SKILL.md
```

安装就是把解压出来的 `xiumi-wechat-article` 整个文件夹放进上面任一 `skills` 目录：

```powershell
# Windows
Expand-Archive .\xiumi-wechat-article-skill-1.2.0.zip -DestinationPath "$HOME\.dsh\skills" -Force
```
```bash
# macOS / Linux
unzip xiumi-wechat-article-skill-1.2.0.zip -d ~/.dsh/skills/
```

目录结构必须是：

```
~/.dsh/skills/xiumi-wechat-article/
├── SKILL.md
├── INSTALL.md
├── references/{copywriting,layout-blueprint,image-brief,wechat-spec,xiumi-workflow}.md
├── assets/{themes.json,template.html,sample-article.md,images/*.jpg}
└── scripts/{build_wechat.py,check_article.py,prep_images.py}
```

注意：DSH 只扫描 `skills/` 的**下一层**（`<name>/SKILL.md` 或 `<name>.md`），不会再往深处递归。多套一层目录就会扫不到。

## 二、怎么确认装上了

1. **目录监听是热的**：新增/改名/删除技能目录会立刻刷新技能目录清单，不用重启 DSH。
2. 重启会话也能看到——技能清单在首个请求前就注入。
3. 直接点名试：`/xiumi-wechat-article`，或问一句「用秀米帮我写一篇公众号推文」，能加载出正文即成功。
4. 脚本自检（无 Pillow 也能跑前两个）：

```powershell
python "$HOME\.dsh\skills\xiumi-wechat-article\scripts\build_wechat.py" --help
```

## 三、升级与卸载

- 升级：直接覆盖同名目录，技能正文每次加载都重读文件，没有缓存版本号。
- 卸载：删掉整个 `xiumi-wechat-article` 目录即可，不写注册表、不留残留。
- 想改名：目录名和 `SKILL.md` 里的 `name:` 要一起改。

## 四、给别的 agent 用

这个包只依赖约定（目录 + `SKILL.md` + frontmatter），不依赖 DSH 私有 API。
Claude Code、以及其他支持 `SKILL.md` 约定的 agent，把这个文件夹放进它们各自的 skills 目录（例如 `~/.claude/skills/`）即可；
脚本里的路径都用「脚本自身所在目录」推导数据文件，所以从一个工作目录搬到另一个也能跑。

## 五、包内文件说明

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 7 步流水线主文档，含触发条件、交付物清单、微信兼容铁律、反模式 |
| `references/copywriting.md` | 标题 10 公式、摘要 3 式、正文骨架 A–E、金句句式、语气三档、合规红线 |
| `references/layout-blueprint.md` | 设计 token、三套主题、12 个区块规格 + HTML 骨架、节奏规则、封面规范、秀米组件路径 |
| `references/image-brief.md` | 配图决策表、尺寸表、图注规范、4 个出图 prompt 模板、版权风险 |
| `references/wechat-spec.md` | 微信硬限制、编辑器行为、内容合规、数据量级基线 |
| `references/xiumi-workflow.md` | 秀米真机实测：登录、编辑器结构、三级菜单、四条落地路线、导出机制、踩坑表 |
| `assets/themes.json` | paper / ink / mint 三套主题 token |
| `assets/template.html` | 双栏、双图、分割线、图注、结尾、提示条的手拼片段 |
| `assets/sample-article.md` | 可直接跑通的示例稿（含 frontmatter 与 `:::lead/:::card/:::notice/:::end` 指令） |
| `scripts/build_wechat.py` | md → 全内联 style 的公众号 HTML 片段，支持 `--placeholder-images` / `--keep-relative` |
| `scripts/check_article.py` | 发布前质检，输出 QA.md，有 ERR 时退出码 1 |
| `scripts/prep_images.py` | 裁封面 2.35:1 / 1:1 / 正文 16:9，转 sRGB，压到 ≤500KB |
