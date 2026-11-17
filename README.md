# Taller 1 — Pipeline de MLOps + imagen Docker

Entrega para el problema de enfermedades comunes y huérfanas. La propuesta completa, con diagrama y etapas, se encuentra en [PIPELINE.md](pipeline/PIPELINE.md).

## Finalidad

Servicio académico con una página web y una API que reciben tres valores y devuelven uno de los cuatro estados requeridos. La función es determinista y ficticia: no se entrenó un modelo, de acuerdo con el enunciado. No usar con pacientes ni interpretar sus resultados como diagnósticos.

## Archivos

```text
entrega_mlops/
  pipeline/
    PIPELINE.md             Propuesta y explicación de etapas
    diagrama_pipeline.png   Imagen del pipeline
  README.md                 Instrucciones de construcción y uso
  Dockerfile                Construcción y arranque del servicio
  .dockerignore             Exclusiones del contexto
  modelo.py                 Función simulada
  app.py                    Servicio HTTP y API
  index.html                Formulario web
```

No requiere bibliotecas externas: utiliza Python y su biblioteca estándar.

## Construir y ejecutar con Docker

1. Instalar Docker Engine o Docker Desktop y arrancarlo. En Windows, utilizar contenedores Linux. Se necesita conexión para descargar la imagen base la primera vez.
2. Extraer el ZIP y abrir una terminal **dentro de `entrega_mlops`**, donde está el Dockerfile.
3. Construir la imagen:

```sh
docker build -t mlops-salud:1.0 .
```

4. Lanzar el servicio:

```sh
docker run --rm -d --name mlops-salud -p 127.0.0.1:5000:5000 mlops-salud:1.0
```

5. Abrir [http://localhost:5000](http://localhost:5000), completar los tres campos y pulsar **Obtener respuesta**. El resultado aparece debajo del botón.
6. Consultar estado y detener:

```sh
docker ps
docker inspect --format='{{.State.Health.Status}}' mlops-salud
docker stop mlops-salud
```

El estado puede aparecer como `starting` durante los primeros segundos. El puerto se publica solo en el equipo local. Si está ocupado, usar `-p 127.0.0.1:5001:5000` y abrir el puerto 5001. La aplicación corre con usuario sin privilegios. El servidor estándar es suficiente para esta demostración local; un despliegue clínico necesita una arquitectura adicional.

## Entradas y reglas

| Campo JSON | Tipo y rango | Significado simulado |
|---|---|---|
| `intensidad` | Número finito, 0 a 10 | Intensidad de síntomas |
| `duracion_dias` | Número finito, 0 a 36500 | Duración |
| `cantidad_sintomas` | Entero, 0 a 100 | Cantidad de síntomas |

Se exigen exactamente estos tres campos; no se aceptan cadenas ni booleanos. Sin síntomas, intensidad y duración deben ser cero. Las reglas se evalúan en este orden:

1. Cantidad cero, intensidad cero y duración cero: **NO ENFERMO**.
2. Con síntomas y duración ≥ 90: **ENFERMEDAD CRÓNICA**.
3. Con síntomas, duración < 90 e intensidad ≥ 7 o cantidad ≥ 5: **ENFERMEDAD AGUDA**.
4. Los demás casos válidos: **ENFERMEDAD LEVE**.

Los umbrales son decisiones de programación sin fundamento clínico. La prioridad de duración resuelve los casos con duración e intensidad altas.

| Intensidad | Días | Cantidad | Respuesta esperada |
|---:|---:|---:|---|
| 0 | 0 | 0 | NO ENFERMO |
| 3 | 5 | 2 | ENFERMEDAD LEVE |
| 8 | 5 | 2 | ENFERMEDAD AGUDA |
| 3 | 120 | 2 | ENFERMEDAD CRÓNICA |

## API y ejemplos

`GET /health` devuelve HTTP 200 y `{"estado":"ok","version":"simulador-1.0"}`.

`POST /predecir` recibe JSON. Ejemplo en PowerShell:

```powershell
$datos = @{intensidad=8; duracion_dias=5; cantidad_sintomas=2} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:5000/predecir -Method Post -ContentType 'application/json' -Body $datos
```

Ejemplo en Bash:

```sh
curl -X POST http://localhost:5000/predecir -H 'Content-Type: application/json' -d '{"intensidad":8,"duracion_dias":5,"cantidad_sintomas":2}'
```

Respuesta esperada, HTTP 200:

```json
{"estado":"ENFERMEDAD AGUDA","version":"simulador-1.0","aviso":"Simulación académica sin validez clínica"}
```

Datos inválidos o JSON mal formado devuelven HTTP 400 con `error`; un tipo de contenido diferente devuelve 415; rutas inexistentes devuelven 404. Se limita el cuerpo a 4096 bytes. La aplicación no almacena las entradas.

## Ejecución alternativa sin Docker

Con Python 3.12 o superior, desde esta carpeta:

```sh
python app.py
```

Abrir http://localhost:5000 y detener con Ctrl+C. No se necesita instalar bibliotecas externas.

## Comprobación manual

Introducir en el formulario los cuatro ejemplos de la tabla anterior y comprobar que cada uno devuelve el estado esperado. La propuesta del pipeline está en `pipeline/PIPELINE.md` y su diagrama en `pipeline/diagrama_pipeline.png`.
