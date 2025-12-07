### README del Backend (Django)

Crea un archivo llamado `README.md` en la raíz de tu carpeta del proyecto Django (donde está el archivo `manage.py`).

```markdown
# 🐍 Sistema de Gestión Escolar - API REST (Backend)

Backend robusto desarrollado en **Django REST Framework** que sirve como el núcleo lógico para la plataforma de gestión escolar. Maneja la autenticación, la persistencia de datos y las reglas de negocio.

## ⚙️ Tecnologías

* **Lenguaje:** Python 3.x
* **Framework:** Django 4.x
* **API Toolkit:** Django REST Framework (DRF)
* **Autenticación:** JWT (JSON Web Tokens)
* **Base de Datos:** SQLite (Dev) / PostgreSQL (Prod)
* **CORS:** `django-cors-headers` para permitir peticiones desde Angular.

## 🔐 Características del API

### 1. Autenticación y Usuarios
* **Modelo de Usuario Personalizado:** Extensión de `AbstractUser` para manejar roles (`administrador`, `maestro`, `alumno`).
* **JWT:** Endpoints para obtención y refresco de tokens.
* **Validaciones Backend:**
    * Unicidad de Matricula y Email.
    * Formato de CURP y RFC.

### 2. Endpoints Principales

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `POST` | `/api/login/` | Autenticación de usuarios. |
| `GET` | `/api/users/` | Listado general de usuarios (filtrable). |
| `POST` | `/api/admin/` | Registro de nuevos administradores. |
| `POST` | `/api/materias/` | Creación de materias (valida NRC). |
| `GET` | `/api/total-usuarios/` | Datos estadísticos para gráficas. |

## 🚀 Instalación y Despliegue

### Prerrequisitos
* Python 3.8+
* Pip / Virtualenv

### Pasos
1.  **Crear entorno virtual:**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

2.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configurar Base de Datos:**
    Realiza las migraciones para crear las tablas:
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

4.  **Crear Superusuario (Opcional):**
    ```bash
    python manage.py createsuperuser
    ```

5.  **Ejecutar el servidor:**
    ```bash
    python manage.py runserver
    ```
    El API estará disponible en `http://127.0.0.1:8000/`.

## 🛡️ Reglas de Negocio Implementadas

* **Integridad de Horarios:** El backend recibe y almacena los horarios validados previamente por el frontend, pero mantiene restricciones de integridad en BD.
* **NRC Único:** Restricción a nivel de modelo para evitar duplicidad de materias.
* **Relaciones:**
    * Un Maestro puede tener múltiples materias.
    * Una Materia pertenece a un Programa Educativo específico.

---
Desarrollado por **David** - 2025