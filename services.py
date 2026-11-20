import re
from datetime import date


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


class ContactoService:
    

    def __init__(self, repositorio):
        self.repositorio = repositorio

    def registrar(self, form):
        datos = {
            "nombre": form.get("nombre", "").strip(),
            "telefono": form.get("telefono", "").strip(),
            "correo": form.get("correo", "").strip(),
            "motivo": form.get("motivo", "").strip(),
            "servicio": form.get("servicio", "").strip(),
            "fecha": form.get("fecha", "").strip(),
            "mensaje": form.get("mensaje", "").strip(),
        }
        if datos["motivo"] != MOTIVO_MANTENIMIENTO:
            datos["servicio"] = ""
            datos["fecha"] = ""
        errores = self._validar(datos)
        if not errores:
            self.repositorio.crear(datos)
        return datos, errores

    def _validar(self, d):
        errores = []
        if not d["nombre"]:
            errores.append("El nombre es obligatorio.")
        elif len(d["nombre"]) > 120:
            errores.append("El nombre debe tener máximo 120 caracteres.")
        if not d["telefono"]:
            errores.append("El teléfono es obligatorio.")
        elif (
            len(d["telefono"]) > 30
            or not re.fullmatch(r"\+?[0-9(). -]+", d["telefono"])
            or not 7 <= sum(c.isdigit() for c in d["telefono"]) <= 15
        ):
            errores.append("Ingresa un teléfono válido de 7 a 15 dígitos.")
        if d["correo"] and (
            len(d["correo"]) > 254
            or not re.fullmatch(r"[^\s@]+@[^\s@.]+(?:\.[^\s@.]+)+", d["correo"])
        ):
            errores.append("Ingresa un correo válido.")
        if len(d["mensaje"]) > 2000:
            errores.append("El mensaje debe tener máximo 2000 caracteres.")
        if d["motivo"] not in MOTIVOS:
            errores.append("Selecciona un motivo de contacto.")
        if d["motivo"] == MOTIVO_MANTENIMIENTO:
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
        elif d["motivo"] in MOTIVOS and not d["mensaje"]:
            errores.append("Escribe un mensaje.")
        return errores
