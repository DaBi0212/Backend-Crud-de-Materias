# 🐍 Sistema de Gestión Escolar - API REST (Backend)

Este repositorio contiene el **Backend** del Sistema de Gestión Escolar. Es una API RESTful desarrollada con **Django** y **Django REST Framework** que gestiona la lógica de negocio, la seguridad y la persistencia de datos, sirviendo como proveedor de información para la aplicación cliente (Angular).

## ⚙️ Stack Tecnológico

* **Lenguaje:** Python 3.10+
* **Framework Web:** Django 4.x
* **API Toolkit:** Django REST Framework (DRF)
* **Autenticación:** JWT (JSON Web Tokens) vía `djangorestframework-simplejwt`
* **Base de Datos:**
  * *Desarrollo:* SQLite
  * *Producción:* PostgreSQL (Configurable)
* **Intercambio de Recursos:** `django-cors-headers` (Habilitado para comunicación con Angular)

## 🔐 Características del API

### 1. Gestión de Identidad y Acceso
* **Modelo de Usuario Extendido:** Implementación personalizada de `AbstractUser` para soportar roles específicos (`administrador`, `maestro`, `alumno`) y metadatos adicionales.
* **Seguridad:** Endpoints protegidos mediante tokens JWT (Access & Refresh).
* **Validaciones de Integridad:**
    * Unicidad estricta en campos clave (Matrícula, Email).
    * Validaciones de formato regex para documentos oficiales (CURP, RFC).

### 2. Endpoints Principales

La API expone los siguientes recursos principales:

| Método | Endpoint | Descripción | Requiere Auth |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/token/` | Login: Obtención de par de tokens (Access/Refresh). | ❌ |
| `POST` | `/api/token/refresh/` | Renovación del token de acceso. | ❌ |
| `GET` | `/api/users/` | Listado general de usuarios (con filtros por rol). | ✅ |
| `POST` | `/api/admin/` | Registro de nuevos administradores. | ✅ |
| `POST` | `/api/materias/` | Creación de materias (Valida NRC único y horarios). | ✅ |
| `GET` | `/api/total-usuarios/` | Data estadística para el Dashboard. | ✅ |

## 🚀 Instalación y Despliegue Local

Sigue estos pasos para levantar el servidor de desarrollo en tu máquina local.

### Prerrequisitos
* Python 3.8 o superior instalado.
* `pip` actualizado.

### Pasos

1.  **Clonar el repositorio:**
    ```bash
    git clone <URL_DE_TU_REPO_BACKEND>
    cd <NOMBRE_DE_LA_CARPETA>
    ```

2.  **Crear entorno virtual:**
    Es recomendable aislar las dependencias del proyecto.
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # Mac/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Migraciones de Base de Datos:**
    Genera la base de datos SQLite inicial y aplica las estructuras de tablas.
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

5.  **Crear Superusuario (Administrador):**
    Para acceder al panel de administración de Django (`/admin`).
    ```bash
    python manage.py createsuperuser
    ```

6.  **Ejecutar el servidor:**
    ```bash
    python manage.py runserver
    ```
    El API estará disponible en `http://127.0.0.1:8000/`.

## ⚙️ Configuración Adicional (CORS)

Para que el Frontend (Angular) pueda comunicarse con este Backend, asegúrate de que el origen del frontend esté permitido en `settings.py`.

```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:4200", # Puerto por defecto de Angular
]