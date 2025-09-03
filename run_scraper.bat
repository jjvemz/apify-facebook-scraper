@echo off
chcp 65001 >nul
REM Extractor de Reels de Facebook - Lanzador
REM Este archivo te ayuda a configurar y ejecutar el extractor facilmente

echo ==========================================
echo    Extractor de Reels de Facebook
echo ==========================================
echo.

REM Verificar si Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en el PATH
    echo Por favor instala Python 3.10 o superior
    pause
    exit /b 1
)

REM Verificar si el entorno virtual existe
if not exist "venv\" (
    echo Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Fallo la creacion del entorno virtual
        pause
        exit /b 1
    )
)

REM Activar entorno virtual
echo Activando entorno virtual...
call venv\Scripts\activate.bat

REM Instalar/actualizar dependencias
echo Verificando e instalando dependencias...
pip install -r requirements.txt --upgrade
if errorlevel 1 (
    echo ERROR: Fallo la instalacion de dependencias
    pause
    exit /b 1
)

REM Verificar si existe el archivo .env
if not exist ".env" (
    echo.
    echo ADVERTENCIA: Archivo .env no encontrado!
    echo Necesitas crear un archivo .env con tus credenciales de Apify:
    echo.
    echo APIFY_API_TOKEN=tu_token_aqui
    echo REELS_ACTOR_ID=apify/facebook-reels-scraper
    echo COMMENTS_ACTOR_ID=apify/facebook-comments-scraper
    echo.
    echo Presiona cualquier tecla para continuar o Ctrl+C para salir...
    pause >nul
)

:menu
echo.
echo Que quieres hacer?
echo.
echo 1. Extraer datos de URLs (escribir URLs manualmente)
echo 2. Verificar configuracion del sistema
echo 3. Salir
echo.
set /p choice="Elige una opcion (1-3): "

if "%choice%"=="1" goto option1
if "%choice%"=="2" goto option3
if "%choice%"=="3" goto exit
goto invalid_choice

:option1
echo.
echo Ingresa las URLs de los Reels de Facebook:
echo (Separa multiples URLs con comas, maximo 10)
echo.
set /p urls="URLs: "
echo.
echo En que formato quieres los resultados?
echo 1. Excel (xlsx) - Recomendado
echo 2. CSV (texto plano)
set /p format_choice="Formato (1/2) [1]: "
if "%format_choice%"=="" set format_choice=1
if "%format_choice%"=="1" set format=xlsx
if "%format_choice%"=="2" set format=csv

echo.
echo Incluir comentarios de los reels?
set /p comments="Incluir comentarios (s/n) [s]: "
if "%comments%"=="" set comments=s

echo.
echo Incluir datos de seguidores? (COSTO ADICIONAL)
echo Nota: Esto aumenta significativamente el costo en Apify
set /p followers="Incluir seguidores (s/n) [n]: "
if "%followers%"=="" set followers=n

echo.
echo Iniciando extraccion...
set command=python scraper.py --urls "%urls%" --format %format%
if /i "%comments%"=="n" set command=%command% --no-comments
if /i "%followers%"=="s" set command=%command% --include-followers
%command%
goto end

:option3
echo.
echo Verificando configuracion del sistema...
python scraper.py --check-env
goto end

:invalid_choice
echo Opcion invalida. Por favor selecciona 1-3.
pause
goto menu

:end
echo.
echo =============================================
echo Extraccion completada!
echo =============================================
echo Los resultados se han guardado en la carpeta 'output'
echo.
pause

:exit
echo.
echo Hasta la vista!
pause