# Marco de Trabajo para Scraping de Reels de Facebook

Un marco de trabajo integral en Python para extraer datos de Reels de Facebook usando Apify. Soporta hasta 10 URLs con exportación de datos estructurados a formatos CSV o Excel. Ahora incluye recolección de datos de seguidores/seguidos para análisis de redes sociales mejorados.

## ✨ Características Principales

- **Recolección de Datos Multi-nivel**: Extrae reels, comentarios y redes de seguidores
- **Formatos de Salida Flexibles**: Exporta a CSV o Excel
- **Análisis de Redes Sociales**: Rastrea seguidores de comentaristas para información de audiencia
- **Procesamiento Consciente de Costos**: Scraping opcional de seguidores para gestionar costos
- **Procesamiento por Lotes**: Maneja múltiples URLs de manera eficiente
- **Validación de Datos**: Validación de URLs incorporada y manejo de errores

## 🚀 Inicio Rápido

### Requisitos Previos

- Python 3.10 o superior
- pip (instalador de paquetes de Python)
- Cuenta de Apify con token API

### Instalación

1. **Clona o descarga** este proyecto a tu máquina local

2. **Ejecuta el lanzador por lotes** (Windows):
   ```bash
   run_scraper.bat
   ```
   El lanzador automáticamente:
   - Crea un entorno virtual
   - Instala las dependencias requeridas
   - Te guía a través del proceso de configuración

3. **Instalación manual** (Alternativa):
   ```bash
   # Crear entorno virtual
   python -m venv venv
   
   # Activar entorno virtual
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   
   # Instalar dependencias
   pip install -r requirements.txt
   ```

## 🔑 Configuración de Clave API

### Paso 1: Obtén tu Token API de Apify

