"""Servicio local de demostración sin dependencias externas."""
import json
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from historial import Historial
from modelo import predecir, VERSION


class Handler(BaseHTTPRequestHandler):
    historial = Historial(Path(os.getenv("HISTORIAL_DB", "datos/predicciones.sqlite3")))

    def respuesta(self, codigo, contenido, tipo="application/json; charset=utf-8"):
        datos = (json.dumps(contenido, ensure_ascii=False).encode("utf-8")
                 if isinstance(contenido, dict) else contenido)
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):
        if self.path == "/":
            self.respuesta(200, Path(__file__).with_name("index.html").read_bytes(),
                           "text/html; charset=utf-8")
        elif self.path == "/health":
            self.respuesta(200, {"estado": "ok", "version": VERSION})
        elif self.path == "/estadisticas":
            try:
                reporte = self.historial.reporte()
            except (OSError, sqlite3.Error):
                self.respuesta(503, {"error": "Historial no disponible"})
                return
            self.respuesta(200, reporte)
        else:
            self.respuesta(404, {"error": "Ruta no encontrada"})

    def do_POST(self):
        if self.path != "/predecir":
            self.respuesta(404, {"error": "Ruta no encontrada"})
            return
        if self.headers.get_content_type() != "application/json":
            self.respuesta(415, {"error": "Se requiere application/json"})
            return
        try:
            longitud = int(self.headers.get("Content-Length", "0"))
            if not 0 < longitud <= 4096:
                raise ValueError("Cuerpo vacío o mayor de 4096 bytes")
            datos = json.loads(self.rfile.read(longitud))
            campos = {"intensidad", "duracion_dias", "cantidad_sintomas"}
            if not isinstance(datos, dict) or set(datos) != campos:
                raise ValueError("Envíe exactamente: " + ", ".join(sorted(campos)))
            estado = predecir(**datos)
        except (ValueError, UnicodeError) as error:
            self.respuesta(400, {"error": str(error)})
            return
        try:
            self.historial.registrar(estado)
        except (OSError, sqlite3.Error):
            self.respuesta(503, {"error": "Historial no disponible"})
            return
        self.respuesta(200, {"estado": estado, "version": VERSION,
                             "aviso": "Simulación académica sin validez clínica"})

    def log_message(self, formato, *args):
        # No registrar datos ni cuerpos de las solicitudes.
        pass


if __name__ == "__main__":
    servidor = ThreadingHTTPServer((os.getenv("HOST", "127.0.0.1"),
                                   int(os.getenv("PORT", "5000"))), Handler)
    print("Servicio disponible en puerto 5000", flush=True)
    servidor.serve_forever()
