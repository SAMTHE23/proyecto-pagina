import os

from flask import Flask, abort, flash, redirect, render_template, request, url_for

from database import Database
from repositories import ContactoRepository, VehiculoRepository
from services import MOTIVO_COTIZACION, MOTIVOS, SERVICIOS, ContactoService

NOMBRE_SITIO = "Autobots"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("Configura la variable de entorno SECRET_KEY antes de iniciar Flask.")

base = Database()
vehiculos_repo = VehiculoRepository(base)
contacto_service = ContactoService(ContactoRepository(base))


@app.get("/")
def home():
    return render_template("index.html", nombre=NOMBRE_SITIO, destacados=vehiculos_repo.listar()[:3])


@app.get("/catalogo")
def catalogo():
    busqueda = request.args.get("q", "").strip()
    return render_template("catalogo.html", vehiculos=vehiculos_repo.listar(busqueda), busqueda=busqueda)


@app.get("/catalogo/<int(signed=True):vehiculo_id>")
def detalle_vehiculo(vehiculo_id):
    vehiculo = vehiculos_repo.obtener(vehiculo_id)
    if vehiculo is None:
        abort(404)
    return render_template(
        "detalle.html",
        vehiculo=vehiculo,
        busqueda=request.args.get("q", "").strip(),
        motivo_cotizacion=MOTIVO_COTIZACION,
    )


@app.get("/servicios")
def servicios():
    return render_template("servicios.html")


@app.route("/contacto", methods=["GET", "POST"])
def contacto():
    if request.method == "POST":
        datos, errores = contacto_service.registrar(request.form)
        if errores:
            for e in errores:
                flash(e, "error")
            return render_template("contacto.html", motivos=MOTIVOS, servicios=SERVICIOS, datos=datos), 400
        flash("¡Gracias! Recibimos tu solicitud y te contactaremos pronto.", "ok")
        return redirect(url_for("contacto"))

    datos = {"motivo": request.args.get("motivo", ""), "servicio": request.args.get("servicio", "")}
    vehiculo_id = request.args.get("vehiculo", type=int)
    if datos["motivo"] == MOTIVO_COTIZACION and vehiculo_id is not None:
        vehiculo = vehiculos_repo.obtener(vehiculo_id)
        if vehiculo is not None:
            descripcion = " ".join(
                str(vehiculo[campo]) for campo in ("marca", "modelo", "anio") if vehiculo[campo]
            )
            referencia = f"el vehículo {descripcion}" if descripcion else "este vehículo"
            datos["mensaje"] = f"Hola, me interesa cotizar {referencia}."
    return render_template("contacto.html", motivos=MOTIVOS, servicios=SERVICIOS, datos=datos)


if __name__ == "__main__":
    app.run()
