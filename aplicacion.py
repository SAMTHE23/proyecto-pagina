import os
from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import pass_context
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import URL
from starlette.middleware.sessions import SessionMiddleware

from api_vehiculos import router as router_vehiculos
from database import Database
from imagenes import EstrategiaImagen, elegir_url_imagen
from repositories import ContactoRepository, VehiculoRepository
from rutas_web import router as router_web
from services import ContactoService

RAIZ = Path(__file__).resolve().parent


@pass_context
def url_relativa(contexto, ruta, **parametros):
    url = contexto["request"].url_for(ruta, **parametros)
    return URL(path=url.path)


def formatear_precio_cop(precio):
    return f"$ {precio:,} COP".replace(",", ".")


def crear_app(
    *,
    clave_secreta: str | None = None,
    url_contenedor: str | None = None,
    api_token: str | None = None,
    estrategia_imagen: EstrategiaImagen | None = None,
    crear_base: Callable[[], Database] = Database,
) -> FastAPI:
    secreto = os.environ.get("SECRET_KEY") if clave_secreta is None else clave_secreta
    if not secreto:
        raise RuntimeError("Configura la variable SECRET_KEY antes de iniciar FastAPI.")

    contenedor = os.environ.get("AZURE_BLOB_BASE_URL", "") if url_contenedor is None else url_contenedor
    resolver_imagen = estrategia_imagen if estrategia_imagen is not None else elegir_url_imagen(contenedor)

    @pass_context
    def imagen_url(contexto, nombre):
        return resolver_imagen(contexto["request"], nombre)

    @asynccontextmanager
    async def iniciar(app):
        base = await run_in_threadpool(crear_base)
        try:
            app.state.vehiculos_repo = VehiculoRepository(base)
            app.state.contacto_service = ContactoService(ContactoRepository(base))
            yield
        finally:
            await run_in_threadpool(base.motor.dispose)

    app = FastAPI(title="Autobots", lifespan=iniciar)
    app.add_middleware(
        SessionMiddleware,
        secret_key=secreto,
        https_only=bool(os.environ.get("WEBSITE_SITE_NAME")),
    )
    app.state.api_token = os.environ.get("AUTOBOTS_API_TOKEN") if api_token is None else api_token

    plantillas = Jinja2Templates(directory=RAIZ / "templates")
    plantillas.env.globals.update(url_for=url_relativa, imagen_url=imagen_url)
    plantillas.env.filters["precio_cop"] = formatear_precio_cop
    app.state.plantillas = plantillas

    app.mount("/static", StaticFiles(directory=RAIZ / "static"), name="static")
    app.include_router(router_web)
    app.include_router(router_vehiculos)
    return app
