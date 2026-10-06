import sqlite3
from contextlib import contextmanager
from pathlib import Path

VEHICULOS_INICIALES = [
    ("Toyota", "Corolla", 2024, "Sedán", "corolla.png"),
    ("Mazda", "MX-5", 2025, "Deportivo", "mazda.png"),
    ("Chevrolet", "Equinox", 2024, "SUV", "equinox.png"),
]


class Database:
    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia.ruta = Path(__file__).with_name("autobot.db")
            cls._instancia._crear_tablas()
        return cls._instancia

    @contextmanager
    def conectar(self):
        con = sqlite3.connect(self.ruta)
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def _crear_tablas(self):
        with self.conectar() as con:
            con.execute(
                "CREATE TABLE IF NOT EXISTS vehiculos ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, marca TEXT, modelo TEXT, "
                "anio INTEGER, tipo TEXT, imagen TEXT)")
            if con.execute("SELECT COUNT(*) FROM vehiculos").fetchone()[0] == 0:
                con.executemany(
                    "INSERT INTO vehiculos (marca, modelo, anio, tipo, imagen) VALUES (?,?,?,?,?)",
                    VEHICULOS_INICIALES)