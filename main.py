from flask import Flask, flash, redirect, render_template, request, url_for

from repositories import ContactoRepository, VehiculoRepository
from services import MOTIVOS, SERVICIOS, ContactoService

NOMBRE_SITIO = "Autobots"

app = Flask(__name__)
app.secret_key = "cambia-esta-clave-en-produccion"  

vehiculos_repo = VehiculoRepository()
contacto_service = ContactoService(ContactoRepository())


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
            return render_template("contactanos.html", motivos=MOTIVOS, servicios=SERVICIOS, datos=datos), 400
        flash("¡Gracias! Recibimos tu solicitud y te contactaremos pronto.", "ok")
        return redirect(url_for("contacto"))  

    
    datos = {"motivo": request.args.get("motivo", ""), "servicio": request.args.get("servicio", "")}
    return render_template("contactanos.html", motivos=MOTIVOS, servicios=SERVICIOS, datos=datos)


if __name__ == "__main__":
    app.run(debug=True)