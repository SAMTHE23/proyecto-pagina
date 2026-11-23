import re
from collections.abc import Mapping
from datetime import date
from typing import Protocol

MOTIVO_COTIZACION = "Cotizar un vehículo"

MOTIVOS = ["Información general", MOTIVO_COTIZACION, "Agendar mantenimiento"]

SERVICIOS = [
    "Cambio de aceite",
    "Revisión de frenos",
    "Diagnóstico general",
    "Alineación y balanceo",
    "Mantenimiento preventivo",
    "Revisión general",
]

MOTIVO_MANTENIMIENTO = "Agendar mantenimiento"

CAMPOS_CONTACTO = ("nombre", "telefono", "correo", "motivo", "servicio", "fecha", "mensaje")


class RegistroContactos(Protocol):
    def crear(self, datos: dict[str, str]) -> None: ...


class ValidadorContacto:
    """Solo valida los datos del formulario; no guarda ni modifica nada."""

    def validar(self, d: dict[str, str]) -> list[str]:
        errores: list[str] = []
        errores += self._nombre(d)
        errores += self._telefono(d)
        errores += self._correo(d)
        errores += self._mensaje(d)
        errores += self._motivo(d)
        errores += self._segun_motivo(d)
        return errores

    def _nombre(self, d):
        if not d["nombre"]:
            return ["El nombre es obligatorio."]
        if len(d["nombre"]) > 120:
            return ["El nombre debe tener máximo 120 caracteres."]
        return []

    def _telefono(self, d):
        if not d["telefono"]:
            return ["El teléfono es obligatorio."]
        if (
            len(d["telefono"]) > 30
            or not re.fullmatch(r"\+?[0-9(). -]+", d["telefono"])
            or not 10 <= sum(c.isdigit() for c in d["telefono"]) <= 15
        ):
            return ["El número de teléfono debe tener entre 10 y 15 dígitos."]
        return []

    def _correo(self, d):
        if d["correo"] and (
            len(d["correo"]) > 254
            or not re.fullmatch(r"[^\s@]+@[^\s@.]+(?:\.[^\s@.]+)+", d["correo"])
        ):
            return ["Ingresa un correo válido."]
        return []

    def _mensaje(self, d):
        if len(d["mensaje"]) > 2000:
            return ["El mensaje debe tener máximo 2000 caracteres."]
        return []

    def _motivo(self, d):
        if d["motivo"] not in MOTIVOS:
            return ["Selecciona un motivo de contacto."]
        return []

    def _segun_motivo(self, d):
        if d["motivo"] == MOTIVO_MANTENIMIENTO:
            return self._cita(d)
        if d["motivo"] in MOTIVOS and not d["mensaje"]:
            return ["Escribe un mensaje."]
        return []

    def _cita(self, d):
        errores = []
        if d["servicio"] not in SERVICIOS:
            errores.append("Selecciona el servicio que necesitas.")
        if not d["fecha"]:
            errores.append("Indica la fecha en la que quieres la cita.")
        else:
            try:
                fecha = date.fromisoformat(d["fecha"])
                if fecha.isoformat() != d["fecha"]:
                    raise ValueError
            except ValueError:
                errores.append("Ingresa una fecha válida en formato AAAA-MM-DD.")
            else:
                if fecha < date.today():
                    errores.append("La fecha de la cita no puede estar en el pasado.")
        return errores


def normalizar_contacto(form: Mapping[str, str]) -> dict[str, str]:
    datos = {campo: form.get(campo, "").strip() for campo in CAMPOS_CONTACTO}
    if datos["motivo"] != MOTIVO_MANTENIMIENTO:
        datos["servicio"] = ""
        datos["fecha"] = ""
    return datos


class ContactoService:
    """Coordina el registro: limpia los datos, los valida y los guarda."""

    def __init__(self, repositorio: RegistroContactos, validador: ValidadorContacto | None = None):
        self.repositorio = repositorio
        self.validador = validador or ValidadorContacto()

    def registrar(self, form: Mapping[str, str]) -> tuple[dict[str, str], list[str]]:
        datos = normalizar_contacto(form)
        errores = self.validador.validar(datos)
        if not errores:
            self.repositorio.crear(datos)
        return datos, errores