from abc import ABC, abstractmethod

from sqlalchemy import text


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

    def listar(self, busqueda=""):
        sql = "SELECT * FROM vehiculos"
        params = {}
        if busqueda:
            sql += " WHERE LOWER(marca) LIKE LOWER(:q) OR LOWER(modelo) LIKE LOWER(:q) OR LOWER(tipo) LIKE LOWER(:q)"
            params = {"q": f"%{busqueda}%"}
        with self.base.conectar() as con:
            return con.execute(text(sql + " ORDER BY id"), params).mappings().all()


class ContactoRepository(BaseRepository):
    def __init__(self, base):
        self.base = base

    def listar(self):
        with self.base.conectar() as con:
            return con.execute(text("SELECT * FROM contactos ORDER BY id DESC")).mappings().all()

    def crear(self, datos: dict):
        with self.base.conectar() as con:
            con.execute(text(
                "INSERT INTO contactos (nombre, telefono, correo, motivo, servicio, fecha, mensaje) "
                "VALUES (:nombre, :telefono, :correo, :motivo, :servicio, :fecha, :mensaje)"
            ), datos)
