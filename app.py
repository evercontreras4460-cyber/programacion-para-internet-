"""
API REST Backend - Sistema de Monitoreo de Calidad del Aire (IoT + IA)
Servidor FastAPI que expone endpoints para recibir datos de sensores,
consultar histórico y obtener predicciones del modelo de IA.
"""

import sys
import os
import json
import threading
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List

from database import (
    init_db, insert_reading, get_recent_readings,
    get_all_readings_for_training, insert_prediction,
    get_latest_predictions, get_stats
)
from iot_simulator import simulate_sensor_reading, generate_historical_data
from ai_model import train_model, predict_next_hours, get_air_quality_index, load_model

# ─────────────────────────────────────────────
# Inicialización de la aplicación
# ─────────────────────────────────────────────
app = FastAPI(
    title="Sistema de Monitoreo de Calidad del Aire",
    description="API REST para monitoreo IoT + predicciones con IA",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos estáticos del frontend
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# ─────────────────────────────────────────────
# Modelos Pydantic
# ─────────────────────────────────────────────
class SensorReading(BaseModel):
    sensor_id: str = "ESP32_001"
    timestamp: Optional[str] = None
    pm25: float
    co2: float
    nox: float
    temperature: float
    humidity: float


# ─────────────────────────────────────────────
# Simulación automática de sensores (background)
# ─────────────────────────────────────────────
_simulation_active = False
_simulation_thread = None

def auto_simulate():
    """Genera lecturas simuladas cada 30 segundos en background."""
    global _simulation_active
    while _simulation_active:
        reading = simulate_sensor_reading()
        insert_reading(reading)
        time.sleep(30)

# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@app.get("/")
async def root():
    """Sirve el dashboard principal."""
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/api/health")
async def health_check():
    """Verificación del estado del servidor."""
    return {"status": "online", "timestamp": datetime.now().isoformat(), "version": "1.0.0"}


@app.post("/api/sensor/reading")
async def receive_reading(reading: SensorReading):
    """
    Endpoint para recibir datos de sensores IoT.
    En un sistema real, el ESP32 enviaría datos a este endpoint vía HTTP POST.
    """
    data = reading.dict()
    if not data.get("timestamp"):
        data["timestamp"] = datetime.now().isoformat()
    row_id = insert_reading(data)
    aqi = get_air_quality_index(data["pm25"])
    return {
        "success": True,
        "id": row_id,
        "air_quality": aqi,
        "message": f"Lectura registrada. Calidad del aire: {aqi['level']}"
    }


@app.get("/api/sensor/readings")
async def get_readings(hours: int = 24, limit: int = 200):
    """Obtiene las lecturas recientes de los sensores."""
    readings = get_recent_readings(hours=hours, limit=limit)
    # Invertir para orden cronológico ascendente (para gráficos)
    readings.reverse()
    return {"data": readings, "count": len(readings)}


@app.get("/api/sensor/latest")
async def get_latest():
    """Obtiene la lectura más reciente del sensor."""
    readings = get_recent_readings(hours=1, limit=1)
    if not readings:
        # Generar una lectura simulada si no hay datos
        reading = simulate_sensor_reading()
        insert_reading(reading)
        readings = [reading]
    latest = readings[0]
    aqi = get_air_quality_index(latest.get("pm25", 0))
    return {"reading": latest, "air_quality": aqi}


@app.get("/api/predictions")
async def get_predictions():
    """Obtiene las predicciones más recientes del modelo de IA."""
    predictions = get_latest_predictions(limit=24)
    return {"predictions": predictions, "count": len(predictions)}


@app.post("/api/predictions/generate")
async def generate_predictions():
    """Genera nuevas predicciones usando el modelo de IA entrenado."""
    readings = get_recent_readings(hours=2, limit=1)
    if not readings:
        raise HTTPException(status_code=404, detail="No hay lecturas recientes para generar predicciones.")
    
    last_reading = readings[0]
    try:
        predictions = predict_next_hours(last_reading, hours_ahead=12)
        for pred in predictions:
            insert_prediction(pred)
        return {"success": True, "predictions": predictions, "count": len(predictions)}
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Modelo de IA no entrenado. Ejecuta /api/model/train primero.")


@app.post("/api/model/train")
async def train_ai_model(background_tasks: BackgroundTasks):
    """Entrena el modelo de IA con los datos históricos almacenados."""
    records = get_all_readings_for_training()
    if len(records) < 100:
        raise HTTPException(
            status_code=400,
            detail=f"Datos insuficientes para entrenamiento. Se tienen {len(records)} registros, se necesitan al menos 100."
        )
    
    def do_train():
        metrics = train_model(records)
        print(f"Entrenamiento completado: {json.dumps(metrics)}")
    
    background_tasks.add_task(do_train)
    return {"success": True, "message": f"Entrenamiento iniciado con {len(records)} registros.", "status": "training"}


@app.get("/api/model/metrics")
async def get_model_metrics():
    """Obtiene las métricas del modelo de IA entrenado."""
    metrics_path = os.path.join(os.path.dirname(__file__), "..", "models", "metrics.json")
    if not os.path.exists(metrics_path):
        raise HTTPException(status_code=404, detail="Modelo no entrenado aún.")
    with open(metrics_path) as f:
        metrics = json.load(f)
    return metrics


@app.get("/api/stats")
async def get_database_stats():
    """Obtiene estadísticas generales del sistema."""
    stats = get_stats()
    return stats


@app.post("/api/simulation/start")
async def start_simulation():
    """Inicia la simulación automática de sensores IoT."""
    global _simulation_active, _simulation_thread
    if _simulation_active:
        return {"message": "Simulación ya está activa."}
    _simulation_active = True
    _simulation_thread = threading.Thread(target=auto_simulate, daemon=True)
    _simulation_thread.start()
    return {"success": True, "message": "Simulación de sensores IoT iniciada (cada 30 segundos)."}


@app.post("/api/simulation/stop")
async def stop_simulation():
    """Detiene la simulación automática de sensores IoT."""
    global _simulation_active
    _simulation_active = False
    return {"success": True, "message": "Simulación detenida."}


@app.get("/api/simulation/status")
async def simulation_status():
    """Verifica si la simulación está activa."""
    return {"active": _simulation_active}


if __name__ == "__main__":
    import uvicorn
    
    # Inicializar base de datos
    init_db()
    
    # Cargar datos históricos si la BD está vacía
    stats = get_stats()
    if stats["total_readings"] == 0:
        print("Base de datos vacía. Generando datos históricos de 30 días...")
        data = generate_historical_data(days=30)
        insert_readings_bulk_fn = __import__("database", fromlist=["insert_readings_bulk"]).insert_readings_bulk
        insert_readings_bulk_fn(data)
        print(f"Se generaron {len(data)} registros históricos.")
    
    # Entrenar modelo si no existe
    model_path = os.path.join(os.path.dirname(__file__), "..", "models", "air_quality_model.pkl")
    if not os.path.exists(model_path):
        print("Entrenando modelo de IA...")
        records = get_all_readings_for_training()
        train_model(records)
    
    print("Iniciando servidor en http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
