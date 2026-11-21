# Autobots

Sitio Flask con catálogo de vehículos y formulario de contacto. Las rutas principales son `/`, `/catalogo`, `/catalogo/<id>`, `/servicios` y `/contacto`.

## Desarrollo local

Requiere Python 3.12. Ejecuta estos comandos en PowerShell desde la raíz del repositorio.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:SECRET_KEY = & .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
.\.venv\Scripts\python.exe -m flask --app main run --debug
```

Abre [http://127.0.0.1:5000](http://127.0.0.1:5000). Si `DATABASE_URL` está sin definir, la aplicación usa `autobot.db` en local.

Los precios se muestran en pesos colombianos (COP). Los precios y las especificaciones de ejemplo son ilustrativos. Reemplázalos por datos confirmados antes de publicar un catálogo comercial. Los vehículos sin un precio registrado muestran **Consultar precio** y las especificaciones opcionales aparecen cuando tienen datos. En la tabla `vehiculos`, actualiza `precio_cop` (en pesos enteros), `motor`, `transmision` y `combustible` para mantener las fichas.

## Azure App Service

Usa App Service Linux con Python 3.12 y una base de datos accesible desde la aplicación. En **Configuración → Variables de entorno** de App Service, agrega las siguientes variables.

| Variable | Valor |
| --- | --- |
| `SECRET_KEY` | Clave aleatoria, privada y estable. Genera una nueva para Azure. |
| `DATABASE_URL` | URL de Azure SQL o PostgreSQL. |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` para instalar `requirements.txt` al desplegar el ZIP. |
| `AZURE_BLOB_BASE_URL` | URL del contenedor de imágenes, si se usa Blob Storage. |

Esta URL de ejemplo conecta con **Azure SQL** mediante autenticación SQL.

```text
mssql+pyodbc://USUARIO:CONTRASENA@SERVIDOR.database.windows.net:1433/BASE?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no
```

`pyodbc` requiere **ODBC Driver 18 for SQL Server** instalado en el sistema donde corre Flask. Para **PostgreSQL**, usa este formato de URL.

```text
postgresql://USUARIO:CONTRASENA@SERVIDOR.postgres.database.azure.com:5432/BASE?sslmode=require
```

Codifica los caracteres especiales del usuario y la contraseña para URL. Permite la conexión desde App Service y da al usuario permisos para crear y modificar las tablas y trabajar con sus datos. La base en Azure se inicializa al arrancar. Para conservar registros de SQLite al pasar a Azure SQL, haz una copia de `autobot.db` y ejecuta `python migrar_sqlite.py RUTA_A_LA_COPIA` con `DATABASE_URL` apuntando a Azure SQL, antes de arrancar la app con esa base.

En **Configuración → Configuración general**, establece el comando de inicio de Gunicorn.

```sh
gunicorn --bind 0.0.0.0:8000 main:app
```

[Configurar Python en App Service](https://learn.microsoft.com/en-us/azure/app-service/configure-language-python) · [Instalar el controlador ODBC en Linux](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server)

### Imágenes en Azure Blob Storage

1. En una cuenta de almacenamiento dedicada a archivos públicos, habilita **Allow Blob anonymous access** en **Configuration**.
2. En **Containers**, crea un contenedor con nivel **Blob (anonymous read access for blobs only)**. Carga los archivos de `static/img` con sus nombres originales.
3. Guarda `https://CUENTA.blob.core.windows.net/CONTENEDOR` como `AZURE_BLOB_BASE_URL`. Abre la URL de una imagen en una ventana privada para comprobar que carga.

Si la variable está sin definir, Flask sigue sirviendo las imágenes locales. Usa el contenedor solo para imágenes públicas. [Configurar acceso de blobs](https://learn.microsoft.com/en-us/azure/storage/blobs/anonymous-read-access-configure) · [Subir archivos desde Azure Portal](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-portal)

### GitHub Actions

El [workflow de Azure](.github/workflows/azure.yml) prueba el catálogo, las fichas y el formulario con PostgreSQL en los Pull Requests hacia `main`. Para habilitar el despliegue en los pushes a `main`, configura la identidad de Azure y GitHub Actions.

- Una identidad de Azure con **Website Contributor** sobre el App Service y una credencial federada de GitHub para `repo:SAMTHE23/proyecto-pagina:ref:refs/heads/main` con audiencia `api://AzureADTokenExchange`.
- Los secretos de Actions `AZURE_CLIENT_ID`, `AZURE_TENANT_ID` y `AZURE_SUBSCRIPTION_ID`, y la variable de Actions `AZURE_WEBAPP_NAME` con el nombre exacto del App Service.

En la pestaña **Actions**, revisa que pasen las pruebas, que termine el despliegue y que responda `/catalogo`. Para verificar la integración, abre una ficha de vehículo y envía un contacto de prueba en Azure. [Configurar el despliegue con GitHub Actions](https://learn.microsoft.com/en-us/azure/app-service/deploy-github-actions)
