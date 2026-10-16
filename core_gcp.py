#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SEO Bot Core Module (GCP Vertex AI + WordPress integration)
Automated content creation and publishing system.
"""

import os
import json
import requests
import random
import time
import logging
from datetime import datetime
import re
from dotenv import load_dotenv

# WordPress XML-RPC
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods import media, posts
from wordpress_xmlrpc.compat import xmlrpc_client
from xmlrpc.client import Binary

# Google Cloud & Vertex AI
import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.preview.vision_models import ImageGenerationModel
from google.cloud import aiplatform, storage, secretmanager
from google.api_core import exceptions as google_exceptions

# OpenAI & Instagram
from openai import OpenAI, APIConnectionError
import instagrapi

# Fix for WordPress XML-RPC compatibility with Python 3.10+
import collections.abc
collections.Iterable = collections.abc.Iterable

# Load environment variables from .env if present
load_dotenv(override=True)

# Non-secret environment variables
PROJECT_ID = os.getenv('PROJECT_ID', '')
LOCATION = os.getenv('LOCATION', 'us-central1')
MODEL_NAME = os.getenv('MODEL_NAME', 'gemini-2.5-flash')
CATEGORYS_PLAGABOT = os.getenv('CATEGORYS_PLAGABOT', 'General, Guias, Consejos')
URL_WP_PLAGABOT = os.getenv('URL_WP_PLAGABOT', '')
BUCKET_NAME = os.getenv('BUCKET_NAME', '')


def get_secret(secret_id, version_id="latest", fallback_env_var=None):
    """Accede a un secreto de Google Secret Manager con fallback a variable de entorno."""
    project_id = os.getenv('PROJECT_ID')
    if project_id:
        try:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logging.info(f"Secret Manager no disponible para '{secret_id}' ({e}). Usando variable local.")

    if fallback_env_var:
        return os.getenv(fallback_env_var, '')
    return ''


# Load secret credentials with fallback
USER_WP_PLAGABOT = get_secret('WP_USER', fallback_env_var='USER_WP_PLAGABOT') or os.getenv('USER_WP_PLAGABOT', '')
PASS_WP_PLAGABOT = get_secret('WP_PASS', fallback_env_var='PASS_WP_PLAGABOT') or os.getenv('PASS_WP_PLAGABOT', '')
OPENAIKEY_PLAGBOT = get_secret('OPENAI_KEY', fallback_env_var='OPENAIKEY_PLAGBOT') or os.getenv('OPENAIKEY_PLAGBOT', '')
INSTA_USER = get_secret('INSTA_USER', fallback_env_var='INSTAGRAM_USER') or os.getenv('INSTAGRAM_USER', '')
INSTA_PASS = get_secret('INSTA_PASS', fallback_env_var='INSTAGRAM_PASS') or os.getenv('INSTAGRAM_PASS', '')


def obtainTitles():
    """Obtiene la lista de títulos de posts existentes en WordPress para evitar duplicados."""
    if not URL_WP_PLAGABOT or not USER_WP_PLAGABOT or not PASS_WP_PLAGABOT:
        print("Advertencia: Configuración de WordPress incompleta. No se pueden obtener títulos previas.")
        return []

    try:
        clientWP = Client(URL_WP_PLAGABOT, USER_WP_PLAGABOT, PASS_WP_PLAGABOT)
        print("Conexión a WordPress exitosa.")
        list_posts = clientWP.call(posts.GetPosts({'number': 300}))
        list_utf8 = [post.title for post in list_posts if getattr(post, 'title', None)]
        print(f"Títulos obtenidos de WordPress: {len(list_utf8)}")
        return list_utf8
    except Exception as e:
        print(f"Error al obtener los títulos de WordPress: {e}")
        return []


def connectToAssistant():
    """Genera contenido optimizado para SEO usando el modelo Vertex AI Gemini."""
    print("Inicializando conexión con Vertex AI...")

    categorias = [c.strip() for c in CATEGORYS_PLAGABOT.split(',') if c.strip()]
    categoria_seleccionada = random.choice(categorias) if categorias else "General"
    print(f"Categoría seleccionada: {categoria_seleccionada}")

    titulos = obtainTitles()

    business_name = os.getenv('BUSINESS_NAME', 'Nuestra Empresa')
    target_location = os.getenv('SEO_TARGET_LOCATION', 'nuestra región')
    target_urls = os.getenv('TARGET_URLS', 'https://ejemplo.com/')
    pricing_info = os.getenv('PRICING_INFO', 'Servicios profesionales con presupuestos personalizados.')

    try:
        print(f"Cargando modelo generativo: {MODEL_NAME}")
        model = GenerativeModel(MODEL_NAME)

        prompt = f"""
