# Windows entry point. Reuse an installed Python; never install dependencies here.
$ErrorActionPreference = 'Stop'
$python = $env:FACTORY_PYTHON
if (-not $python) {
    $bundled = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
    if (Test-Path -LiteralPath $bundled) { $python = $bundled }
    else {
        $command = Get-Command python -ErrorAction SilentlyContinue
        if ($command) { $python = $command.Source }
    }
}
if (-not $python -or -not (Test-Path -LiteralPath $python)) {
    throw 'Python 3.11+ is required. Set FACTORY_PYTHON to an existing python.exe.'
}
& $python (Join-Path $PSScriptRoot 'factory.py') @args
exit $LASTEXITCODE
