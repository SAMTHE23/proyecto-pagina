from abc import ABC, abstractmethod

from database import Database


class BaseRepository(ABC):
    """Contrato común: cualquier repositorio sabe listar y crear."""

    @abstractmethod
    def listar(self):
        ...

    @abstractmethod
    def crear(self, datos: dict):
        ...


class VehiculoRepository:
    def listar(self, texto=""):
        sql, params = "SELECT * FROM vehiculos", []
        if texto:
            sql += " WHERE marca LIKE ? OR modelo LIKE ? OR tipo LIKE ?"
            params = [f"%{texto}%"] * 3
        with Database().conectar() as con:
            return con.execute(sql, params).fetchall()


class ContactoRepository(BaseRepository):
    def listar(self):
        with Database().conectar() as con:
            return con.execute("SELECT * FROM contactos ORDER BY id DESC").fetchall()

    def crear(self, datos: dict):
        with Database().conectar() as con:
            con.execute(
                "INSERT INTO contactos (nombre, telefono, correo, motivo, servicio, fecha, mensaje) "
                "VALUES (:nombre, :telefono, :correo, :motivo, :servicio, :fecha, :mensaje)",
                datos)