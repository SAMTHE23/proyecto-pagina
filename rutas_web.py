from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.datastructures import FormData

from services import MOTIVO_COTIZACION, MOTIVOS, SERVICIOS

router = APIRouter(default_response_class=HTMLResponse)
NOMBRE_SITIO = "Autobots"
CONFIRMACION_CONTACTO = "¡Gracias! Recibimos tu solicitud y te contactaremos pronto."


def adaptar_formulario(formulario: FormData) -> dict[str, str]:
    """Adapta los valores del formulario HTTP a entradas de texto del servicio."""
    datos: dict[str, str] = {}
    for campo, valor in formulario.multi_items():
        if isinstance(valor, str):
            datos.setdefault(campo, valor)
    return datos


@router.get("/")
def home(request: Request):
    destacados = request.app.state.vehiculos_repo.listar()[:3]
    return request.app.state.plantillas.TemplateResponse(
        request=request,
        name="index.html",
        context={"nombre": NOMBRE_SITIO, "destacados": destacados},
    )


@router.get("/catalogo")
def catalogo(request: Request):
    busqueda = request.query_params.get("q", "").strip()
    vehiculos = request.app.state.vehiculos_repo.listar(busqueda)
    return request.app.state.plantillas.TemplateResponse(
        request=request,
        name="catalogo.html",
        context={"vehiculos": vehiculos, "busqueda": busqueda},
    )


@router.get("/catalogo/{vehiculo_id}")
def detalle_vehiculo(request: Request, vehiculo_id: str):
    try:
        if not vehiculo_id.removeprefix("-").isdecimal():
            raise ValueError
        identificador = int(vehiculo_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado.") from None

    vehiculo = request.app.state.vehiculos_repo.obtener(identificador)
    if vehiculo is None:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado.")
    return request.app.state.plantillas.TemplateResponse(
        request=request,
        name="detalle.html",
        context={
            "vehiculo": vehiculo,
            "busqueda": request.query_params.get("q", "").strip(),
            "motivo_cotizacion": MOTIVO_COTIZACION,
        },
    )


@router.get("/servicios")
def servicios(request: Request):
    return request.app.state.plantillas.TemplateResponse(request=request, name="servicios.html")


def _renderizar_contacto(
    request: Request, datos: dict[str, str], avisos: list[tuple[str, str]], status_code: int = 200
):
    return request.app.state.plantillas.TemplateResponse(
        request=request,
        name="contacto.html",
        context={"motivos": MOTIVOS, "servicios": SERVICIOS, "datos": datos, "avisos": avisos},
        status_code=status_code,
    )


@router.get("/contacto")
def contacto(request: Request):
    parametros = request.query_params
    datos = {"motivo": parametros.get("motivo", ""), "servicio": parametros.get("servicio", "")}
    if datos["motivo"] == MOTIVO_COTIZACION:
        try:
            vehiculo_id = int(parametros.get("vehiculo", ""))
        except ValueError:
            pass
        else:
            vehiculo = request.app.state.vehiculos_repo.obtener(vehiculo_id)
            if vehiculo is not None:
                descripcion = " ".join(
                    str(vehiculo[campo]) for campo in ("marca", "modelo", "anio") if vehiculo[campo]
                )
                referencia = f"el vehículo {descripcion}" if descripcion else "este vehículo"
                datos["mensaje"] = f"Hola, me interesa cotizar {referencia}."

    avisos = [("ok", CONFIRMACION_CONTACTO)] if request.session.pop("contacto_confirmado", False) else []
    return _renderizar_contacto(request, datos, avisos)


@router.post("/contacto")
async def registrar_contacto(request: Request):
    async with request.form() as formulario:
        datos_formulario = adaptar_formulario(formulario)
    datos, errores = await run_in_threadpool(
        request.app.state.contacto_service.registrar, datos_formulario
    )
    if errores:
        return _renderizar_contacto(request, datos, [("error", error) for error in errores], 400)

    request.session["contacto_confirmado"] = True
    return RedirectResponse(request.url_for("contacto").path, status_code=303)
