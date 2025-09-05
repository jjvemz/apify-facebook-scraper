#!/bin/bash

# Extractor de Reels de Facebook - Lanzador (macOS/Linux)
# Este archivo te ayuda a configurar y ejecutar el extractor facilmente

set -e  # Exit on error

echo "=========================================="
echo "   Extractor de Reels de Facebook"
echo "=========================================="
echo

# Verificar si Python esta instalado
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 no esta instalado o no esta en el PATH"
    echo "Por favor instala Python 3.10 o superior"
    echo "En macOS puedes usar: brew install python"
    echo "En Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

# Mostrar version de Python
python3 --version

# Verificar si el entorno virtual existe
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Fallo la creacion del entorno virtual"
        exit 1
    fi
fi

# Activar entorno virtual
echo "Activando entorno virtual..."
source venv/bin/activate

# Verificar si pip esta disponible
if ! command -v pip &> /dev/null; then
    echo "ERROR: pip no esta disponible en el entorno virtual"
    exit 1
fi

# Instalar/actualizar dependencias
echo "Verificando e instalando dependencias..."
pip install -r requirements.txt --upgrade
if [ $? -ne 0 ]; then
    echo "ERROR: Fallo la instalacion de dependencias"
    exit 1
fi

# Verificar si existe el archivo .env
if [ ! -f ".env" ]; then
    echo
    echo "ADVERTENCIA: Archivo .env no encontrado!"
    echo "Necesitas crear un archivo .env con tus credenciales de Apify:"
    echo
    echo "APIFY_API_TOKEN=tu_token_aqui"
    echo "REELS_ACTOR_ID=apify/facebook-reels-scraper"
    echo "COMMENTS_ACTOR_ID=apify/facebook-comments-scraper"
    echo
    echo "Presiona Enter para continuar o Ctrl+C para salir..."
    read -r
fi

# Función para mostrar el menú
show_menu() {
    echo
    echo "¿Que quieres hacer?"
    echo
    echo "1. Extraer datos de URLs (escribir URLs manualmente)"
    echo "2. Verificar configuracion del sistema"
    echo "3. Salir"
    echo
}

# Función para leer input con valor por defecto
read_with_default() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    
    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " input
        if [ -z "$input" ]; then
            input="$default"
        fi
    else
        read -p "$prompt: " input
    fi
    
    eval "$var_name='$input'"
}

# Loop principal del menú
while true; do
    show_menu
    read -p "Elige una opcion (1-3): " choice
    
    case $choice in
        1)
            echo
            echo "Ingresa las URLs de los Reels de Facebook:"
            echo "(Separa multiples URLs con comas, maximo 10)"
            echo
            read -p "URLs: " urls
            
            if [ -z "$urls" ]; then
                echo "ERROR: Debes proporcionar al menos una URL"
                continue
            fi
            
            echo
            echo "¿En que formato quieres los resultados?"
            echo "1. Excel (xlsx) - Recomendado"
            echo "2. CSV (texto plano)"
            read_with_default "Formato (1/2)" "1" "format_choice"
            
            case $format_choice in
                1) format="xlsx" ;;
                2) format="csv" ;;
                *) format="xlsx" ;;
            esac
            
            echo
            read_with_default "¿Incluir comentarios de los reels? (s/n)" "s" "comments"
            
            echo
            echo "¿Incluir datos de seguidores? (COSTO ADICIONAL)"
            echo "Nota: Esto aumenta significativamente el costo en Apify"
            read_with_default "Incluir seguidores (s/n)" "n" "followers"
            
            echo
            echo "Iniciando extraccion..."
            
            # Construir comando
            command="python3 scraper.py --urls \"$urls\" --format $format"
            if [[ "$comments" =~ ^[Nn]$ ]]; then
                command="$command --no-comments"
            fi
            if [[ "$followers" =~ ^[Ss]$ ]]; then
                command="$command --include-followers"
            fi
            
            # Ejecutar comando
            eval $command
            break
            ;;
        2)
            echo
            echo "Verificando configuracion del sistema..."
            python3 scraper.py --check-env
            break
            ;;
        3)
            echo
            echo "¡Hasta la vista!"
            exit 0
            ;;
        *)
            echo "Opcion invalida. Por favor selecciona 1-3."
            echo "Presiona Enter para continuar..."
            read -r
            ;;
    esac
done

echo
echo "============================================="
echo "¡Extraccion completada!"
echo "============================================="
echo "Los resultados se han guardado en la carpeta 'output'"
echo
echo "Presiona Enter para salir..."
read -r