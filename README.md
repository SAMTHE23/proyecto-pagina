# Autobots

Sitio web de un concesionario de vehículos hecho con **FastAPI**. Incluye un catálogo con búsqueda, la ficha de cada vehículo, una página de servicios, un formulario de contacto y una API REST para administrar los vehículos.


## Contenido

1. [Características](#características)
2. [Tecnologías](#tecnologías)
3. [Estructura del proyecto](#estructura-del-proyecto)
4. [Inicio rápido](#inicio-rápido)
5. [Variables de entorno](#variables-de-entorno)
6. [API de vehículos](#api-de-vehículos)
7. [Pruebas](#pruebas)
8. [Despliegue en Azure](#despliegue-en-azure)
9. [Arquitectura y conceptos de la entrega](#arquitectura-y-conceptos-de-la-entrega)

## Características

| Ruta | Qué muestra |
| --- | --- |
| `/` | Inicio con vehículos destacados. |
| `/catalogo` | Catálogo con búsqueda por marca, modelo o tipo (`?q=`). |
| `/catalogo/{vehiculo_id}` | Ficha del vehículo con su especificación. |
| `/servicios` | Servicios del taller. |
| `/contacto` | Formulario para pedir información, cotizar un vehículo o agendar mantenimiento. |
| `/docs` | Documentación interactiva de la API (Swagger UI). |

Los precios se muestran en pesos colombianos (COP). Los vehículos sin precio registrado muestran **Consultar precio**, y las especificaciones opcionales (`motor`, `transmision`, `combustible`) aparecen solo cuando tienen datos.

Los precios y las especificaciones de ejemplo son ilustrativos. Reemplázalos por datos confirmados antes de publicar un catálogo comercial.

## Tecnologías

- **FastAPI** y **Uvicorn** para la aplicación web y la API.
- **Jinja2** para las plantillas HTML.
- **Pydantic** para validar los datos de la API.
- **SQLAlchemy** para acceder a **SQLite** (local), **PostgreSQL** o **Azure SQL**.
- **GitHub Actions** y **Azure App Service** para pruebas y despliegue.

## Estructura del proyecto

| Archivo o carpeta | Responsabilidad |
| --- | --- |
| `main.py` | Punto de entrada: expone la aplicación para Uvicorn. |
| `aplicacion.py` | Fábrica `crear_app`: ensambla configuración, plantillas, base de datos y rutas. Incluye `cargar_configuracion` y `configurar_plantillas`. |
| `rutas_web.py` | Páginas HTML: inicio, catálogo, ficha, servicios y contacto. |
| `api_vehiculos.py` | API REST de vehículos: modelos Pydantic, token de acceso y rutas. |
| `services.py` | Lógica del contacto: `ContactoService` coordina el registro y `ValidadorContacto` valida los datos. |
| `repositories.py` | Acceso a los datos de vehículos y contactos. |
| `database.py` | `Database` entrega conexiones; la elección de la base, las tablas y la creación del esquema están en funciones separadas. |
| `imagenes.py` | Estrategia para servir imágenes locales o desde Blob Storage. |
| `migrar_sqlite.py` | Copia los registros de SQLite a Azure SQL. |
| `templates/` | Plantillas HTML. |
| `static/` | Estilos e imágenes. |
| `tests/` | Pruebas de integración. |
| `.github/workflows/` | Pruebas y despliegue automático a Azure. |

## Inicio rápido

Requiere Python 3.12.

### Windows (PowerShell)

Ejecuta estos comandos desde la raíz del repositorio.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:SECRET_KEY = & .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
$env:AUTOBOTS_API_TOKEN = & .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

### Linux, macOS y Codespaces

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
export AUTOBOTS_API_TOKEN=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
python -m uvicorn main:app --reload
```

Abre [http://127.0.0.1:8000](http://127.0.0.1:8000). Si `DATABASE_URL` está sin definir, la aplicación usa `autobot.db` en local.

## Variables de entorno

| Variable | Para qué sirve |
| --- | --- |
| `SECRET_KEY` | **Obligatoria.** Firma las sesiones. Debe ser aleatoria, privada y estable. |
| `AUTOBOTS_API_TOKEN` | Token privado para crear, modificar o borrar vehículos por la API. Sin él, esas operaciones responden `503`. |
| `DATABASE_URL` | URL de Azure SQL o PostgreSQL. Sin definir, se usa SQLite local. En Azure es obligatoria. |
| `AZURE_BLOB_BASE_URL` | URL del contenedor de imágenes, si se usa Blob Storage. Sin definir, se sirven las imágenes locales. |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | Solo en Azure: `true` para instalar `requirements.txt` al desplegar el ZIP. |
| `TEST_DATABASE_URL` | Solo en pruebas: base temporal (PostgreSQL en GitHub Actions). |

## API de vehículos

Prueba las operaciones en [Swagger UI](http://127.0.0.1:8000/docs). La ficha y el catálogo HTML usan la misma base que la API.

| Método | Ruta | Resultado |
| --- | --- | --- |
| `GET` | `/api/vehiculos?q=Toyota+Corolla` | Lista o filtra por marca, modelo, nombre completo o tipo. |
| `GET` | `/api/vehiculos/{vehiculo_id}` | Consulta el vehículo por ID. |
| `POST` | `/api/vehiculos` | Crea un vehículo y devuelve `201` y su ruta en `Location`. |
| `PUT` | `/api/vehiculos/{vehiculo_id}` | Reemplaza los datos editables. Los campos opcionales omitidos quedan vacíos. |
| `PATCH` | `/api/vehiculos/{vehiculo_id}` | Cambia los campos enviados. Usa `null` para borrar el valor de un campo opcional. |
| `DELETE` | `/api/vehiculos/{vehiculo_id}` | Elimina el registro y devuelve `204`. |
| `HEAD` y `OPTIONS` | Colección y ficha | Devuelven encabezados sin cuerpo. `OPTIONS` indica los métodos admitidos en `Allow`. |

Para `POST`, `PUT`, `PATCH` y `DELETE`, configura `AUTOBOTS_API_TOKEN` y pega el valor en **Authorize** de Swagger. Prueba primero con SQLite y un vehículo que tú crees. Los cambios de la API se guardan en la base.

Puedes actualizar `precio_cop` (en pesos enteros), `motor`, `transmision` y `combustible` desde la API. Ejemplo de cuerpo para `POST`:

```json
{
  "marca": "Toyota",
  "modelo": "Yaris de prueba",
  "anio": 2025,
  "tipo": "Sedán",
  "precio_cop": 85000000
}
```

## Pruebas

En PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

En Linux, macOS o Codespaces:

```bash
pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

Las pruebas usan SQLite temporal por defecto. GitHub Actions define `TEST_DATABASE_URL` para probar con un PostgreSQL temporal. La suite abre las páginas, comprueba las URLs de las imágenes, envía un contacto y ejecuta el ciclo de vida de un vehículo desde la API.

## Despliegue en Azure

Usa App Service Linux con Python 3.12 y una base de datos accesible desde la aplicación. En **Configuración → Variables de entorno** de App Service, agrega las variables de la sección [Variables de entorno](#variables-de-entorno): `SECRET_KEY` (genera una nueva para Azure), `AUTOBOTS_API_TOKEN`, `DATABASE_URL`, `SCM_DO_BUILD_DURING_DEPLOYMENT` y, si usas Blob Storage, `AZURE_BLOB_BASE_URL`.

### Base de datos

Esta URL de ejemplo conecta con **Azure SQL** mediante autenticación SQL.

```
mssql+pyodbc://USUARIO:CONTRASENA@SERVIDOR.database.windows.net:1433/BASE?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no
```

`pyodbc` requiere **ODBC Driver 18 for SQL Server** instalado en el sistema donde corre FastAPI. Para **PostgreSQL**, usa este formato de URL.

```
postgresql://USUARIO:CONTRASENA@SERVIDOR.postgres.database.azure.com:5432/BASE?sslmode=require
```

Codifica los caracteres especiales del usuario y la contraseña para URL. Permite la conexión desde App Service y da al usuario permisos para crear y modificar las tablas y trabajar con sus datos. La base en Azure se inicializa al arrancar.

Para conservar registros de SQLite al pasar a Azure SQL, haz una copia de `autobot.db` y ejecuta `python migrar_sqlite.py RUTA_A_LA_COPIA` con `DATABASE_URL` apuntando a Azure SQL, antes de arrancar la app con esa base.

### Comando de inicio

El workflow configura el comando de inicio de Uvicorn al desplegar. Si publicas manualmente, establece el mismo comando en **Configuración → Configuración general**.

```
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

[Configurar Python en App Service](https://learn.microsoft.com/en-us/azure/app-service/configure-language-python) · [Instalar el controlador ODBC en Linux](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server)

### Imágenes en Azure Blob Storage

1. En una cuenta de almacenamiento dedicada a archivos públicos, habilita **Allow Blob anonymous access** en **Configuration**.
2. En **Containers**, crea un contenedor con nivel **Blob (anonymous read access for blobs only)**. Carga los archivos de `static/img` con sus nombres originales.
3. Guarda `https://CUENTA.blob.core.windows.net/CONTENEDOR` como `AZURE_BLOB_BASE_URL`. Abre la URL de una imagen en una ventana privada para comprobar que carga.

Si la variable está sin definir, FastAPI sigue sirviendo las imágenes locales. Usa el contenedor solo para imágenes públicas. [Configurar acceso de blobs](https://learn.microsoft.com/en-us/azure/storage/blobs/anonymous-read-access-configure) · [Subir archivos desde Azure Portal](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-portal)

### GitHub Actions

El [workflow de Azure](.github/workflows/azure.yml) prueba las páginas, el formulario y la API con PostgreSQL en los Pull Requests hacia `main`. Para habilitar el despliegue en los pushes a `main`, configura la identidad de Azure y GitHub Actions.

- Una identidad de Azure con **Website Contributor** sobre el App Service y una credencial federada de GitHub para `repo:SAMTHE23/proyecto-pagina:ref:refs/heads/main` con audiencia `api://AzureADTokenExchange`.
- Los secretos de Actions `AZURE_CLIENT_ID`, `AZURE_TENANT_ID` y `AZURE_SUBSCRIPTION_ID`, y la variable de Actions `AZURE_WEBAPP_NAME` con el nombre exacto del App Service.

En la pestaña **Actions**, revisa que pasen las pruebas, que termine el despliegue y que responda `/catalogo`. Para verificar la integración, abre una ficha de vehículo y envía un contacto de prueba en Azure. [Configurar el despliegue con GitHub Actions](https://learn.microsoft.com/en-us/azure/app-service/deploy-github-actions)

## Arquitectura y conceptos de la entrega

### Patrones de software

| Patrón | Aplicación |
| --- | --- |
| Repositorio | `VehiculoRepository` y `ContactoRepository` aíslan el acceso a los datos en `repositories.py`. |
| Capa de servicios | `ContactoService` coordina el registro de contactos: limpia los datos, los valida y decide cuándo guardarlos. |
| Estrategia | `elegir_url_imagen` configura una función de imágenes locales o de Blob Storage. Las plantillas llaman a ambas mediante `imagen_url`. |
| Fábrica de aplicación | `crear_app` configura FastAPI y permite elegir dependencias distintas para la aplicación y las pruebas. |
| Adaptador | `adaptar_formulario` convierte el `FormData` de Starlette en un conjunto de valores de texto que acepta el servicio. |

### Principios SOLID

| Principio | Evidencia |
| --- | --- |
| Responsabilidad única | Cada módulo y cada clase tiene una tarea. `rutas_web.py` maneja HTML, `api_vehiculos.py` maneja la API y los repositorios manejan SQL. `Database` solo guarda el motor y entrega conexiones, mientras `crear_motor` elige la base y `crear_tablas` prepara el esquema. `ContactoService` solo coordina el registro y `ValidadorContacto` se encarga de validar. `crear_app` solo ensambla la aplicación, apoyada en `cargar_configuracion` y `configurar_plantillas`. |
| Abierto/cerrado | La prueba registra una tercera estrategia mediante el parámetro `estrategia_imagen` de la fábrica y conserva la misma llamada en las plantillas. |
| Sustitución de Liskov | La prueba del servicio pasa un registro en memoria que cumple el mismo contrato de guardado que el repositorio SQL. |
| Segregación de interfaces | El servicio depende de `RegistroContactos`, que solo exige `crear`. |
| Inversión de dependencias | `ContactoService` recibe su registro por constructor. La fábrica conecta el repositorio real y la API recibe el de su instancia mediante `Depends`. |

### Conceptos demostrables en el código y las pruebas

1. Rutas y routers.
2. Métodos HTTP.
3. Parámetros de ruta como `vehiculo_id`.
4. Parámetros de consulta como `q`.
5. Cuerpos JSON tipados.
6. Validación con Pydantic.
7. Modelos y códigos de respuesta HTTP.
8. Manejo de errores con `HTTPException`.
9. Inyección de dependencias con `Depends`.
10. Formularios HTML y plantillas Jinja.
11. Transacciones de base de datos.
12. Documentación interactiva con OpenAPI y Swagger UI.
13. Pruebas de integración y automatización con GitHub Actions.