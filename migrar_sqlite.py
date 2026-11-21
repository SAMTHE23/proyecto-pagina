

import argparse
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from database import CAMPOS_FICHA, CONTACTOS_SQL, VEHICULOS_SQL, motor_azure_sql, preparar_tablas_azure_sql


def copiar_tabla(origen, destino, tabla):
    columnas_origen = {columna["name"] for columna in origen.execute(f"PRAGMA table_info({tabla.name})")}
    columnas = ", ".join(
        nombre for nombre in tabla.c.keys() if nombre not in CAMPOS_FICHA or nombre in columnas_origen
    )
    copiados = 0
    for fila in origen.execute(f"SELECT {columnas} FROM {tabla.name} ORDER BY id"):
        datos = dict(fila)
        existente = destino.execute(
            select(tabla).where(tabla.c.id == datos["id"])
        ).mappings().one_or_none()
        if existente is None:
            destino.execute(tabla.insert(), datos)
            copiados += 1
        elif any(existente[campo] != valor for campo, valor in datos.items()):
            raise ValueError(f"El ID {datos['id']} de {tabla.name} ya contiene otros datos.")
    return copiados


def migrar(ruta, url):
    motor = motor_azure_sql(url)
    try:
        with closing(sqlite3.connect(ruta.resolve().as_uri() + "?mode=ro", uri=True)) as origen:
            origen.row_factory = sqlite3.Row
            origen.execute("BEGIN")
            with motor.begin() as destino:
                preparar_tablas_azure_sql(destino)
                return {
                    tabla.name: copiar_tabla(origen, destino, tabla)
                    for tabla in (VEHICULOS_SQL, CONTACTOS_SQL)
                }
    finally:
        motor.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archivo", type=Path, help="Ruta de la copia de autobot.db")
    args = parser.parse_args()
    url = os.environ.get("DATABASE_URL")
    if not url:
        parser.error("Configura DATABASE_URL con la conexión a Azure SQL.")
    try:
        copiados = migrar(args.archivo, url)
    except (ValueError, sqlite3.Error) as error:
        parser.exit(1, f"Migración cancelada: {error}\n")
    except SQLAlchemyError:
        parser.exit(1, "Migración cancelada. Revisa el controlador ODBC, la conexión y los permisos.\n")
    for tabla, cantidad in copiados.items():
        print(f"{tabla}: {cantidad} filas copiadas.")


if __name__ == "__main__":
    main()
