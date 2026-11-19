import os

from flask import Flask, flash, redirect, render_template, request, url_for

from database import Database
from repositories import ContactoRepository, VehiculoRepository
from services import MOTIVOS, SERVICIOS, ContactoService

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
    return render_template("contacto.html", motivos=MOTIVOS, servicios=SERVICIOS, datos=datos)


if __name__ == "__main__":
    app.run()