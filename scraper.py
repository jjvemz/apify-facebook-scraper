#!/usr/bin/env python3
"""
Marco de Trabajo para Scraping de Reels de Facebook usando Apify
Soporta hasta 10 URLs de Reels de Facebook con procesamiento pandas DataFrame y exportación CSV/XLSX.
"""

import argparse
import json
import sys
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

import pandas as pd
from apify_client import ApifyClient
from dotenv import load_dotenv


class FacebookReelsScraper:
    def __init__(self, output_format: str = 'csv'):
        self._load_environment()
        self.output_format = output_format
        self.client = ApifyClient(self.api_token)
        self.output_dir = Path('output')
        self.output_dir.mkdir(exist_ok=True)
    
    def _load_environment(self):
        """Load and validate environment variables"""
        load_dotenv()
        
        self.api_token = os.getenv('APIFY_API_TOKEN')
        self.reels_actor_id = os.getenv('REELS_ACTOR_ID', 'apify/facebook-reels-scraper')
        self.comments_actor_id = os.getenv('COMMENTS_ACTOR_ID', 'apify/facebook-comments-scraper')
        self.followers_actor_id = os.getenv('FOLLOWERS_ACTOR_ID', 'apify/facebook-followers-following-scraper')
        
        if not self.api_token:
            self._show_env_setup_error()
            raise ValueError("APIFY_API_TOKEN es requerido. Por favor configúralo en tu archivo .env.")
        
        if not self.api_token.startswith('apify_api_'):
            print("Advertencia: El formato del token API puede ser incorrecto. Formato esperado: apify_api_...")
    
    def _show_env_setup_error(self):
        """Muestra mensaje de error útil para token API faltante"""
        env_file = Path('.env')
        template_file = Path('.env.template')
        
        print("\n" + "="*60)
        print("ERROR: TOKEN API DE APIFY NO ENCONTRADO")
        print("="*60)
        
        if not env_file.exists():
            print("¡Archivo .env no encontrado!")
            if template_file.exists():
                print(f"Copia '{template_file}' a '.env' y agrega tu token API")
            else:
                print("Crea un archivo .env con tu token API")
            print("\nEjemplo de contenido .env:")
            print("APIFY_API_TOKEN=apify_api_tu_token_aquí")
        else:
            print("El archivo .env existe pero APIFY_API_TOKEN falta o está vacío")
        
        print("\nPara obtener tu token API:")
        print("1. Ve a https://console.apify.com/account/integrations")  
        print("2. Copia tu token API")
        print("3. Agrégalo a tu archivo .env")
        print("\n" + "="*60)
    
    def validate_facebook_url(self, url: str) -> bool:
        """Valida si la URL es una URL de reel de Facebook"""
        try:
            parsed = urlparse(url)
            return (
                parsed.netloc in ['www.facebook.com', 'facebook.com', 'm.facebook.com'] and
                ('reel' in parsed.path.lower() or '/videos/' in parsed.path)
            )
        except Exception:
            return False
    
    def validate_urls(self, urls: List[str]) -> List[str]:
        """Valida y filtra URLs de reels de Facebook"""
        if len(urls) > 10:
            print(f"Advertencia: Se proporcionaron más de 10 URLs ({len(urls)}). Usando las primeras 10 URLs.")
            urls = urls[:10]
        
        valid_urls = []
        for i, url in enumerate(urls, 1):
            if self.validate_facebook_url(url):
                valid_urls.append(url)
            else:
                print(f"Advertencia: La URL {i} no es una URL válida de reel de Facebook: {url}")
        
        if not valid_urls:
            raise ValueError("No se proporcionaron URLs válidas de reels de Facebook.")
        
        return valid_urls
    
    def format_start_urls(self, urls: List[str]) -> List[Dict[str, str]]:
        """Formatea URLs para entrada del actor de Apify"""
        return [{"url": url} for url in urls]
    
    def scrape_reels(self, urls: List[str]) -> Optional[str]:
        """Extrae datos de reels usando el actor de Apify"""
        start_urls = self.format_start_urls(urls)
        
        run_input = {
            "startUrls": start_urls,
            "resultsLimit": 1
        }
        
        print(f"Iniciando extracción de reels para {len(urls)} URLs...")
        
        try:
            run = self.client.actor(self.reels_actor_id).call(run_input=run_input)
            return run.get('defaultDatasetId')
        except Exception as e:
            print(f"Error extrayendo reels: {e}")
            return None
    
    def scrape_comments(self, urls: List[str]) -> Optional[str]:
        """Extrae datos de comentarios usando el actor de Apify"""
        start_urls = self.format_start_urls(urls)
        
        run_input = {
            "startUrls": start_urls,
            "resultsLimit": 100
        }
        
        print(f"Iniciando extracción de comentarios para {len(urls)} URLs...")
        
        try:
            run = self.client.actor(self.comments_actor_id).call(run_input=run_input)
            return run.get('defaultDatasetId')
        except Exception as e:
            print(f"Error extrayendo comentarios: {e}")
            return None
    
    def scrape_followers(self, profile_urls: List[str]) -> Optional[str]:
        """Extrae datos de seguidores para perfiles de comentaristas usando el actor de Apify"""
        if not profile_urls:
            return None
            
        start_urls = self.format_start_urls(profile_urls)
        
        run_input = {
            "startUrls": start_urls,
            "resultsLimit": 1000  # Limitar seguidores por perfil
        }
        
        print(f"Iniciando extracción de seguidores para {len(profile_urls)} perfiles...")
        
        try:
            run = self.client.actor(self.followers_actor_id).call(run_input=run_input)
            return run.get('defaultDatasetId')
        except Exception as e:
            print(f"Error extrayendo seguidores: {e}")
            return None
    
    def extract_dataset_items(self, dataset_id: str) -> List[Dict[str, Any]]:
        """Extrae elementos del dataset de Apify"""
        try:
            items = list(self.client.dataset(dataset_id).iterate_items())
            return items
        except Exception as e:
            print(f"Error extrayendo dataset {dataset_id}: {e}")
            return []
    
    def create_url_slug(self, url: str) -> str:
        """Crea un slug seguro de nombre de archivo desde la URL"""
        slug = re.sub(r'[^\w\-_]', '_', url)
        slug = re.sub(r'_+', '_', slug)
        return slug[:50]  # Limit length
    
    def process_reel_data(self, url: str, reel_data: List[Dict], comment_data: List[Dict], 
                          follower_data: List[Dict] = None) -> pd.DataFrame:
        """Procesa y combina datos de reels, comentarios y seguidores en DataFrame"""
        print(f"Procesando datos para URL: {url}")
        print(f"Registros de reels disponibles: {len(reel_data)}")
        print(f"Registros de comentarios disponibles: {len(comment_data)}")
        
        # More flexible URL matching - try different URL formats
        reel_info = None
        for reel in reel_data:
            reel_url = reel.get('url', '') or reel.get('postUrl', '') or reel.get('link', '')
            if reel_url == url or url in reel_url or reel_url in url:
                reel_info = reel
                break
        
        comments = []
        for comment in comment_data:
            comment_url = comment.get('url', '') or comment.get('postUrl', '') or comment.get('link', '')
            if comment_url == url or url in comment_url or comment_url in url:
                comments.append(comment)
        
        print(f"Datos de reel encontrados: {bool(reel_info)}")
        print(f"Encontrados {len(comments)} comentarios")
        
        # Siempre crear al menos datos básicos incluso si no hay coincidencias específicas
        if not reel_info and not comments and reel_data:
            print("No se encontraron coincidencias de URL, usando los primeros datos de reel disponibles")
            reel_info = reel_data[0] if reel_data else {}
            comments = comment_data[:10] if comment_data else []  # Tomar los primeros 10 comentarios como muestra
        
        # Crear búsqueda de seguidores por autor
        follower_lookup = {}
        if follower_data:
            for follower_item in follower_data:
                profile_url = follower_item.get('profile_url', '')
                author_name = follower_item.get('author_name', '')
                if profile_url or author_name:
                    key = profile_url if profile_url else author_name
                    if key not in follower_lookup:
                        follower_lookup[key] = []
                    follower_lookup[key].append(follower_item)
        
        rows = []
        
        if reel_info or not comments:  # Create reel row even if no comments
            # Handle different possible field names from Apify
            base_row = {
                'url': url,
                'reel_id': reel_info.get('id', '') or reel_info.get('postId', '') or reel_info.get('videoId', ''),
                'reel_title': reel_info.get('title', '') or reel_info.get('text', '') or reel_info.get('caption', ''),
                'reel_description': reel_info.get('description', '') or reel_info.get('text', '') or reel_info.get('caption', ''),
                'reel_author': reel_info.get('author', '') or reel_info.get('ownerName', '') or reel_info.get('username', ''),
                'reel_likes': reel_info.get('likes', 0) or reel_info.get('likesCount', 0) or reel_info.get('reactions', 0),
                'reel_shares': reel_info.get('shares', 0) or reel_info.get('sharesCount', 0),
                'reel_views': reel_info.get('views', 0) or reel_info.get('viewsCount', 0) or reel_info.get('playCount', 0),
                'reel_created_at': reel_info.get('createdAt', '') or reel_info.get('timestamp', '') or reel_info.get('publishedAt', ''),
                'comment_id': '',
                'comment_author': '',
                'comment_text': '',
                'comment_likes': 0,
                'comment_replies': 0,
                'comment_created_at': '',
                'commenter_followers_count': 0,
                'commenter_following_count': 0,
                'commenter_profile_url': '',
                'follower_name': '',
                'follower_profile_url': ''
            }
            
            if comments:
                for comment in comments:
                    comment_author = comment.get('author', '') or comment.get('authorName', '') or comment.get('username', '') or comment.get('name', '')
                    comment_profile_url = comment.get('profile_url', '') or comment.get('profileUrl', '') or comment.get('authorUrl', '')
                    
                    # Get followers for this commenter
                    commenter_followers = follower_lookup.get(comment_profile_url, []) if comment_profile_url else []
                    if not commenter_followers and comment_author:
                        commenter_followers = follower_lookup.get(comment_author, [])
                    
                    if commenter_followers:
                        # Crear fila para cada seguidor
                        for follower in commenter_followers:
                            row = base_row.copy()
                            row.update({
                                'comment_id': comment.get('id', '') or comment.get('commentId', ''),
                                'comment_author': comment_author,
                                'comment_text': comment.get('text', '') or comment.get('message', '') or comment.get('content', ''),
                                'comment_likes': comment.get('likes', 0) or comment.get('likesCount', 0) or comment.get('reactions', 0),
                                'comment_replies': comment.get('replies', 0) or comment.get('repliesCount', 0),
                                'comment_created_at': comment.get('createdAt', '') or comment.get('timestamp', '') or comment.get('publishedAt', ''),
                                'commenter_followers_count': len(commenter_followers),
                                'commenter_following_count': comment.get('following_count', 0),
                                'commenter_profile_url': comment_profile_url,
                                'follower_name': follower.get('name', ''),
                                'follower_profile_url': follower.get('profile_url', '')
                            })
                            rows.append(row)
                    else:
                        # No hay datos de seguidores, solo datos de comentarios
                        row = base_row.copy()
                        row.update({
                            'comment_id': comment.get('id', ''),
                            'comment_author': comment_author,
                            'comment_text': comment.get('text', ''),
                            'comment_likes': comment.get('likes', 0),
                            'comment_replies': comment.get('replies', 0),
                            'comment_created_at': comment.get('createdAt', ''),
                            'commenter_followers_count': 0,
                            'commenter_following_count': 0,
                            'commenter_profile_url': comment_profile_url,
                            'follower_name': '',
                            'follower_profile_url': ''
                        })
                        rows.append(row)
            else:
                rows.append(base_row)
        else:
            # No hay datos de reel, procesar solo comentarios
            for comment in comments:
                comment_author = comment.get('author', '')
                comment_profile_url = comment.get('profile_url', '')
                
                commenter_followers = follower_lookup.get(comment_profile_url, []) if comment_profile_url else []
                if not commenter_followers and comment_author:
                    commenter_followers = follower_lookup.get(comment_author, [])
                
                if commenter_followers:
                    for follower in commenter_followers:
                        row = {
                            'url': url,
                            'reel_id': '',
                            'reel_title': '',
                            'reel_description': '',
                            'reel_author': '',
                            'reel_likes': 0,
                            'reel_shares': 0,
                            'reel_views': 0,
                            'reel_created_at': '',
                            'comment_id': comment.get('id', ''),
                            'comment_author': comment_author,
                            'comment_text': comment.get('text', ''),
                            'comment_likes': comment.get('likes', 0),
                            'comment_replies': comment.get('replies', 0),
                            'comment_created_at': comment.get('createdAt', ''),
                            'commenter_followers_count': len(commenter_followers),
                            'commenter_following_count': comment.get('following_count', 0),
                            'commenter_profile_url': comment_profile_url,
                            'follower_name': follower.get('name', ''),
                            'follower_profile_url': follower.get('profile_url', '')
                        }
                        rows.append(row)
                else:
                    row = {
                        'url': url,
                        'reel_id': '',
                        'reel_title': '',
                        'reel_description': '',
                        'reel_author': '',
                        'reel_likes': 0,
                        'reel_shares': 0,
                        'reel_views': 0,
                        'reel_created_at': '',
                        'comment_id': comment.get('id', ''),
                        'comment_author': comment_author,
                        'comment_text': comment.get('text', ''),
                        'comment_likes': comment.get('likes', 0),
                        'comment_replies': comment.get('replies', 0),
                        'comment_created_at': comment.get('createdAt', ''),
                        'commenter_followers_count': 0,
                        'commenter_following_count': 0,
                        'commenter_profile_url': comment_profile_url,
                        'follower_name': '',
                        'follower_profile_url': ''
                    }
                    rows.append(row)
        
        # Asegurar que siempre tengamos al menos una fila de datos
        if not rows:
            print("No se crearon filas, agregando fila de respaldo con datos básicos de URL")
            fallback_row = {
                'url': url,
                'reel_id': 'N/A',
                'reel_title': 'No se recuperaron datos',
                'reel_description': '',
                'reel_author': '',
                'reel_likes': 0,
                'reel_shares': 0,
                'reel_views': 0,
                'reel_created_at': '',
                'comment_id': '',
                'comment_author': '',
                'comment_text': '',
                'comment_likes': 0,
                'comment_replies': 0,
                'comment_created_at': '',
                'commenter_followers_count': 0,
                'commenter_following_count': 0,
                'commenter_profile_url': '',
                'follower_name': '',
                'follower_profile_url': ''
            }
            rows.append(fallback_row)
        
        print(f"Creadas {len(rows)} filas para procesamiento")
        df = pd.DataFrame(rows)
        print(f"Forma del DataFrame: {df.shape}")
        return df
    
    def save_dataframe(self, df: pd.DataFrame, filename: str):
        """Guarda DataFrame en archivo en formato especificado"""
        try:
            # Asegurar que el directorio de salida existe
            self.output_dir.mkdir(exist_ok=True)
            file_path = self.output_dir / f"{filename}.{self.output_format}"
            
            print(f"Intentando guardar en: {file_path.absolute()}")
            print(f"Forma del DataFrame: {df.shape}")
            print(f"Columnas del DataFrame: {list(df.columns)}")
            
            if self.output_format == 'xlsx':
                df.to_excel(file_path, index=False, engine='openpyxl')
            else:
                df.to_csv(file_path, index=False, encoding='utf-8')
            
            # Verificar que el archivo fue creado
            if file_path.exists():
                file_size = file_path.stat().st_size
                print(f"Guardado exitosamente: {file_path} ({file_size} bytes)")
            else:
                print(f"El archivo no fue creado: {file_path}")
                
        except Exception as e:
            print(f"Error guardando {filename}: {e}")
            print(f"Directorio de salida: {self.output_dir.absolute()}")
            print(f"El directorio existe: {self.output_dir.exists()}")
            import traceback
            traceback.print_exc()
    
    def run_scraper(self, urls: List[str], scrape_comments: bool = True, scrape_followers: bool = False):
        """Ejecución principal del scraper con procesamiento DataFrame"""
        try:
            valid_urls = self.validate_urls(urls)
            print(f"Procesando {len(valid_urls)} URLs válidas")
            
            reel_dataset_id = self.scrape_reels(valid_urls)
            if not reel_dataset_id:
                print("Falló la extracción de reels. Saliendo.")
                return
            
            print("Extrayendo datos de reels...")
            reel_data = self.extract_dataset_items(reel_dataset_id)
            print(f"Recuperados {len(reel_data)} registros de reels")
            if reel_data:
                print("Claves de datos de reel de muestra:", list(reel_data[0].keys()) if reel_data else "Sin datos")
            
            comment_data = []
            if scrape_comments:
                comment_dataset_id = self.scrape_comments(valid_urls)
                if comment_dataset_id:
                    print("Extrayendo datos de comentarios...")
                    comment_data = self.extract_dataset_items(comment_dataset_id)
                    print(f"Recuperados {len(comment_data)} registros de comentarios")
                    if comment_data:
                        print("Claves de datos de comentarios de muestra:", list(comment_data[0].keys()) if comment_data else "Sin datos")
                else:
                    print("Advertencia: Falló la extracción de comentarios, continuando solo con datos de reels.")
            
            follower_data = []
            if scrape_followers and comment_data:
                # Extraer URLs únicas de perfiles desde comentarios
                profile_urls = set()
                for comment in comment_data:
                    profile_url = comment.get('profile_url', '')
                    if profile_url:
                        profile_urls.add(profile_url)
                
                if profile_urls:
                    follower_dataset_id = self.scrape_followers(list(profile_urls))
                    if follower_dataset_id:
                        print("Extrayendo datos de seguidores...")
                        follower_data = self.extract_dataset_items(follower_dataset_id)
                    else:
                        print("Advertencia: Falló la extracción de seguidores, continuando sin datos de seguidores.")
                else:
                    print("Advertencia: No se encontraron URLs de perfiles en comentarios para extracción de seguidores.")
            
            print("Procesando datos en DataFrames...")
            all_dataframes = []
            
            for url in valid_urls:
                print(f"\n=== Procesando URL: {url} ===")
                df = self.process_reel_data(url, reel_data, comment_data, follower_data if scrape_followers else None)
                slug = self.create_url_slug(url)
                
                # Siempre guardar, incluso si está vacío (crea un archivo mostrando que no se encontraron datos)
                if not df.empty:
                    print(f"DataFrame creado exitosamente con {len(df)} filas")
                    self.save_dataframe(df, slug)
                    all_dataframes.append(df)
                else:
                    print(f"DataFrame está vacío para {url}, pero esto no debería pasar debido a la fila de respaldo")
                    # Crear DataFrame mínimo si de alguna manera sigue vacío
                    minimal_df = pd.DataFrame([{
                        'url': url,
                        'reel_id': 'ERROR',
                        'reel_title': 'Falló la recuperación de datos',
                        'reel_description': 'Verificar si la URL es válida y el actor funciona',
                        'error': 'No se recuperaron datos de Apify'
                    }])
                    self.save_dataframe(minimal_df, slug)
                    all_dataframes.append(minimal_df)
            
            if all_dataframes:
                print("Creando dataset combinado...")
                combined_df = pd.concat(all_dataframes, ignore_index=True)
                self.save_dataframe(combined_df, 'combined')
            
            print(f"\n¡Extracción completada exitosamente!")
            print(f"- Total de URLs procesadas: {len(valid_urls)}")
            print(f"- Registros de reels: {len(reel_data)}")
            print(f"- Registros de comentarios: {len(comment_data)}")
            if scrape_followers:
                print(f"- Registros de seguidores: {len(follower_data)}")
            print(f"- Archivos individuales: {len(all_dataframes)}")
            print(f"- Formato de salida: {self.output_format.upper()}")
            print(f"- Directorio de salida: {self.output_dir.absolute()}")
            
        except Exception as e:
            print(f"Error del scraper: {e}")
            sys.exit(1)


