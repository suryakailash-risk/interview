$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

& "$root\.venv\Scripts\python.exe" -m streamlit run frontend/app.py --server.port 8501
