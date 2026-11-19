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
