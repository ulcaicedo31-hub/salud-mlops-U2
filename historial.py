"""Historial persistente de resultados simulados y fechas en UTC."""
from contextlib import closing
from datetime import datetime, timezone
import sqlite3

from modelo import CATEGORIAS


class Historial:
    def __init__(self, ruta):
        self.ruta = ruta

    def conectar(self):
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        conexion = sqlite3.connect(self.ruta)
        try:
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS predicciones (
                    id INTEGER PRIMARY KEY,
                    categoria TEXT NOT NULL,
                    fecha TEXT NOT NULL
                )
            """)
        except sqlite3.Error:
            conexion.close()
            raise
        return conexion

    def registrar(self, categoria):
        with closing(self.conectar()) as conexion, conexion:
            # Serializar las escrituras antes de asignar la fecha.
            conexion.execute("BEGIN IMMEDIATE")
            fecha = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
            conexion.execute(
                "INSERT INTO predicciones (categoria, fecha) VALUES (?, ?)",
                (categoria, fecha),
            )

    def reporte(self):
        totales = dict.fromkeys(CATEGORIAS, 0)
        with closing(self.conectar()) as conexion, conexion:
            conexion.execute("BEGIN")
            totales.update(conexion.execute(
                "SELECT categoria, COUNT(*) FROM predicciones GROUP BY categoria"
            ))
            ultimas = [
                {"categoria": categoria, "fecha": fecha}
                for categoria, fecha in conexion.execute(
                    "SELECT categoria, fecha FROM predicciones ORDER BY id DESC LIMIT 5"
                )
            ]
        return {
            "totales_por_categoria": totales,
            "ultimas_5_predicciones": ultimas,
            "fecha_ultima_prediccion": ultimas[0]["fecha"] if ultimas else None,
        }
