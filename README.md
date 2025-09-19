# Santolina - Página Web de Bienestar Integral

## Descripción

Santolina es la página web oficial del emprendimiento de bienestar integral que ofrece servicios especializados en nutrición, terapias alternativas y productos naturales. La página está diseñada para mostrar los servicios disponibles y permitir a los clientes agendar turnos de manera fácil y eficiente.

## Instalación y Configuración

### Inicialización de la base de datos

Para inicializar la base de datos me ubico en la carpeta y ejecuto:

```bash
python app/initialize_db.py
```
### Inicializaicón de datos

En los archivos init_db_data.sql se encuentran las consultas para inicializar algunos datos en la base de datos. Se puede correr desde un gestor de base de datos como pgAdmin o desde la consola de psql.

### Ejecutar el Proyecto

Para correr el proyecto me ubico en la carpeta y ejecuto:

```bash
uvicorn app.main:app --reload
```

### Configuración de Gmail API
Los mails se envian usando una cuenta de Gmail por lo que se debe crear una cuenta de correo electrónico y configurar la API de Gmail.

Para que el sistema de envío de emails funcione correctamente, es necesario configurar Gmail API:

#### 1. Crear Proyecto en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita **Gmail API** en la sección "APIs y servicios"

#### 2. Crear Credenciales de Escritorio

1. Ve a "Credenciales" → "Crear credenciales" → "ID de cliente OAuth 2.0"
2. Selecciona **"Aplicación de escritorio"** (no usar aplicación web)
3. Guarda el `client_id` y `client_secret` generados

#### 3. Configurar Variables de Entorno

Agrega las siguientes variables a tu archivo `.env`:

```env
GMAIL_CLIENT_ID=tu_client_id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=tu_client_secret
GMAIL_FROM_EMAIL=tu_cuenta_de_notificaciones@gmail.com
```

#### 4. Obtener Refresh Token

1. Ejecuta el script para obtener el refresh token:
   ```bash
   python app/get_refresh_token.py
   ```

2. Se abrirá una ventana del navegador de Google
3. Haz clic en "Continuar" para autorizar la aplicación
4. Una vez verificado, aparecerá el `refresh_token` en la consola

#### 5. Completar Configuración

Agrega el refresh token obtenido al archivo `.env`:

```env
GMAIL_REFRESH_TOKEN=tu_refresh_token_obtenido
```

#### Variables de Entorno Completas

Tu archivo `.env` debe contener:

```env
# Gmail API Configuration
GMAIL_CLIENT_ID=tu_client_id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=tu_client_secret
GMAIL_REFRESH_TOKEN=tu_refresh_token_obtenido
GMAIL_FROM_EMAIL=tu_cuenta_de_notificaciones@gmail.com

# Otras configuraciones...
```

Una vez configurado, el sistema renovará automáticamente los tokens de acceso sin intervención manual.

### Configuración de Inicio de Sesión con Google

Para permitir que los usuarios inicien sesión con sus cuentas de Google, es necesario configurar Google OAuth:

#### 1. Habilitar APIs Necesarias

En el mismo proyecto de Google Cloud Console:

1. Ve a "APIs y servicios" → "Biblioteca"
2. Busca y habilita las siguientes APIs:
   - **Google+ API** (para obtener información del perfil)
   - **People API** (para acceder a datos del usuario)
   - **OAuth2 API** (si está disponible)

#### 2. Crear Credenciales de Aplicación Web

1. Ve a "Credenciales" → "Crear credenciales" → "ID de cliente OAuth 2.0"
2. Selecciona **"Aplicación web"** (diferente a las credenciales de Gmail)
3. Configura las **URI de redirección autorizadas**:

**Para desarrollo local:**
```
http://localhost:8000/auth/google/callback
```

**Para producción:**
```
http://tu_dominio.com/auth/google/callback
```

4. Guarda el `client_id` y `client_secret` generados

#### 3. Configurar Variables de Entorno para OAuth

Agrega las siguientes variables a tu archivo `.env`:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=tu_oauth_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu_oauth_client_secret
```

**Nota:** Se recomienda usar la misma cuenta de Gmail para ambas configuraciones (notificaciones y OAuth) para simplificar la gestión de credenciales.