Eres un experto escritor técnico y ameno, especialista en redacción web y posicionamiento SEO.
Tus objetivos principales son:
1. Generar un título único que no exista en la lista de títulos previos.
2. Crear un artículo de blog entre 1.000 y 1.500 palabras, optimizado para SEO, bien redactado y ameno para los lectores.

Información del negocio y contexto:
- Nombre de la marca / negocio: {business_name}
- Ubicación / Área objetivo SEO: {target_location}
- Enlaces estratégicos a incluir: {target_urls}
- Información de precios / ofertas: {pricing_info}

Instrucciones de formato y estilo:
- Utiliza código HTML directo para estructurar el contenido (h2, h3, p, ul, li). NO utilices Markdown.
- La etiqueta HTML más grande permitida en el cuerpo es <h2>.
- El título debe ser único e impactante.
- Estructura: Introducción atractiva, desarrollo estructurado en secciones con subtítulos claros y conclusión.
- PROHIBIDO EL USO DE MARKDOWN: No utilices nunca asteriscos (`*`) ni numerales (`#`) dentro del texto.

Responde ÚNICAMENTE en formato JSON válido con esta estructura exacta:
{{
  "title": "Tu título aquí",
  "post": "Tu contenido HTML aquí"
}}

Información de entrada:
- Títulos previamente publicados (NO repetir): {json.dumps(titulos)}
- Categoría seleccionada: {categoria_seleccionada}
"""

        print("Generando contenido con el modelo de Vertex AI...")
        response = model.generate_content(
            contents=prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        print("Contenido generado correctamente.")
        return response.text
    except Exception as e:
        print(f"Error al generar contenido con Vertex AI: {e}")
        return None


def parseResponse(response_text):
    """Procesa y valida la respuesta JSON devuelta por el modelo IA."""
    if not response_text:
        return None, None

    print("Iniciando análisis y limpieza de la respuesta JSON...")
    clean_text = response_text.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(clean_text, strict=False)
        return data.get("title"), data.get("post") or data.get("content")
    except json.JSONDecodeError:
        print("JSON con imperfecciones de formato. Intentando recuperación...")
        fixed_text = re.sub(r'(?<!\\)"(?![:,\}\]])', r'\"', clean_text)
        try:
            data = json.loads(fixed_text, strict=False)
            return data.get("title"), data.get("post") or data.get("content")
        except Exception as e:
            print(f"Estrategia de respaldo Regex para extraer JSON: {e}")
            t_match = re.search(r'"title":\s*"(.*?)"', clean_text, re.DOTALL)
            p_match = re.search(r'(?:"post"|"content"):\s*"(.*?)"', clean_text, re.DOTALL)
            if t_match and p_match:
                title = t_match.group(1).replace('\\"', '"')
                post = p_match.group(1).replace('\\"', '"').replace('\\n', '\n')
                return title, post

    return None, None


def downloadImage(title, image_bytes):
    """Sube los bytes de una imagen a Google Cloud Storage y retorna la URL pública."""
    if not BUCKET_NAME:
        print("BUCKET_NAME no configurado. Omitiendo subida a Cloud Storage.")
        return None

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = re.sub(r'[^a-zA-Z0-9_]', '_', title).lower()
        blob_name = f"temp_images/{safe_title}_{timestamp}.png"

        blob = bucket.blob(blob_name)
        blob.upload_from_string(image_bytes, content_type="image/png")
        blob.make_public()

        public_url = blob.public_url
        print(f"Imagen subida a Cloud Storage: {public_url}")
        return public_url
    except Exception as e:
        print(f"Error al guardar la imagen en Cloud Storage: {e}")
        return None


def createImage(title):
    """Genera una imagen ilustrativa en alta resolución usando Vertex AI Imagen 3."""
    print("Iniciando generación de imagen con Imagen 3...")
    prompt_image = f"Genera una imagen fotorrealista de alta calidad para ilustrar un artículo de blog sobre: {title}. La imagen no debe contener letras ni texto."

    try:
        os.makedirs("images", exist_ok=True)
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        images = model.generate_images(
            prompt=prompt_image,
            number_of_images=1,
            language="es",
            aspect_ratio="1:1"
        )

        safe_title = re.sub(r'[^a-zA-Z0-9_]', '_', title)
        image_path = f"images/{safe_title}.png"
        images[0].save(location=image_path, include_generation_parameters=False)
        print(f"Imagen generada con éxito en {image_path}")
        return image_path
    except Exception as e:
        print(f"Error al crear la imagen con Imagen 3: {e}")
        return None


def newPost(title, post_content, categoria_seleccionada, image_url):
    """Crea y publica la entrada en WordPress con su imagen destacada."""
    print(f"Creando nuevo post en WordPress: '{title}'")

    if not title or not post_content:
        raise ValueError("El título y el contenido del post no pueden estar vacíos.")

    if not URL_WP_PLAGABOT or not USER_WP_PLAGABOT or not PASS_WP_PLAGABOT:
        print("Error: Credenciales de WordPress no configuradas.")
        return None

    try:
        client = Client(URL_WP_PLAGABOT, USER_WP_PLAGABOT, PASS_WP_PLAGABOT)
    except Exception as e:
        print(f"Error de conexión con WordPress: {e}")
        return None

    image_id = None
    if image_url and os.path.exists(image_url):
        try:
            with open(image_url, "rb") as img_file:
                data = {
                    'name': f"{title}.png",
                    'type': 'image/png',
                    'bits': Binary(img_file.read())
                }
            upload_response = client.call(media.UploadFile(data))
            if upload_response and 'id' in upload_response:
                image_id = upload_response['id']
                print(f"Imagen subida a WordPress con ID de medio: {image_id}")
        except Exception as e:
            print(f"Error al subir imagen a WordPress: {e}")

    tags_config = os.getenv('WP_POST_TAGS', 'SEO, Blog, Consejos, Guía')
    tags_list = [t.strip() for t in tags_config.split(',') if t.strip()]

    try:
        post = WordPressPost()
        post.title = title
        post.content = post_content
        post.terms_names = {
            'post_tag': tags_list,
            'category': [categoria_seleccionada]
        }
        if image_id:
            post.thumbnail = image_id
        post.post_status = 'publish'

        post_id = client.call(posts.NewPost(post))
        print(f"Post publicado con éxito en WordPress. ID: {post_id}")
        return post_id
    except Exception as e:
        print(f"Error al publicar entrada en WordPress: {e}")
        return None


def newPhoto(title, image_url):
    """Publica opcionalmente la imagen y título en Instagram."""
    if not image_url or not INSTA_USER or not INSTA_PASS:
        print("Configuración de Instagram no disponible. Omitiendo publicación.")
        return

    try:
        print("Iniciando publicación en Instagram...")
        cl_insta = instagrapi.Client()
        cl_insta.login(INSTA_USER, INSTA_PASS)

        response_img = requests.get(image_url)
        response_img.raise_for_status()

        temp_image_path = "/tmp/temp_image_for_insta.jpg"
        with open(temp_image_path, "wb") as f:
            f.write(response_img.content)

        caption = f"{title}\n\n#SEO #DigitalMarketing #AIContent #Automation"
        cl_insta.photo_upload(path=temp_image_path, caption=caption)
        print("Imagen publicada con éxito en Instagram.")
    except Exception as e:
        print(f"Error al publicar en Instagram: {e}")
