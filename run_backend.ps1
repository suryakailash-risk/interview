$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

& "$root\.venv\Scripts\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
