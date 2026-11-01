#!/usr/bin/env sh
# 安装 xiumi-wechat-article 技能（macOS / Linux）
#   sh install.sh                      装到用户级 ~/.dsh/skills/
#   sh install.sh project              装到当前目录 ./.dsh/skills/
#   sh install.sh /some/skills         装到指定 skills 目录
set -eu

SKILL="xiumi-wechat-article"
DIR=$(cd "$(dirname "$0")" && pwd)
SRC="$DIR/$SKILL"

[ -f "$SRC/SKILL.md" ] || { echo "包不完整：找不到 $SRC/SKILL.md（确认解压后没多套一层目录）" >&2; exit 1; }

case "${1:-user}" in
  user)    ROOT="$HOME/.dsh/skills" ;;
  project) ROOT="$PWD/.dsh/skills" ;;
  *)       ROOT="$1" ;;
esac

DEST="$ROOT/$SKILL"
mkdir -p "$ROOT"

if [ -e "$DEST" ]; then
  BACKUP="$DEST.bak-$(date +%Y%m%d-%H%M%S)"
  mv "$DEST" "$BACKUP"
  echo "已备份旧版到 $BACKUP"
fi

cp -R "$SRC" "$DEST"

[ -f "$DEST/SKILL.md" ] || { echo "复制后找不到 SKILL.md：$DEST" >&2; exit 1; }

if ! head -n 10 "$DEST/SKILL.md" | grep -Eq "^name:[[:space:]]*$SKILL[[:space:]]*$"; then
  echo "警告：SKILL.md 的 name 与目录名不一致，可能加载不出来" >&2
fi

MISSING=""
for f in references/copywriting.md references/layout-blueprint.md references/image-brief.md \
         references/wechat-spec.md references/xiumi-workflow.md assets/themes.json \
         assets/template.html assets/sample-article.md scripts/build_wechat.py scripts/check_article.py; do
  [ -f "$DEST/$f" ] || MISSING="$MISSING $f"
done
[ -z "$MISSING" ] || echo "警告：缺少文件：$MISSING" >&2

if command -v python3 >/dev/null 2>&1; then
  if python3 "$DEST/scripts/build_wechat.py" "$DEST/assets/sample-article.md" -o /tmp/xiumi-selftest.html >/dev/null 2>&1; then
    echo "Python 自检通过（示例稿能出 HTML）"
  else
    echo "警告：Python 自检失败，请确认 Python 版本（需 3.10+）" >&2
  fi
  rm -f /tmp/xiumi-selftest.html
else
  echo "没找到 python3，跳过脚本自检（技能正文不受影响）"
fi

COUNT=$(find "$DEST" -type f | wc -l | tr -d ' ')
echo
echo "装好了：$DEST（$COUNT 个文件）"
echo "验证：新开会话输入 /$SKILL，或直接说「用秀米帮我写一篇公众号推文」。"
