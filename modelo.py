"""Simulador académico determinista; sus reglas no tienen validez clínica."""
import math

VERSION = "simulador-2.0"
CATEGORIAS = (
    "NO ENFERMO",
    "ENFERMEDAD LEVE",
    "ENFERMEDAD AGUDA",
    "ENFERMEDAD CRÓNICA",
    "ENFERMEDAD TERMINAL",
)


def predecir(intensidad, duracion_dias, cantidad_sintomas):
    valores = (intensidad, duracion_dias, cantidad_sintomas)
    limites = ((0, 10), (0, 36500), (0, 100))
    for nombre, valor, (minimo, maximo) in zip(
        ("intensidad", "duracion_dias", "cantidad_sintomas"), valores, limites
    ):
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ValueError(f"{nombre} debe ser numérico")
        if not math.isfinite(valor) or not minimo <= valor <= maximo:
            raise ValueError(f"{nombre} debe estar entre {minimo} y {maximo}")
    if not isinstance(cantidad_sintomas, int):
        raise ValueError("cantidad_sintomas debe ser un entero")
    if cantidad_sintomas == 0 and (intensidad != 0 or duracion_dias != 0):
        raise ValueError("Sin síntomas, intensidad y duración deben ser cero")
    if cantidad_sintomas == 0:
        return "NO ENFERMO"
    if intensidad >= 9 and duracion_dias >= 180 and cantidad_sintomas >= 8:
        return "ENFERMEDAD TERMINAL"
    if duracion_dias >= 90:
        return "ENFERMEDAD CRÓNICA"
    if intensidad >= 7 or cantidad_sintomas >= 5:
        return "ENFERMEDAD AGUDA"
    return "ENFERMEDAD LEVE"