def parse_arguments():
    """Parsea argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description="Marco de Trabajo para Scraping de Reels de Facebook usando Apify (máx 10 URLs)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python scraper.py --urls "https://www.facebook.com/reel/123456789"
  python scraper.py --urls "url1,url2,url3" --format xlsx
  python scraper.py --file urls.txt --no-comments --format csv
        """
    )
    
    url_group = parser.add_mutually_exclusive_group(required=False)
    url_group.add_argument(
        '--urls', '-u',
        type=str,
        help='URLs de Reels de Facebook separadas por comas (máx 10)'
    )
    url_group.add_argument(
        '--file', '-f',
        type=str,
        help='Archivo que contiene URLs de Reels de Facebook (una por línea, máx 10)'
    )
    url_group.add_argument(
        '--check-env',
        action='store_true',
        help='Verificar configuración de entorno y token API'
    )
    url_group.add_argument(
        '--test-mode',
        action='store_true',
        help='Probar procesamiento de datos y exportación de archivos con datos ficticios (sin llamadas API)'
    )
    
    parser.add_argument(
        '--format',
        choices=['csv', 'xlsx'],
        default='csv',
        help='Formato de salida: csv o xlsx (por defecto: csv)'
    )
    
    parser.add_argument(
        '--no-comments',
        action='store_true',
        help='Omitir extracción de comentarios (solo reels)'
    )
    
    parser.add_argument(
        '--include-followers',
        action='store_true',
        help='Incluir datos de seguidores para comentaristas (mayor costo)'
    )
    
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Solo validar URLs sin extraer datos'
    )
    
    return parser.parse_args()


