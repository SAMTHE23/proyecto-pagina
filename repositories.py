from abc import ABC, abstractmethod

from sqlalchemy import select, text

from database import CONTACTOS_SQL


class BaseRepository(ABC):
    """Contrato común: cualquier repositorio sabe listar y crear."""

    @abstractmethod
    def listar(self):
        ...

    @abstractmethod
    def crear(self, datos: dict):
        ...


class VehiculoRepository:
    def __init__(self, base):
        self.base = base
        self._tabla = "dbo.vehiculos" if base.motor.dialect.name == "mssql" else "vehiculos"

    def listar(self, busqueda=""):
        sql = f"SELECT * FROM {self._tabla}"
        params = {}
        if busqueda:
            sql += " WHERE LOWER(marca) LIKE LOWER(:q) OR LOWER(modelo) LIKE LOWER(:q) OR LOWER(tipo) LIKE LOWER(:q)"
            params = {"q": f"%{busqueda}%"}
        with self.base.conectar() as con:
            return con.execute(text(sql + " ORDER BY id"), params).mappings().all()

    def obtener(self, vehiculo_id):
        if not -2**63 <= vehiculo_id < 2**63:
            return None
        with self.base.conectar() as con:
            consulta = text(f"SELECT * FROM {self._tabla} WHERE id = :id")
            return con.execute(consulta, {"id": vehiculo_id}).mappings().one_or_none()


class ContactoRepository(BaseRepository):
    def __init__(self, base):
        self.base = base

    def listar(self):
        with self.base.conectar() as con:
            if con.dialect.name == "mssql":
                consulta = select(CONTACTOS_SQL).order_by(CONTACTOS_SQL.c.id.desc())
                return con.execute(consulta).mappings().all()
            return con.execute(text("SELECT * FROM contactos ORDER BY id DESC")).mappings().all()

    def crear(self, datos: dict):
        with self.base.conectar() as con:
            if con.dialect.name == "mssql":
                con.execute(CONTACTOS_SQL.insert(), datos)
                return
            con.execute(text(
                "INSERT INTO contactos (nombre, telefono, correo, motivo, servicio, fecha, mensaje) "
                "VALUES (:nombre, :telefono, :correo, :motivo, :servicio, :fecha, :mensaje)"
            ), datos)
