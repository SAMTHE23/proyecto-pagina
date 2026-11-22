import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from fastapi.testclient import TestClient
from sqlalchemy import text

from aplicacion import crear_app
from database import Database
from services import ContactoService

API = "/api/vehiculos"
TOKEN = "token-solo-pruebas"
AUTORIZADO = {"Authorization": f"Bearer {TOKEN}"}
CONTACTO = {
    "nombre": "Contacto de prueba",
    "telefono": "3001234567",
    "motivo": "Información general",
    "mensaje": "Solicitud de prueba",
}


class AplicacionTest(TestCase):
    def setUp(self):
        carpeta = self.enterContext(TemporaryDirectory())
        self.ruta = Path(carpeta) / "autobots-prueba.db"
        self.app = self.crear_app_prueba()
        self.cliente = self.enterContext(TestClient(self.app, base_url="https://autobots.test"))

    def crear_app_prueba(self, *, contenedor="", token=TOKEN, estrategia_imagen=None):
        return crear_app(
            clave_secreta="clave-solo-pruebas",
            url_contenedor=contenedor,
            api_token=token,
            estrategia_imagen=estrategia_imagen,
            crear_base=lambda: Database(
                url_conexion=os.environ.get("TEST_DATABASE_URL", ""),
                ruta_sqlite=self.ruta,
            ),
        )

    def test_paginas_y_archivos_estaticos(self):
        for ruta in ("/", "/catalogo", "/servicios", "/contacto", "/static/styles.css", "/static/img/logo.png"):
            with self.subTest(ruta=ruta):
                self.assertEqual(self.cliente.get(ruta).status_code, 200)

        vehiculo = self.cliente.get(API, params={"q": "Toyota Corolla"}).json()[0]
        ruta_ficha = f"/catalogo/{vehiculo['id']}"
        for consulta in ("corolla", "Toyota Corolla"):
            respuesta = self.cliente.get("/catalogo", params={"q": consulta})
            self.assertEqual(respuesta.status_code, 200)
            self.assertIn(f'href="{ruta_ficha}?', respuesta.text)

        ficha = self.cliente.get(ruta_ficha, params={"q": "Toyota Corolla"})
        self.assertEqual(ficha.status_code, 200)
        for texto in ("COP", "Transmisión", "/static/img/corolla.png", "/catalogo?q=Toyota+Corolla"):
            self.assertIn(texto, ficha.text)
        contacto = self.cliente.get("/contacto", params={"motivo": "Cotizar un vehículo", "vehiculo": vehiculo["id"]})
        self.assertIn("Toyota Corolla 2024", contacto.text)
        self.assertEqual(self.cliente.get("/catalogo/no-existe").status_code, 404)

    def test_imagenes_en_blob(self):
        blob = "https://prueba.blob.core.windows.net/imagenes"
        with TestClient(self.crear_app_prueba(contenedor=blob)) as cliente:
            vehiculo = cliente.get(API, params={"q": "Toyota Corolla"}).json()[0]
            ficha = cliente.get(f"/catalogo/{vehiculo['id']}")
            self.assertEqual(ficha.status_code, 200)
            self.assertIn(f"{blob}/corolla.png", ficha.text)

    def test_acepta_otra_estrategia_de_imagenes(self):
        def resolver_imagen(_request, nombre):
            return f"https://ejemplo.test/{nombre}"

        with TestClient(self.crear_app_prueba(estrategia_imagen=resolver_imagen)) as cliente:
            self.assertIn("https://ejemplo.test/corolla.png", cliente.get("/catalogo").text)

    def test_contacto_valida_guarda_y_confirma_una_vez(self):
        invalida = self.cliente.post("/contacto", data={**CONTACTO, "telefono": "12345"})
        self.assertEqual(invalida.status_code, 400)
        self.assertIn("entre 10 y 15", invalida.text)

        guardada = self.cliente.post("/contacto", data=CONTACTO, follow_redirects=False)
        self.assertEqual(guardada.status_code, 303)
        ruta = guardada.headers["Location"]
        self.assertEqual(ruta, "/contacto")
        self.assertIn("Recibimos tu solicitud", self.cliente.get(ruta).text)
        self.assertNotIn("Recibimos tu solicitud", self.cliente.get(ruta).text)

        repo = self.app.state.contacto_service.repositorio
        self.assertEqual(repo.listar()[0]["nombre"], CONTACTO["nombre"])

    def test_crud_vehiculos(self):
        datos = {"marca": "Autobots", "modelo": "Prueba", "anio": 2026, "precio_cop": 50000000}
        self.assertEqual(self.cliente.post(API, json=datos).status_code, 401)
        invalida = self.cliente.post(API, headers=AUTORIZADO, json={**datos, "precio_cop": -1})
        self.assertEqual(invalida.status_code, 422)

        creada = self.cliente.post(API, headers=AUTORIZADO, json=datos)
        self.assertEqual(creada.status_code, 201)
        id_vehiculo = creada.json()["id"]
        ruta = f"{API}/{id_vehiculo}"
        self.assertEqual(creada.headers["Location"], ruta)
        self.assertEqual(self.cliente.get(ruta).json()["precio_cop"], datos["precio_cop"])
        self.assertEqual(self.cliente.head(ruta).content, b"")

        parcial = self.cliente.patch(ruta, headers=AUTORIZADO, json={"precio_cop": None, "motor": "2.0 L"})
        self.assertEqual(parcial.status_code, 200)
        self.assertIsNone(parcial.json()["precio_cop"])
        self.assertEqual(parcial.json()["modelo"], datos["modelo"])
        self.assertEqual(parcial.json()["motor"], "2.0 L")
        self.assertEqual(self.cliente.patch(ruta, headers=AUTORIZADO, json={"marca": None}).status_code, 422)

        completa = self.cliente.put(ruta, headers=AUTORIZADO, json={"marca": "Autobots", "modelo": "Actualizado"})
        self.assertEqual(completa.status_code, 200)
        self.assertEqual(completa.json()["modelo"], "Actualizado")
        self.assertIsNone(completa.json()["motor"])
        self.assertIsNone(completa.json()["anio"])

        borrada = self.cliente.delete(ruta, headers=AUTORIZADO)
        self.assertEqual(borrada.status_code, 204)
        self.assertEqual(borrada.content, b"")
        self.assertEqual(self.cliente.get(ruta).status_code, 404)
        self.assertEqual(self.cliente.head(ruta).status_code, 404)

    def test_swagger_y_metodos_disponibles(self):
        self.assertEqual(self.cliente.get("/docs").status_code, 200)
        esquema = self.cliente.get("/openapi.json").json()
        for ruta, url, metodos in (
            (API, API, {"GET", "POST", "HEAD", "OPTIONS"}),
            (API + "/{vehiculo_id}", API + "/1", {"GET", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}),
        ):
            self.assertEqual(set(esquema["paths"][ruta]), {metodo.lower() for metodo in metodos})
            opciones = self.cliente.options(url)
            self.assertEqual(opciones.status_code, 204)
            self.assertEqual(set(opciones.headers["Allow"].split(", ")), metodos)
        self.assertIn("TokenVehiculos", esquema["components"]["securitySchemes"])

    def test_configuracion_sin_token_conserva_la_lectura(self):
        with TestClient(self.crear_app_prueba(token="")) as cliente:
            self.assertEqual(cliente.get(API).status_code, 200)
            self.assertEqual(cliente.post(API, json={"marca": "A", "modelo": "B"}).status_code, 503)

    def test_catalogo_vacio_permanece_vacio_al_reiniciar(self):
        ruta = self.ruta.with_name("vaciado.db")
        base = Database(url_conexion="", ruta_sqlite=ruta)
        try:
            with base.conectar() as con:
                con.execute(text("DELETE FROM vehiculos"))
        finally:
            base.motor.dispose()

        reiniciada = Database(url_conexion="", ruta_sqlite=ruta)
        try:
            with reiniciada.conectar() as con:
                self.assertEqual(con.execute(text("SELECT COUNT(*) FROM vehiculos")).scalar_one(), 0)
        finally:
            reiniciada.motor.dispose()


class ContactoServiceTest(TestCase):
    def test_acepta_un_registro_que_solo_expone_crear(self):
        class RegistroEnMemoria:
            def __init__(self):
                self.solicitudes = []

            def crear(self, datos):
                self.solicitudes.append(datos)

        registro = RegistroEnMemoria()
        datos, errores = ContactoService(registro).registrar(CONTACTO)
        self.assertEqual(errores, [])
        self.assertEqual(registro.solicitudes, [datos])
