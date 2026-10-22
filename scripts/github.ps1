# Run only the project-local GitHub CLI; preserve native command arguments.
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$cli = Join-Path $root '.tools/gh/bin/gh.exe'
if (-not (Test-Path -LiteralPath $cli)) { throw 'Project-local gh is missing.' }
$env:GH_CONFIG_DIR = Join-Path $root 'local-output/gh-config'
& $cli @args
exit $LASTEXITCODE
