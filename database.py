import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import (
    BigInteger, Column, Integer, MetaData, Table, Unicode, UnicodeText, create_engine,
    inspect, text,
)
from sqlalchemy.engine import URL, make_url
from sqlalchemy.schema import CreateColumn

CAMPOS_FICHA = ("precio_cop", "motor", "transmision", "combustible")

# Los precios y las especificaciones son datos de ejemplo para el catálogo inicial.
VEHICULOS_INICIALES = [
    {
        "marca": "Toyota", "modelo": "Corolla", "anio": 2024, "tipo": "Sedán", "imagen": "corolla.png",
        "precio_cop": 105_900_000, "motor": "2.0 L", "transmision": "Automática CVT", "combustible": "Gasolina",
    },
    {
        "marca": "Mazda", "modelo": "MX-5", "anio": 2025, "tipo": "Deportivo", "imagen": "mazda.png",
        "precio_cop": 154_900_000, "motor": "2.0 L", "transmision": "Manual", "combustible": "Gasolina",
    },
    {
        "marca": "Chevrolet", "modelo": "Equinox", "anio": 2024, "tipo": "SUV", "imagen": "equinox.png",
        "precio_cop": 132_900_000, "motor": "1.5 L turbo", "transmision": "Automática", "combustible": "Gasolina",
    },
]


ESQUEMA_AZURE_SQL = MetaData(schema="dbo")
VEHICULOS_SQL = Table(
    "vehiculos", ESQUEMA_AZURE_SQL,
    Column("id", Integer, primary_key=True),
    Column("marca", UnicodeText),
    Column("modelo", UnicodeText),
    Column("anio", Integer),
    Column("tipo", UnicodeText),
    Column("imagen", UnicodeText),
    Column("precio_cop", BigInteger),
    Column("motor", Unicode(120)),
    Column("transmision", Unicode(120)),
    Column("combustible", Unicode(120)),
)
CONTACTOS_SQL = Table(
    "contactos", ESQUEMA_AZURE_SQL,
    Column("id", Integer, primary_key=True),
    Column("nombre", UnicodeText, nullable=False),
    Column("telefono", UnicodeText, nullable=False),
    Column("correo", UnicodeText),
    Column("motivo", UnicodeText, nullable=False),
    Column("servicio", UnicodeText),
    Column("fecha", UnicodeText),
    Column("mensaje", UnicodeText),
    Column("creado", UnicodeText, server_default=text("CONVERT(nvarchar(19), SYSUTCDATETIME(), 120)")),
)


def agregar_campos_ficha(con, esquema=None):
    existentes = {columna["name"] for columna in inspect(con).get_columns("vehiculos", schema=esquema)}
    faltantes = [campo for campo in CAMPOS_FICHA if campo not in existentes]
    if not faltantes:
        return

    tabla = "dbo.vehiculos" if esquema else "vehiculos"
    for campo in faltantes:
        definicion = CreateColumn(VEHICULOS_SQL.c[campo]).compile(dialect=con.dialect)
        con.execute(text(f"ALTER TABLE {tabla} ADD {definicion}"))

    # Solo completa columnas nuevas de los tres registros de demostración originales.
    asignaciones = ", ".join(f"{campo} = :{campo}" for campo in faltantes)
    con.execute(text(
        f"UPDATE {tabla} SET {asignaciones} WHERE marca = :marca AND modelo = :modelo "
        "AND anio = :anio AND tipo = :tipo AND imagen = :imagen"
    ), VEHICULOS_INICIALES)


def motor_azure_sql(url):
    conexion = make_url(url)
    if conexion.drivername != "mssql+pyodbc":
        raise ValueError("Usa una URL mssql+pyodbc para Azure SQL.")
    return create_engine(conexion, pool_pre_ping=True, deprecate_large_types=True)


def preparar_tablas_azure_sql(con):
    resultado = con.execute(text(
        "SET NOCOUNT ON; IF @@TRANCOUNT = 0 BEGIN TRANSACTION; "
        "DECLARE @resultado int; "
        "EXEC @resultado = sys.sp_getapplock "
        "@Resource = 'autobots:esquema', @LockMode = 'Exclusive', "
        "@LockOwner = 'Transaction', @LockTimeout = 30000; "
        "SELECT @resultado;"
    )).scalar_one()
    if resultado < 0:
        raise RuntimeError("No se pudo obtener el bloqueo de inicialización de Azure SQL.")
    tabla_nueva = not inspect(con).has_table("vehiculos", schema="dbo")
    ESQUEMA_AZURE_SQL.create_all(con)
    agregar_campos_ficha(con, esquema="dbo")
    return tabla_nueva


class Database:
    def __init__(self, *, url_conexion: str | None = None, ruta_sqlite: Path | None = None):
        url = os.environ.get("DATABASE_URL") if url_conexion is None else url_conexion
        if url and make_url(url).drivername == "mssql+pyodbc":
            self.motor = motor_azure_sql(url)
        else:
            if url:
                conexion = make_url(url)
                if conexion.drivername not in {"postgresql", "postgresql+psycopg"}:
                    raise RuntimeError("DATABASE_URL debe apuntar a Azure SQL (mssql+pyodbc) o PostgreSQL.")
                conexion = conexion.set(drivername="postgresql+psycopg")
            elif ruta_sqlite is None and os.environ.get("WEBSITE_SITE_NAME"):
                raise RuntimeError("Configura DATABASE_URL con la conexión a la base de datos en Azure.")
            else:
                ruta = ruta_sqlite or Path(__file__).with_name("autobot.db")
                conexion = URL.create("sqlite", database=str(ruta))
            self.motor = create_engine(conexion, pool_pre_ping=True)
        self._crear_tablas()

    @contextmanager
    def conectar(self):
        with self.motor.begin() as con:
            yield con

    def _crear_tablas(self):
        with self.conectar() as con:
            if con.dialect.name == "mssql":
                if preparar_tablas_azure_sql(con):
                    con.execute(VEHICULOS_SQL.insert(), VEHICULOS_INICIALES)
                return
            if con.dialect.name == "postgresql":
                
                con.execute(text("SELECT pg_advisory_xact_lock(7143085721)"))
                clave = "INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY"
                fecha_creacion = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            else:
                con.exec_driver_sql("BEGIN IMMEDIATE")
                clave = "INTEGER PRIMARY KEY AUTOINCREMENT"
                fecha_creacion = "TEXT DEFAULT CURRENT_TIMESTAMP"

            tabla_nueva = not inspect(con).has_table("vehiculos")
            con.execute(text(
                f"CREATE TABLE IF NOT EXISTS vehiculos (id {clave}, "
                "marca TEXT, modelo TEXT, anio INTEGER, tipo TEXT, imagen TEXT, "
                "precio_cop BIGINT, motor TEXT, transmision TEXT, combustible TEXT)"
            ))
            agregar_campos_ficha(con)
            con.execute(text(
                f"CREATE TABLE IF NOT EXISTS contactos (id {clave}, nombre TEXT NOT NULL, "
                "telefono TEXT NOT NULL, correo TEXT, motivo TEXT NOT NULL, "
                f"servicio TEXT, fecha TEXT, mensaje TEXT, creado {fecha_creacion})"
            ))
            if tabla_nueva:
                con.execute(text(
                    "INSERT INTO vehiculos "
                    "(marca, modelo, anio, tipo, imagen, precio_cop, motor, transmision, combustible) "
                    "VALUES (:marca, :modelo, :anio, :tipo, :imagen, :precio_cop, :motor, :transmision, :combustible)"
                ), VEHICULOS_INICIALES)
