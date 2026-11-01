# 安装 xiumi-wechat-article 技能（Windows）
#
#   .\install.ps1                  装到用户级：%USERPROFILE%\.dsh\skills\
#   .\install.ps1 -Scope project   装到当前目录：<当前目录>\.dsh\skills\
#   .\install.ps1 -Target "D:\some\skills"   装到指定 skills 目录
#
# 技能就是一堆文件：把 xiumi-wechat-article 整个目录放进任意 skills 目录即可。
# 这个脚本只是把「复制 + 备份旧版 + 自检」串起来，避免手抖多套一层目录。
param(
    [ValidateSet("user", "project")]
    [string]$Scope = "user",
    [string]$Target = ""
)

$ErrorActionPreference = "Stop"
$skillName = "xiumi-wechat-article"
$src = Join-Path $PSScriptRoot $skillName

if (-not (Test-Path (Join-Path $src "SKILL.md"))) {
    throw "包不完整：找不到 $src\SKILL.md（请确认解压后没有多套一层目录）"
}

if ($Target) {
    $skillsRoot = $Target
} elseif ($Scope -eq "project") {
    $skillsRoot = Join-Path (Get-Location) ".dsh\skills"
} else {
    $skillsRoot = Join-Path $HOME ".dsh\skills"
}

$dest = Join-Path $skillsRoot $skillName

New-Item -ItemType Directory -Force -Path $skillsRoot | Out-Null

# 旧版备份，不直接覆盖
if (Test-Path $dest) {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backup = "$dest.bak-$stamp"
    Move-Item $dest $backup
    Write-Host "已备份旧版到 $backup"
}

Copy-Item $src $dest -Recurse -Force

# 自检 1：目录层级与入口文件
$entry = Join-Path $dest "SKILL.md"
if (-not (Test-Path $entry)) { throw "复制后找不到 SKILL.md，安装失败：$dest" }

# 自检 2：frontmatter 的 name 必须与目录名一致
$head = Get-Content $entry -TotalCount 10 -Encoding UTF8
if (-not ($head -match "^name:\s*$skillName\s*$")) {
    Write-Warning "SKILL.md 里的 name 与目录名 '$skillName' 不一致，可能加载不出来"
}

# 自检 3：文件齐全
$required = @(
    "references\copywriting.md",
    "references\layout-blueprint.md",
    "references\image-brief.md",
    "references\wechat-spec.md",
    "references\xiumi-workflow.md",
    "assets\themes.json",
    "assets\template.html",
    "assets\sample-article.md",
    "scripts\build_wechat.py",
    "scripts\check_article.py"
)
$missing = @($required | Where-Object { -not (Test-Path (Join-Path $dest $_)) })
$count = (Get-ChildItem $dest -Recurse -File).Count
if ($missing.Count -gt 0) { Write-Warning ("缺少文件：" + ($missing -join ", ")) }

# 自检 4：python 可用就跑一遍示例稿
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
if ($py) {
    $out = Join-Path $env:TEMP "xiumi-selftest.html"
    & $py.Source (Join-Path $dest "scripts\build_wechat.py") (Join-Path $dest "assets\sample-article.md") -o $out 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-Host "Python 自检通过（示例稿能出 HTML）" }
    else { Write-Warning "Python 自检失败，脚本可能跑不起来，请检查 Python 版本（需 3.10+）" }
    Remove-Item $out -Force -ErrorAction SilentlyContinue
} else {
    Write-Host "没找到 python，跳过脚本自检（技能正文不受影响）"
}

Write-Host ""
Write-Host "装好了：$dest（$count 个文件）"
Write-Host "验证：新开一个会话，输入 /$skillName，或直接说「用秀米帮我写一篇公众号推文」。"
Write-Host "技能目录是热监听的，通常不用重启；没生效就重启一次 DSH。"
