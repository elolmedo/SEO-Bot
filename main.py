#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SEO Bot - Main Execution Entry Point
Automates WordPress article creation and publishing using Google Cloud Vertex AI (Gemini + Imagen 3).
"""

import os
import random
import logging
from google.cloud import aiplatform
from core_gcp import (
    connectToAssistant,
    parseResponse,
    createImage,
    newPost,
    CATEGORYS_PLAGABOT,
    PROJECT_ID,
    LOCATION
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def run_seo_bot(event=None, context=None):
    """
    Main entry point for local execution or Cloud Function / Cloud Run trigger.
    """
    print("==================================================")
    print("🤖 SEO BOT: INICIANDO PROCESO AUTOMÁTICO DE PUBLICACIÓN")
    print("==================================================")

    if PROJECT_ID and LOCATION:
        try:
            aiplatform.init(project=PROJECT_ID, location=LOCATION)
            print(f"Vertex AI inicializado (Proyecto: {PROJECT_ID}, Ubicación: {LOCATION})")
        except Exception as e:
            print(f"Advertencia al inicializar aiplatform: {e}")

    # --- PASO 1: Generación de Texto con Gemini ---
    print("\n[PASO 1/3] Generando contenido de texto con Google Vertex AI...")
    response_text = connectToAssistant()
    title, post_content = parseResponse(response_text)

    if not title or not post_content:
        raise ValueError("El título o contenido devuelto por la IA está vacío. Abortando.")

    print(f"✅ Título generado: '{title}'")

    # --- PASO 2: Generación de Imagen con Imagen 3 ---
    print("\n[PASO 2/3] Generando imagen en alta resolución con Imagen 3...")
    image_path = createImage(title)

    if not image_path:
        print("⚠️ No se pudo generar la imagen. Se procederá a publicar sin imagen destacada personal de Imagen 3.")

    # --- PASO 3: Publicación en WordPress ---
    print("\n[PASO 3/3] Publicando en WordPress...")
    categorias = [c.strip() for c in CATEGORYS_PLAGABOT.split(',') if c.strip()]
    categoria_seleccionada = random.choice(categorias) if categorias else "General"

    post_id = newPost(title, post_content, categoria_seleccionada, image_path)

    if post_id:
        print(f"\n🎉 ¡Proceso completado con éxito! Post publicado con ID: {post_id}")
    else:
        print("\n❌ Error en el proceso de publicación en WordPress.")


if __name__ == "__main__":
    try:
        run_seo_bot()
    except Exception as e:
        logging.error(f"Error crítico en la ejecución de SEO Bot: {e}", exc_info=True)
