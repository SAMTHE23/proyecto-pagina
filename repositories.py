from abc import ABC, abstractmethod

from sqlalchemy import MetaData, false, select, text

from database import CONTACTOS_SQL, VEHICULOS_SQL

TABLA_VEHICULOS = VEHICULOS_SQL.to_metadata(MetaData(), schema=None)


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
        sql_server = base.motor.dialect.name == "mssql"
        self._tabla = VEHICULOS_SQL if sql_server else TABLA_VEHICULOS
        self._limite_id = 2**63 if base.motor.dialect.name == "sqlite" else 2**31
        self._nombre_completo = "CONCAT(marca, ' ', modelo)" if sql_server else "marca || ' ' || modelo"

    def listar(self, busqueda=""):
        sql = f"SELECT * FROM {self._tabla.fullname}"
        params = {}
        if busqueda:
            sql += (
                " WHERE LOWER(marca) LIKE LOWER(:q)"
                " OR LOWER(modelo) LIKE LOWER(:q)"
                " OR LOWER(tipo) LIKE LOWER(:q)"
                f" OR LOWER({self._nombre_completo}) LIKE LOWER(:q)"
            )
            params = {"q": f"%{busqueda}%"}
        with self.base.conectar() as con:
            return con.execute(text(sql + " ORDER BY id"), params).mappings().all()

    def _por_id(self, vehiculo_id):
        if not -self._limite_id <= vehiculo_id < self._limite_id:
            return false()
        return self._tabla.c.id == vehiculo_id

    def obtener(self, vehiculo_id):
        with self.base.conectar() as con:
            consulta = select(self._tabla).where(self._por_id(vehiculo_id))
            return con.execute(consulta).mappings().one_or_none()

    def crear(self, datos):
        with self.base.conectar() as con:
            consulta = self._tabla.insert().returning(*self._tabla.c)
            return con.execute(consulta, datos).mappings().one()

    def actualizar(self, vehiculo_id, datos):
        if not datos:
            return self.obtener(vehiculo_id)
        with self.base.conectar() as con:
            consulta = (
                self._tabla.update()
                .where(self._por_id(vehiculo_id))
                .values(datos)
                .returning(*self._tabla.c)
            )
            return con.execute(consulta).mappings().one_or_none()

    def eliminar(self, vehiculo_id):
        with self.base.conectar() as con:
            consulta = (
                self._tabla.delete()
                .where(self._por_id(vehiculo_id))
                .returning(self._tabla.c.id)
            )
            return con.execute(consulta).scalar_one_or_none() is not None


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
