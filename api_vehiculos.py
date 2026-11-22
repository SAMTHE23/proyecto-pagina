from hmac import compare_digest
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Response, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, field_validator

from repositories import VehiculoRepository


router = APIRouter(prefix="/api/vehiculos", tags=["Vehículos"])

METODOS_COLECCION = "GET, HEAD, OPTIONS, POST"
METODOS_DETALLE = "GET, HEAD, OPTIONS, PUT, PATCH, DELETE"

Texto = Annotated[str, Field(min_length=1, max_length=120)]
Anio = Annotated[int, Field(strict=True, ge=1886, le=9999)]
Precio = Annotated[int, Field(strict=True, ge=0, le=2**63 - 1)]
VehiculoID = Annotated[int, Path(ge=-(2**63), le=2**63 - 1)]


class DatosVehiculo(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    anio: Anio | None = None
    tipo: Texto | None = None
    imagen: Annotated[str, Field(min_length=1, max_length=1024)] | None = None
    precio_cop: Precio | None = None
    motor: Texto | None = None
    transmision: Texto | None = None
    combustible: Texto | None = None

    @field_validator("motor", "transmision", "combustible")
    @classmethod
    def validar_longitud_sql_server(cls, valor):
        if valor is not None and len(valor.encode("utf-16-le")) > 240:
            raise ValueError("La especificación supera el espacio de 120 caracteres de la base de datos.")
        return valor


class VehiculoCompleto(DatosVehiculo):
    marca: Texto
    modelo: Texto


class VehiculoParcial(DatosVehiculo):
    marca: Texto | None = None
    modelo: Texto | None = None

    @field_validator("marca", "modelo")
    @classmethod
    def validar_nombre_presente(cls, valor):
        if valor is None:
            raise ValueError("La marca y el modelo requieren texto cuando se incluyen.")
        return valor


class VehiculoRespuesta(BaseModel):
    id: int
    marca: str | None
    modelo: str | None
    anio: int | None
    tipo: str | None
    imagen: str | None
    precio_cop: int | None
    motor: str | None
    transmision: str | None
    combustible: str | None


def obtener_repositorio(request: Request) -> VehiculoRepository:
    return request.app.state.vehiculos_repo


Repositorio = Annotated[VehiculoRepository, Depends(obtener_repositorio)]
bearer = HTTPBearer(auto_error=False, scheme_name="TokenVehiculos")


def verificar_token(
    request: Request,
    credenciales: Annotated[HTTPAuthorizationCredentials | None, Security(bearer)],
):
    token = request.app.state.api_token
    if not token:
        raise HTTPException(503, "La escritura de vehículos no está configurada.")
    if credenciales is None or not compare_digest(
        credenciales.credentials.encode("utf-8"), token.encode("utf-8")
    ):
        raise HTTPException(401, "Se requiere un token de acceso válido.", headers={"WWW-Authenticate": "Bearer"})


ESCRITURA = [Depends(verificar_token)]
ERROR_DETALLE = {404: {"description": "Vehículo no encontrado"}}
ERRORES_ESCRITURA = {
    401: {"description": "Token ausente o inválido"},
    503: {"description": "Escritura no configurada"},
}


def exigir_vehiculo(resultado):
    if resultado is None:
        raise HTTPException(404, "Vehículo no encontrado.")
    return resultado


def respuesta_head(metodos):
    respuesta = Response(media_type="application/json", headers={"Allow": metodos})
    del respuesta.headers["content-length"]
    return respuesta


@router.get("", response_model=list[VehiculoRespuesta])
def listar_vehiculos(repo: Repositorio, q: str = ""):
    return repo.listar(q.strip())


@router.head("", response_class=Response)
def head_coleccion():
    return respuesta_head(METODOS_COLECCION)


@router.options("", status_code=204, response_class=Response)
def opciones_coleccion():
    return Response(status_code=204, headers={"Allow": METODOS_COLECCION})


@router.post(
    "", status_code=201, response_model=VehiculoRespuesta,
    dependencies=ESCRITURA, responses=ERRORES_ESCRITURA,
)
def crear_vehiculo(datos: VehiculoCompleto, request: Request, response: Response, repo: Repositorio):
    vehiculo = repo.crear(datos.model_dump())
    response.headers["Location"] = request.url_for("api_obtener_vehiculo", vehiculo_id=vehiculo["id"]).path
    return vehiculo


@router.get("/{vehiculo_id}", name="api_obtener_vehiculo", response_model=VehiculoRespuesta, responses=ERROR_DETALLE)
def obtener_vehiculo(vehiculo_id: VehiculoID, repo: Repositorio):
    return exigir_vehiculo(repo.obtener(vehiculo_id))


@router.head("/{vehiculo_id}", response_class=Response, responses=ERROR_DETALLE)
def head_detalle(vehiculo_id: VehiculoID, repo: Repositorio):
    exigir_vehiculo(repo.obtener(vehiculo_id))
    return respuesta_head(METODOS_DETALLE)


@router.options("/{vehiculo_id}", status_code=204, response_class=Response)
def opciones_detalle(vehiculo_id: VehiculoID):
    return Response(status_code=204, headers={"Allow": METODOS_DETALLE})


@router.put(
    "/{vehiculo_id}", response_model=VehiculoRespuesta,
    dependencies=ESCRITURA, responses=ERROR_DETALLE | ERRORES_ESCRITURA,
)
def reemplazar_vehiculo(vehiculo_id: VehiculoID, datos: VehiculoCompleto, repo: Repositorio):
    return exigir_vehiculo(repo.actualizar(vehiculo_id, datos.model_dump()))


@router.patch(
    "/{vehiculo_id}", response_model=VehiculoRespuesta,
    dependencies=ESCRITURA, responses=ERROR_DETALLE | ERRORES_ESCRITURA,
)
def modificar_vehiculo(vehiculo_id: VehiculoID, datos: VehiculoParcial, repo: Repositorio):
    return exigir_vehiculo(repo.actualizar(vehiculo_id, datos.model_dump(exclude_unset=True)))


@router.delete(
    "/{vehiculo_id}", status_code=204, response_class=Response,
    dependencies=ESCRITURA, responses=ERROR_DETALLE | ERRORES_ESCRITURA,
)
def eliminar_vehiculo(vehiculo_id: VehiculoID, repo: Repositorio):
    if not repo.eliminar(vehiculo_id):
        raise HTTPException(404, "Vehículo no encontrado.")
    return Response(status_code=204)
