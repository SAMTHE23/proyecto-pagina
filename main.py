from flask import Flask, render_template, request

NOMBRE_SITIO = "Autobots"

app = Flask(__name__)

VEHICULOS = [
    {"id": 1, "marca": "Toyota", "modelo": "Corolla", "anio": 2024, "tipo": "Sedán", "imagen": "corolla.png"},
    {"id": 2, "marca": "Mazda", "modelo": "MX-5", "anio": 2025, "tipo": "Deportivo", "imagen": "mazda.png"},
    {"id": 3, "marca": "Chevrolet", "modelo": "Equinox", "anio": 2024, "tipo": "SUV", "imagen": "equinox.png"},
]


@app.get("/")
def home():
    return render_template("index.html", nombre=NOMBRE_SITIO)


@app.get("/catalogo")
def catalogo():
    busqueda = request.args.get("q", "").strip()
    q = busqueda.lower()
    if q:
        resultados = [
            v for v in VEHICULOS
            if q in v["marca"].lower() or q in v["modelo"].lower() or q in v["tipo"].lower()
        ]
    else:
        resultados = VEHICULOS
    return render_template("catalogo.html", vehiculos=resultados, busqueda=busqueda)


if __name__ == "__main__":
    app.run(debug=True)