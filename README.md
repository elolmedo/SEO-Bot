# SEO Bot 🤖📝

Una herramienta automatizada en Python para la **generación y publicación autónoma de artículos de blog optimizados para SEO** en sitios WordPress utilizando Inteligencia Artificial (Google Cloud Vertex AI Gemini 2.5 y modelos fotorrealistas Imagen 3 / OpenAI DALL-E 3).

---

## 🚀 ¿Qué problema resuelve el proyecto?

- **Automatización de contenidos SEO:** Genera de forma continua artículos extensos (1.000 - 1.500 palabras), estructurados en HTML, ricos en contexto y optimizados para palabras clave específicas.
- **Evita contenido repetido:** Consulta automáticamente las publicaciones previas de WordPress para asegurar que los títulos e ideas generadas sean 100% únicos.
- **Imágenes destacadas automáticas:** Crea imágenes en alta resolución mediante modelos de IA sin necesidad de bancos de imágenes o edición manual.
- **Cero costes de licencias pesadas:** Diseñado para ejecutarse eficientemente en entornos Serverless (Google Cloud Functions, Cloud Run Jobs o ejecución local programada con `cron`).

---

## 🛠️ Stack Tecnológico y Prerrequisitos

### Stack Tecnológico
- **Lenguaje:** Python 3.10+
- **Modelos IA:** Google Vertex AI (`gemini-2.5-flash`, `imagen-3.0-generate-001`) / OpenAI (`dall-e-3`)
- **Integración CMS:** `python-wordpress-xmlrpc` (API XML-RPC de WordPress)
- **Gestión de Secretos:** Google Cloud Secret Manager / `python-dotenv`
- **Redes Sociales (Opcional):** `instagrapi` (publicación automática en Instagram)

### Prerrequisitos
- Python 3.10 o superior.
- Una cuenta activa en Google Cloud Platform (GCP) con la API de Vertex AI habilitada.
- Un sitio WordPress con la API XML-RPC o contraseñas de aplicación habilitadas.

---

## ⚙️ Configuración de Variables de Entorno

SEO Bot admite la carga de variables desde un archivo `.env` para ejecución local, o desde **Google Cloud Secret Manager** cuando se despliega en Cloud Run / Cloud Functions.

### 1. Crear el archivo `.env`
Copia la plantilla `.env.example` para crear tu entorno local:
```bash
cp .env.example .env
```

### 2. Variables Principales

| Variable | Descripción | Ejemplo / Valor |
| :--- | :--- | :--- |
| `USER_WP_PLAGABOT` | Usuario de WordPress con permisos de edición | `admin_seo` |
| `PASS_WP_PLAGABOT` | Contraseña de aplicación de WordPress | `xxxx xxxx xxxx xxxx` |
| `URL_WP_PLAGABOT` | URL del endpoint XML-RPC de WordPress | `https://mi-sitio.com/xmlrpc.php` |
| `PROJECT_ID` | ID de proyecto en Google Cloud | `mi-proyecto-gcp` |
| `LOCATION` | Región GCP de Vertex AI | `us-central1` |
| `MODEL_NAME` | Modelo de Gemini a utilizar | `gemini-2.5-flash` |
| `CATEGORYS_PLAGABOT` | Lista de categorías separadas por coma | `Tecnología, Marketing, Guías` |
| `BUSINESS_NAME` | Nombre de la marca o negocio | `Mi Empresa SEO` |
| `SEO_TARGET_LOCATION` | Ciudad o región objetivo para SEO local | `Madrid, España` |
| `TARGET_URLS` | URLs estratégicas a enlazar en los artículos | `https://mi-sitio.com/contacto/` |
| `PRICING_INFO` | Tarifas u ofertas a mencionar en los artículos | `Servicios desde 100€` |

---

## ⚡ Instalación y Despliegue Local (Quickstart)

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/seo-bot.git
cd seo-bot
```

### 2. Crear un entorno virtual e instalar dependencias
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Autenticación con Google Cloud (Local)
Si ejecutas el bot localmente, inicia sesión con Google Cloud SDK:
```bash
gcloud auth application-default login
```
O coloca tu Service Account JSON siguiendo el formato de `gcp-key.json.template`.

### 4. Ejecución manual
```bash
python3 main.py
```

---

## 🏗️ Esquema de Arquitectura y Flujo de Trabajo

```
+-------------------------------------------------------------------------+
|                               SEO BOT                                   |
+-------------------------------------------------------------------------+
                                     |
    1. Consulta posts previas        v        2. Petición de contenido
+-----------------------+   +-------------------+   +--------------------+
|   WordPress XML-RPC   |---|     main.py       |-->|  Vertex AI Gemini  |
| (Títulos existentes)  |   | (Lógica Bot SEO)  |   |  (Genera texto)    |
+-----------------------+   +-------------------+   +--------------------+
                                     |
                                     v
                           3. Generación Imagen
                            +-----------------+
                            | Vertex Imagen 3 |
                            +-----------------+
                                     |
                                     v 4. Publicación automática
                            +-----------------+
                            |  Post WordPress |
                            |   + Imagen ID   |
                            +-----------------+
```

---

## 🔒 Licencia y Uso Ético

Este proyecto está bajo la licencia **GNU Affero General Public License v3 (AGPL-3.0)**. 

> **Aviso de Uso Responsable:**
> SEO Bot ha sido desarrollado exclusivamente con fines educativos, de automatización legítima y optimización SEO ética. Se insta a los usuarios a respetar las directrices de los motores de búsqueda, evitar prácticas de spam engañoso y garantizar la calidad del contenido publicado.
