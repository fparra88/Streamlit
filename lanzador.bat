@echo off
:: 1. Forzar a que el archivo se ejecute en la carpeta donde está guardado
cd /d "%~dp0"

:: 2. Verificar si el archivo .py existe antes de lanzarlo
if not exist "ui.py" (
    echo [ERROR] No encuentro el archivo ui.py en esta carpeta.
    echo Carpeta actual: %cd%
    pause
    exit
)

echo Iniciando servidor de Streamlit...
:: 3. Usar "python -m streamlit" es más seguro que solo "streamlit"
python -m streamlit run ui.py

pause