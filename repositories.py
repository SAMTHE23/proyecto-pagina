from database import Database


from database import Database


class VehiculoRepository:
    def listar(self, texto=""):
        sql, params = "SELECT * FROM vehiculos", []
        if texto:
            sql += " WHERE marca LIKE ? OR modelo LIKE ? OR tipo LIKE ?"
            params = [f"%{texto}%"] * 3
        with Database().conectar() as con:
            return con.execute(sql, params).fetchall()