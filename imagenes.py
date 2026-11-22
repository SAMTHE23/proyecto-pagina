from collections.abc import Callable
from urllib.parse import quote, urlsplit

from fastapi import Request

EstrategiaImagen = Callable[[Request, str], str]


def imagen_local(solicitud: Request, nombre: str) -> str:
    ruta = solicitud.url_for("static", path=f"img/{quote(nombre, safe='/')}")
    return ruta.path


def elegir_url_imagen(url_contenedor: str) -> EstrategiaImagen:
    """Selecciona cómo obtener la URL de las imágenes al iniciar la aplicación."""
    url_contenedor = url_contenedor.strip().rstrip("/")
    if not url_contenedor:
        return imagen_local

    contenedor = urlsplit(url_contenedor)
    if (
        contenedor.scheme != "https"
        or not contenedor.hostname
        or not contenedor.path
        or contenedor.username is not None
        or "?" in url_contenedor
        or "#" in url_contenedor
    ):
        raise RuntimeError("AZURE_BLOB_BASE_URL debe ser la URL HTTPS del contenedor, sin credenciales.")

    def imagen_blob(_solicitud: Request, nombre: str) -> str:
        return f"{url_contenedor}/{quote(nombre, safe='/')}"

    return imagen_blob
