@echo off
rem Script de Inicio Robusto para Estudian2
rem Cambia al directorio donde está ester archivo bat
cd /d "%~dp0"

echo ====================================================
echo      🎓 INICIANDO ESTUDIAN2 - TU ASISTENTE IA
echo ====================================================
echo.
echo Cargando sistema... por favor espera.
echo.

rem Ejecutar Streamlit
streamlit run app.py

rem Si falla, pausa para ver el error
if %errorlevel% neq 0 (
    echo.
    echo ❌ OCURRIO UN ERROR.
    echo Por favor revisa el mensaje de arriba.
    pause
)
