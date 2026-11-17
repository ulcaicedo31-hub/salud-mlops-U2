from datetime import datetime, timezone
import http.client
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
import unittest

from app import Handler
from historial import Historial
from modelo import predecir


CASOS = [
    ((0, 0, 0), "NO ENFERMO"),
    ((3, 5, 2), "ENFERMEDAD LEVE"),
    ((8, 5, 2), "ENFERMEDAD AGUDA"),
    ((3, 120, 2), "ENFERMEDAD CRÓNICA"),
    ((9, 180, 8), "ENFERMEDAD TERMINAL"),
]


class PruebasModelo(unittest.TestCase):
    def test_cinco_categorias(self):
        for entrada, categoria in CASOS:
            with self.subTest(entrada=entrada):
                self.assertEqual(predecir(*entrada), categoria)

    def test_limites_de_categoria_terminal(self):
        for entrada in ((8.9, 180, 8), (9, 179.9, 8), (9, 180, 7)):
            with self.subTest(entrada=entrada):
                self.assertEqual(predecir(*entrada), "ENFERMEDAD CRÓNICA")


class PruebasReporte(unittest.TestCase):
    def setUp(self):
        temporal = TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        self.ruta = Path(temporal.name) / "pruebas.sqlite3"

        class HandlerPruebas(Handler):
            historial = Historial(self.ruta)

        self.servidor = ThreadingHTTPServer(("127.0.0.1", 0), HandlerPruebas)
        self.addCleanup(self.servidor.server_close)
        hilo = Thread(target=self.servidor.serve_forever, kwargs={"poll_interval": 0.01})
        hilo.start()
        self.addCleanup(hilo.join)
        self.addCleanup(self.servidor.shutdown)

    def solicitar(self, metodo, ruta, datos=None):
        conexion = http.client.HTTPConnection(
            "127.0.0.1", self.servidor.server_port, timeout=5
        )
        try:
            cuerpo = json.dumps(datos) if datos is not None else None
            conexion.request(metodo, ruta, cuerpo, {"Content-Type": "application/json"})
            respuesta = conexion.getresponse()
            return respuesta.status, json.load(respuesta)
        finally:
            conexion.close()

    def test_reporte_vacio_y_entradas_invalidas(self):
        codigo, _ = self.solicitar("POST", "/predecir", {"intensidad": 3})
        self.assertEqual(codigo, 400)
        codigo, reporte = self.solicitar("GET", "/estadisticas")
        self.assertEqual(codigo, 200)
        self.assertEqual(reporte, {
            "totales_por_categoria": {categoria: 0 for _, categoria in CASOS},
            "ultimas_5_predicciones": [],
            "fecha_ultima_prediccion": None,
        })

    def test_reporte_persistente_con_cinco_resultados_y_fecha(self):
        secuencia = CASOS + [CASOS[-1], CASOS[1]]
        inicio = datetime.now(timezone.utc).replace(microsecond=0)
        for (intensidad, dias, cantidad), esperado in secuencia:
            codigo, resultado = self.solicitar("POST", "/predecir", {
                "intensidad": intensidad,
                "duracion_dias": dias,
                "cantidad_sintomas": cantidad,
            })
            self.assertEqual(codigo, 200)
            self.assertEqual(resultado["estado"], esperado)

        codigo, reporte = self.solicitar("GET", "/estadisticas")
        self.assertEqual(codigo, 200)
        self.assertEqual(reporte["totales_por_categoria"], {
            "NO ENFERMO": 1,
            "ENFERMEDAD LEVE": 2,
            "ENFERMEDAD AGUDA": 1,
            "ENFERMEDAD CRÓNICA": 1,
            "ENFERMEDAD TERMINAL": 2,
        })
        ultimas = reporte["ultimas_5_predicciones"]
        self.assertEqual([fila["categoria"] for fila in ultimas],
                         [categoria for _, categoria in reversed(secuencia[-5:])])
        self.assertEqual(reporte["fecha_ultima_prediccion"], ultimas[0]["fecha"])
        fecha = datetime.fromisoformat(reporte["fecha_ultima_prediccion"])
        self.assertEqual(fecha.utcoffset(), timezone.utc.utcoffset(None))
        self.assertLessEqual(inicio, fecha)
        self.assertLessEqual(fecha, datetime.now(timezone.utc))
        self.assertEqual(Historial(self.ruta).reporte(), reporte)
