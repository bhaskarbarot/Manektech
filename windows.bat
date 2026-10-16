@echo off
setlocal EnableExtensions
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1

set "MODE=%~1"
if "%MODE%"=="" set "MODE=full"
if /i not "%MODE%"=="full" if /i not "%MODE%"=="quick" (
  echo usage: windows.bat [full^|quick]
  goto :fail
)
set "VENV_PY=.venv\Scripts\python.exe"

echo.
echo ==^> Checking Docker
where docker >nul 2>nul
if errorlevel 1 (
  echo ERROR: Docker Desktop is not installed. Install it from https://www.docker.com/products/docker-desktop/ and run this file again.
  goto :fail
)
docker info >nul 2>nul
if errorlevel 1 (
  echo ERROR: Docker Desktop is not running. Open Docker Desktop, wait until it says running, then run this file again.
  goto :fail
)
docker compose version >nul 2>nul
if errorlevel 1 (
  echo ERROR: Docker Compose v2 is missing. Update Docker Desktop.
  goto :fail
)

echo.
echo ==^> Checking Python 3.11+
set "PY="
for %%V in (3.13 3.12 3.11) do (
  if not defined PY (
    py -%%V -c "import sys" >nul 2>nul && set "PY=py -%%V"
  )
)
if not defined PY (
  python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo ERROR: Python 3.11 or newer is required. Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH".
  goto :fail
)
%PY% --version

echo.
echo ==^> Starting PostgreSQL + pgvector in Docker (port 5433)
docker compose up -d --wait
if errorlevel 1 goto :fail

echo.
echo ==^> Creating virtual environment .venv
if not exist "%VENV_PY%" (
  %PY% -m venv .venv
  if errorlevel 1 goto :fail
)
"%VENV_PY%" -m pip install --quiet --upgrade pip
if errorlevel 1 goto :fail

echo.
echo ==^> Installing the project
"%VENV_PY%" -m pip install --quiet -e ".[dev]"
if errorlevel 1 goto :fail

set "MODEL=hashing"
if /i "%MODE%"=="full" (
  echo.
  echo ==^> Installing the local multilingual embedding model ^(CPU only, first run downloads a few hundred MB^)
  "%VENV_PY%" -m pip install --quiet torch --index-url https://download.pytorch.org/whl/cpu && "%VENV_PY%" -m pip install --quiet -e ".[dev,local-embeddings]" && set "MODEL=st"
)
if /i "%MODE%"=="full" if "%MODEL%"=="hashing" echo WARNING: could not install the local model, continuing with the built-in hashing model

echo.
echo ==^> Creating the database schema
"%VENV_PY%" -m ontology_store.db.scripts.create_schema
if errorlevel 1 goto :fail

echo.
echo ==^> Running the tests
"%VENV_PY%" -m pytest -q
if errorlevel 1 goto :fail

echo.
echo ==^> Running the demo (model: %MODEL%)
"%VENV_PY%" -m ontology_store.demo --model %MODEL%
if errorlevel 1 goto :fail

echo.
echo ==^> Done
echo Setup, tests and demo finished successfully.
echo Run the demo again:  .venv\Scripts\python -m ontology_store.demo --model %MODEL%
echo Run the tests again: .venv\Scripts\pytest
echo Stop the database:   docker compose down

echo.
echo ==^> Starting the test UI (Streamlit)
"%VENV_PY%" -m pip install --quiet -e ".[dev,ui]"
if errorlevel 1 (
  echo WARNING: could not install Streamlit, the UI was skipped. Setup, tests and demo above are still fine.
  pause
  exit /b 0
)
set "EMBEDDING_MODEL=%MODEL%"
echo The UI opens in your browser at http://localhost:8501
echo Press Ctrl+C in this window to stop the UI.
echo Start it again later: .venv\Scripts\python -m streamlit run ui\app.py
start "" /b cmd /c "ping -n 7 127.0.0.1 >nul && start http://localhost:8501"
"%VENV_PY%" -m streamlit run ui\app.py
if errorlevel 1 pause
exit /b 0

:fail
echo.
echo Setup stopped because of the error above.
pause
exit /b 1
