from urllib.parse import quote, urlsplit

from flask import url_for


def imagen_local(nombre):
    return url_for("static", filename=f"img/{nombre}")


def elegir_url_imagen(url_contenedor):
    """Selecciona cómo obtener la URL de las imágenes al iniciar Flask."""
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

    def imagen_blob(nombre):
        return f"{url_contenedor}/{quote(nombre, safe='/')}"

    return imagen_blob