def load_urls_from_file(file_path: str) -> List[str]:
    """Carga URLs desde archivo de texto"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        return urls
    except FileNotFoundError:
        print(f"Error: Archivo no encontrado: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error leyendo archivo {file_path}: {e}")
        sys.exit(1)


def test_data_processing(output_format='csv'):
    """Prueba procesamiento de datos y exportación con datos ficticios"""
    print("PROBANDO PROCESAMIENTO DE DATOS")
    print("="*50)
    
    try:
        # Create test scraper instance without API calls - bypass API token check
        print("Creando instancia de scraper de prueba...")
        
        # Configurar temporalmente un token API falso para pruebas
        import os
        original_token = os.environ.get('APIFY_API_TOKEN')
        os.environ['APIFY_API_TOKEN'] = 'token_prueba_para_testing_local'
        
        scraper = FacebookReelsScraper(output_format)
        
        # Restaurar token original
        if original_token:
            os.environ['APIFY_API_TOKEN'] = original_token
        else:
            del os.environ['APIFY_API_TOKEN']
        
        # Create dummy data
        test_urls = ['https://www.facebook.com/reel/test123', 'https://www.facebook.com/reel/test456']
        
        dummy_reel_data = [
            {
                'url': 'https://www.facebook.com/reel/test123',
                'id': 'reel_123',
                'title': 'Test Reel 1',
                'description': 'This is a test reel',
                'author': 'TestUser1',
                'likes': 100,
                'shares': 10,
                'views': 1000,
                'createdAt': '2024-01-01T12:00:00Z'
            },
            {
                'url': 'https://www.facebook.com/reel/test456', 
                'id': 'reel_456',
                'title': 'Test Reel 2',
                'description': 'Another test reel',
                'author': 'TestUser2',
                'likes': 200,
                'shares': 20,
                'views': 2000,
                'createdAt': '2024-01-02T12:00:00Z'
            }
        ]
        
        dummy_comment_data = [
            {
                'url': 'https://www.facebook.com/reel/test123',
                'id': 'comment_1',
                'author': 'Commenter1',
                'text': 'Great video!',
                'likes': 5,
                'replies': 2,
                'createdAt': '2024-01-01T13:00:00Z'
            },
            {
                'url': 'https://www.facebook.com/reel/test123',
                'id': 'comment_2', 
                'author': 'Commenter2',
                'text': 'Love this content',
                'likes': 3,
                'replies': 0,
                'createdAt': '2024-01-01T14:00:00Z'
            }
        ]
        
        print(f"Probando con {len(test_urls)} URLs")
        print(f"Datos de reel ficticios: {len(dummy_reel_data)} registros")
        print(f"Datos de comentarios ficticios: {len(dummy_comment_data)} registros")
        
        # Procesar cada URL
        all_dataframes = []
        for url in test_urls:
            print(f"\n--- Procesando URL de prueba: {url} ---")
            df = scraper.process_reel_data(url, dummy_reel_data, dummy_comment_data)
            if not df.empty:
                slug = scraper.create_url_slug(url)
                scraper.save_dataframe(df, f"TEST_{slug}")
                all_dataframes.append(df)
        
        # Crear archivo de prueba combinado
        if all_dataframes:
            combined_df = pd.concat(all_dataframes, ignore_index=True)
            scraper.save_dataframe(combined_df, 'TEST_combined')
            
        print(f"\n¡Prueba completada exitosamente!")
        print(f"Revisa la carpeta 'output' para archivos de prueba")
        print(f"Creados {len(all_dataframes)} archivos individuales + 1 archivo combinado")
        
    except Exception as e:
        print(f"Prueba falló: {e}")
        import traceback
        traceback.print_exc()


def check_environment():
    """Verifica y muestra configuración del entorno"""
    print("\n" + "="*50)
    print("VERIFICACIÓN DE ENTORNO")
    print("="*50)
    
    load_dotenv()
    
    # Verificar archivo .env
    env_file = Path('.env')
    template_file = Path('.env.template')
    
    print(f"Archivo .env: {'Encontrado' if env_file.exists() else 'Faltante'}")
    print(f".env.template: {'Encontrado' if template_file.exists() else 'Faltante'}")
    
    # Verificar token API
    api_token = os.getenv('APIFY_API_TOKEN')
    if api_token:
        token_preview = f"{api_token[:12]}..." if len(api_token) > 12 else api_token
        print(f"Token API: Encontrado ({token_preview})")
        
        if not api_token.startswith('apify_api_'):
            print("⚠️  Advertencia: El formato del token puede ser incorrecto")
    else:
        print("Token API: Faltante")
    
    # Verificar IDs de actores
    reels_actor = os.getenv('REELS_ACTOR_ID', 'apify/facebook-reels-scraper')
    comments_actor = os.getenv('COMMENTS_ACTOR_ID', 'apify/facebook-comments-scraper')
    followers_actor = os.getenv('FOLLOWERS_ACTOR_ID', 'apify/facebook-followers-following-scraper')
    
    print(f"Actor de Reels: {reels_actor}")
    print(f"Actor de Comentarios: {comments_actor}")
    print(f"Actor de Seguidores: {followers_actor}")
    
    # Verificar directorio de salida
    output_dir = Path('output')
    print(f"Directorio de Salida: {'Encontrado' if output_dir.exists() else 'Se creará'}")
    
    # Verificar dependencias
    try:
        import pandas as pd
        import openpyxl
        from apify_client import ApifyClient
        print("Dependencias: Todas instaladas")
    except ImportError as e:
        print(f"Dependencias: Faltante ({e.name})")
    
    print("="*50)
    
    if not api_token:
        print("\nPróximos pasos:")
        if template_file.exists():
            print("1. Copiar .env.template a .env")
        else:
            print("1. Crear archivo .env")
        print("2. Agregar tu token API de Apify")
        print("3. Obtener token desde: https://console.apify.com/account/integrations")


def main():
    """Función principal"""
    args = parse_arguments()
    
    # Manejar comando de verificación de entorno
    if args.check_env:
        check_environment()
        return
    
    # Manejar modo de prueba
    if args.test_mode:
        test_data_processing(args.format)
        return
    
    # Validar que se proporcionen URLs o archivo cuando no se verifica entorno o prueba
    if not args.urls and not args.file:
        print("Error: Debe proporcionar --urls, --file, --check-env, o --test-mode")
        sys.exit(1)
    
    if args.urls:
        urls = [url.strip() for url in args.urls.split(',') if url.strip()]
    else:
        urls = load_urls_from_file(args.file)
    
    if not urls:
        print("Error: No se proporcionaron URLs.")
        sys.exit(1)
    
    try:
        scraper = FacebookReelsScraper(output_format=args.format)
        
        if args.validate_only:
            print("Validando URLs...")
            valid_urls = scraper.validate_urls(urls)
            print(f"URLs válidas encontradas: {len(valid_urls)}")
            for i, url in enumerate(valid_urls, 1):
                print(f"  {i}. {url}")
            return
        
        scraper.run_scraper(
            urls=urls,
            scrape_comments=not args.no_comments,
            scrape_followers=args.include_followers
        )
        
    except KeyboardInterrupt:
        print("\nExtracción interrumpida por el usuario.")
        sys.exit(1)
    except Exception as e:
        print(f"Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()