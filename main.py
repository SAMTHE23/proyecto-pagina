from flask import Flask, render_template, request
from repositories import VehiculoRepository

NOMBRE_SITIO = "Autobots"

app = Flask(__name__)
vehiculos_repo = VehiculoRepository()


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


if __name__ == "__main__":
    app.run(debug=True)