# proyecto-pagina

## Desarrollo local en VS Code (PowerShell)

```powershell
python -m pip install -r requirements.txt
$env:SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
python -m flask --app main run --debug
```

Sin `DATABASE_URL`, el desarrollo local usa `autobot.db`. Los datos de ese archivo siguen disponibles en local. Cada nueva terminal necesita definir `SECRET_KEY`.

## Azure App Service (Linux)

1. Crea o usa una base en **Azure Database for PostgreSQL Flexible Server**. Asegúrate de que App Service tenga conectividad al servidor y el usuario pueda crear tablas en la base.
2. En **Configuración → Variables de entorno → Configuración de la aplicación**, guarda `SECRET_KEY` con una clave aleatoria nueva y estable. La clave anterior quedó expuesta en el historial de Git. Guarda también `DATABASE_URL` con la URL de tu base. Codifica en formato URL los caracteres especiales de la contraseña. Ejemplo con valores de muestra:

   ```text
   postgresql://USUARIO:CONTRASENA@SERVIDOR.postgres.database.azure.com:5432/BASE?sslmode=require
   ```

3. En **Configuración → Configuración general → Comando de inicio**, configura:

   ```sh
   gunicorn --bind 0.0.0.0:8000 main:app
   ```

4. Despliega el proyecto con `requirements.txt` en la raíz. Al iniciar, la aplicación crea las tablas y carga los vehículos de ejemplo si el catálogo está vacío.

Si ya tienes contactos o vehículos personalizados en un archivo SQLite, conserva una copia y migra esos registros a PostgreSQL antes de poner el sitio en producción. La inicialización crea tablas y datos de ejemplo. La transferencia de registros existentes es un paso aparte.

## GitHub Actions

El workflow `.github/workflows/azure.yml` instala las dependencias y prueba el catálogo y el formulario con un PostgreSQL temporal en cada Pull Request hacia `main`. Después de pasar las pruebas, puede desplegar los cambios de `main` y comprobar que el catálogo responde en Azure.

1. Selecciona **Python 3.12** en tu App Service de Linux. Además de `SECRET_KEY` y `DATABASE_URL`, agrega `SCM_DO_BUILD_DURING_DEPLOYMENT=true` a las variables de la aplicación para que Azure instale `requirements.txt` desde el ZIP.
2. Configura una identidad de Azure con el rol **Website Contributor** en ese App Service. Agrega una credencial federada de GitHub para la rama `main`, con el sujeto `repo:SAMTHE23/proyecto-pagina:ref:refs/heads/main` y audiencia `api://AzureADTokenExchange`. Sigue la sección de OpenID Connect de la [guía de Microsoft](https://learn.microsoft.com/en-us/azure/app-service/deploy-github-actions).
3. En GitHub, abre **Settings → Secrets and variables → Actions**. En **Secrets**, agrega `AZURE_CLIENT_ID`, `AZURE_TENANT_ID` y `AZURE_SUBSCRIPTION_ID` con los valores de tu identidad de despliegue. En **Variables**, agrega `AZURE_WEBAPP_NAME` con el nombre del App Service una vez configurado todo lo anterior.
4. Una vez integrado el workflow, abre **Actions → Pruebas y despliegue en Azure → Run workflow** y selecciona `main` para probar el primer despliegue. Las integraciones posteriores en `main` activarán el mismo workflow automáticamente.