1. **Crea una cuenta de Apify** en [https://apify.com](https://apify.com)
2. **Navega a Configuración** → **Integraciones** → **Tokens API**
3. **Copia tu token API** (comienza con `apify_api_...`)

### Paso 2: Crea Variables de Entorno

Crea un archivo `.env` en el directorio raíz del proyecto:

```bash
# Requerido: Tu token API de Apify
APIFY_API_TOKEN=apify_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Opcional: IDs de actores personalizados (usa valores por defecto si no se especifica)
REELS_ACTOR_ID=apify/facebook-reels-scraper
COMMENTS_ACTOR_ID=apify/facebook-comments-scraper
FOLLOWERS_ACTOR_ID=apify/facebook-followers-following-scraper
```

### Paso 3: Plantilla de Archivo de Entorno

Copia esta plantilla para crear tu archivo `.env`:

```env
# =============================================================================
# CONFIGURACIÓN DE APIFY
# =============================================================================

# Tu token API de Apify (REQUERIDO)
# Obtén esto desde: https://console.apify.com/account/integrations
APIFY_API_TOKEN=tu_token_api_de_apify_aquí

# IDs de actores para scraping (OPCIONAL - usa valores por defecto si no se especifica)
REELS_ACTOR_ID=apify/facebook-reels-scraper
COMMENTS_ACTOR_ID=apify/facebook-comments-scraper
FOLLOWERS_ACTOR_ID=apify/facebook-followers-following-scraper

# =============================================================================
# VALORES DE EJEMPLO
# =============================================================================
# APIFY_API_TOKEN=apify_api_1234567890abcdefghijklmnopqrstuvwxyz
# REELS_ACTOR_ID=apify/facebook-reels-scraper
# COMMENTS_ACTOR_ID=apify/facebook-comments-scraper
# FOLLOWERS_ACTOR_ID=apify/facebook-followers-following-scraper
```

## 📊 Uso

### Usando el Lanzador por Lotes (Recomendado)

Simplemente ejecuta el archivo por lotes y sigue el menú interactivo:

```bash
run_scraper.bat
```

### Uso por Línea de Comandos

#### Ejemplos Básicos

```bash
# Extraer una sola URL a CSV
python scraper.py --urls "https://www.facebook.com/reel/1234567890"

# Extraer múltiples URLs a Excel
python scraper.py --urls "url1,url2,url3" --format xlsx

# Extraer desde archivo sin comentarios
python scraper.py --file urls.txt --no-comments

# Incluir datos de seguidores (mayor costo)
python scraper.py --urls "url1,url2" --include-followers

# Validar URLs únicamente (sin scraping)
python scraper.py --urls "url1,url2" --validate-only
```

#### Ejemplos Avanzados

```bash
# Formato CSV con comentarios (por defecto)
python scraper.py --urls "https://www.facebook.com/reel/123,https://www.facebook.com/reel/456" --format csv

# Formato Excel sin comentarios
python scraper.py --file mis_urls.txt --format xlsx --no-comments

# Incluir datos de seguidores con salida Excel
python scraper.py --urls "url1,url2" --format xlsx --include-followers

# Solo validar URLs antes del scraping
python scraper.py --urls "https://www.facebook.com/reel/789" --validate-only
```

### Opciones de Línea de Comandos

| Opción | Corto | Descripción | Ejemplo |
|--------|-------|-------------|---------|
| `--urls` | `-u` | URLs separadas por comas (máx 10) | `--urls "url1,url2"` |
| `--file` | `-f` | Archivo con URLs (una por línea) | `--file urls.txt` |
| `--format` | | Formato de salida: csv o xlsx | `--format xlsx` |
| `--no-comments` | | Omitir scraping de comentarios | `--no-comments` |
| `--include-followers` | | Incluir datos de seguidores para comentaristas | `--include-followers` |
| `--validate-only` | | Solo validar URLs | `--validate-only` |

## 📁 Estructura de Archivos

```
directorio_proyecto/
├── scraper.py              # Script principal del scraper
├── requirements.txt        # Dependencias de Python  
├── run_scraper.bat        # Lanzador Windows
├── .env                   # Variables de entorno (tú creas este)
├── README.md             # Este archivo
├── output/               # Directorio de resultados (se crea automáticamente)
│   ├── url_slug_1.csv    # Resultados de URL individual
│   ├── url_slug_2.xlsx   # Resultados de URL individual  
│   └── combined.csv      # Dataset combinado
└── venv/                 # Entorno virtual (se crea automáticamente)
```

## 📊 Formato de Salida

### Estructura de Datos

Cada archivo exportado contiene las siguientes columnas:

#### Información de Reel
- `url` - URL original del Reel de Facebook
- `reel_id` - Identificador único del reel
- `reel_title` - Título/caption del reel
- `reel_description` - Descripción del reel
- `reel_author` - Nombre del autor/creador
- `reel_likes` - Número de likes
- `reel_shares` - Número de compartidos
- `reel_views` - Número de visualizaciones
- `reel_created_at` - Timestamp de creación

#### Información de Comentarios (si está habilitado)
- `comment_id` - Identificador único del comentario
- `comment_author` - Nombre del autor del comentario
- `comment_text` - Contenido del comentario
- `comment_likes` - Cantidad de likes del comentario
- `comment_replies` - Número de respuestas
- `comment_created_at` - Timestamp del comentario

#### Información de Seguidores (si está habilitado)
- `commenter_followers_count` - Total de seguidores del comentarista
- `commenter_following_count` - Total de seguidos del comentarista
- `commenter_profile_url` - URL del perfil del comentarista
- `follower_name` - Nombre del seguidor individual
- `follower_profile_url` - URL del perfil del seguidor individual

### Archivos de Salida

1. **Archivos individuales**: `{url_slug}.{csv|xlsx}` - Datos para cada URL
2. **Archivo combinado**: `combined.{csv|xlsx}` - Todos los datos fusionados
3. **Ubicación**: directorio `output/`

## 🔧 Solución de Problemas

### Problemas Comunes

#### 1. Error de Token API Faltante
```
ValueError: APIFY_API_TOKEN es requerido. Por favor configúralo en tu archivo .env.
```
**Solución**: Crea el archivo `.env` con tu token API de Apify (ver instrucciones de configuración arriba)

#### 2. Advertencia de URLs Inválidas
```
Advertencia: La URL X no es una URL válida de reel de Facebook: [url]
```
**Solución**: Asegúrate de que las URLs sean Reels de Facebook (contengan 'reel' o '/videos/' en la ruta)

#### 3. Error de Importación
```
ModuleNotFoundError: No module named 'pandas'
```
**Solución**: Instala los requisitos: `pip install -r requirements.txt`

#### 4. Error de Permisos en Windows
**Solución**: Ejecuta el Símbolo del Sistema como Administrador o usa el lanzador por lotes

### Requisitos de Formato de URL

✅ **URLs Válidas de Reels de Facebook:**
- `https://www.facebook.com/reel/1234567890`
- `https://facebook.com/usuario/videos/1234567890`
- `https://m.facebook.com/reel/1234567890`

❌ **URLs Inválidas:**
- Videos de YouTube
- Reels de Instagram  
- Dominios que no sean de Facebook
- Posts regulares de Facebook (no reels/videos)

### Depuración de Variables de Entorno

Para verificar si las variables de entorno se cargan correctamente:

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Token API cargado:', bool(os.getenv('APIFY_API_TOKEN')))"
```

## 💰 Consideraciones de Costo

- Apify cobra por ejecución de actor y volumen de datos
- Costo estimado: ~$3.16 por 1000 reels
- **Los datos de seguidores incrementan significativamente los costos** - usa `--include-followers` con cuidado
- Usa la bandera `--validate-only` para verificar URLs antes del scraping
- Considera usar `--no-comments` para reducir costos
- El scraping de seguidores procesa el perfil de cada comentarista por separado

## ⚖️ Directrices Legales y Éticas

- **Solo extrae contenido público** - respeta la configuración de privacidad
- **Cumple con GDPR/CCPA** - maneja los datos personales de manera responsable  
- **Respeta los límites de velocidad** - evita sobrecargar los servidores de Facebook
- **Sigue los Términos de Servicio de Facebook**
- **Usa proxies residenciales** si haces scraping a escala

## 🛠️ Configuración Avanzada

### Actores de Apify Utilizados

Este marco de trabajo integra tres actores especializados de Apify:

1. **Actor de Reels** (`apify/facebook-reels-scraper`): Extrae información básica del reel (título, autor, likes, visualizaciones, etc.)
2. **Actor de Comentarios** (`apify/facebook-comments-scraper`): Recolecta comentarios y datos de comentaristas
3. **Actor de Seguidores** (`apify/facebook-followers-following-scraper`): Recopila datos de seguidores/seguidos para comentaristas

### IDs de Actores Personalizados

Puedes usar diferentes actores de Apify configurando estas variables de entorno:

```env
REELS_ACTOR_ID=tu-actor-personalizado/reel-scraper
COMMENTS_ACTOR_ID=tu-actor-personalizado/comment-scraper
FOLLOWERS_ACTOR_ID=tu-actor-personalizado/followers-scraper
```

### Procesamiento por Lotes

Para procesar muchas URLs de manera eficiente, considera:
1. Dividir listas grandes de URLs en lotes más pequeños
2. Usar el actor `useful-tools/batch-runner` para procesamiento paralelo
3. Implementar lógica de reintento para URLs fallidas

## 📞 Soporte

Para problemas con:
- **Este marco de trabajo**: Consulta la sección de solución de problemas o crea un issue
- **Plataforma Apify**: Contacta [Soporte de Apify](https://help.apify.com/)
- **Bloqueo de Facebook**: Considera usar proxies residenciales

## 🔄 Actualizaciones

Para actualizar el marco de trabajo:
1. Descarga la versión más reciente
2. Ejecuta `pip install -r requirements.txt` para actualizar dependencias
3. Revisa este README para nuevas opciones de configuración

---

**¡Feliz Scraping! 🎯**