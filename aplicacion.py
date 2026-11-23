import os
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
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


@dataclass(frozen=True)
class Configuracion:
    clave_secreta: str
    url_contenedor: str
    api_token: str | None
    solo_https: bool


def cargar_configuracion(
    clave_secreta: str | None = None,
    url_contenedor: str | None = None,
    api_token: str | None = None,
) -> Configuracion:
    secreto = os.environ.get("SECRET_KEY") if clave_secreta is None else clave_secreta
    if not secreto:
        raise RuntimeError("Configura la variable SECRET_KEY antes de iniciar FastAPI.")
    contenedor = os.environ.get("AZURE_BLOB_BASE_URL", "") if url_contenedor is None else url_contenedor
    token = os.environ.get("AUTOBOTS_API_TOKEN") if api_token is None else api_token
    return Configuracion(
        clave_secreta=secreto,
        url_contenedor=contenedor,
        api_token=token,
        solo_https=bool(os.environ.get("WEBSITE_SITE_NAME")),
    )



@pass_context
def url_relativa(contexto, ruta, **parametros):
    url = contexto["request"].url_for(ruta, **parametros)
    return URL(path=url.path)


def formatear_precio_cop(precio):
    return f"$ {precio:,} COP".replace(",", ".")


def configurar_plantillas(directorio: Path, resolver_imagen) -> Jinja2Templates:
    @pass_context
    def imagen_url(contexto, nombre):
        return resolver_imagen(contexto["request"], nombre)

    plantillas = Jinja2Templates(directory=directorio)
    plantillas.env.globals.update(url_for=url_relativa, imagen_url=imagen_url)
    plantillas.env.filters["precio_cop"] = formatear_precio_cop
    return plantillas



def crear_app(
    *,
    clave_secreta: str | None = None,
    url_contenedor: str | None = None,
    api_token: str | None = None,
    estrategia_imagen: EstrategiaImagen | None = None,
    crear_base: Callable[[], Database] = Database,
) -> FastAPI:
    config = cargar_configuracion(clave_secreta, url_contenedor, api_token)
    resolver_imagen = estrategia_imagen if estrategia_imagen is not None else elegir_url_imagen(config.url_contenedor)

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
    app.add_middleware(SessionMiddleware, secret_key=config.clave_secreta, https_only=config.solo_https)
    app.state.api_token = config.api_token
    app.state.plantillas = configurar_plantillas(RAIZ / "templates", resolver_imagen)
    app.mount("/static", StaticFiles(directory=RAIZ / "static"), name="static")
    app.include_router(router_web)
    app.include_router(router_vehiculos)
    return app