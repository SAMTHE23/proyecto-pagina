from flask import Flask, render_template

NOMBRE_SITIO = "Autobots"

app = Flask(__name__)


@app.get("/")
def home():
    return render_template("index.html", nombre=NOMBRE_SITIO)


if __name__ == "__main__":
    app.run(debug=True)