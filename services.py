MOTIVOS = ["Información general", "Cotizar un vehículo", "Agendar mantenimiento"]
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
    """Reglas de negocio del formulario. Recibe el repositorio (inversión de dependencias)."""

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
        errores = self._validar(datos)
        if not errores:
            self.repositorio.crear(datos)
        return datos, errores

    def _validar(self, d):
        errores = []
        if not d["nombre"]:
            errores.append("El nombre es obligatorio.")
        if not d["telefono"]:
            errores.append("El teléfono es obligatorio.")
        if d["motivo"] not in MOTIVOS:
            errores.append("Selecciona un motivo de contacto.")
        if d["motivo"] == MOTIVO_MANTENIMIENTO:
            if d["servicio"] not in SERVICIOS:
                errores.append("Selecciona el servicio que necesitas.")
            if not d["fecha"]:
                errores.append("Indica la fecha en la que quieres la cita.")
        elif d["motivo"] and not d["mensaje"]:
            errores.append("Escribe un mensaje.")
        return errores