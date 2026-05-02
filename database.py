"""
Módulo de Base de Datos - Sistema de Monitoreo de Calidad del Aire
Gestiona el almacenamiento y recuperación de datos de sensores IoT usando SQLite.
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "air_quality.db")


def get_connection() -> sqlite3.Connection:
    """Retorna una conexión a la base de datos SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Inicializa la base de datos y crea las tablas necesarias."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            pm25 REAL,
            co2 REAL,
            nox REAL,
            temperature REAL,
            humidity REAL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            predicted_at TEXT NOT NULL,
            target_timestamp TEXT NOT NULL,
            pm25_predicted REAL,
            co2_predicted REAL,
            model_version TEXT DEFAULT '1.0',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_readings_timestamp 
        ON sensor_readings(timestamp)
    """)
    
    conn.commit()
    conn.close()
    print(f"Base de datos inicializada en: {DB_PATH}")


def insert_reading(reading: dict) -> int:
    """Inserta una lectura de sensor en la base de datos."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sensor_readings (sensor_id, timestamp, pm25, co2, nox, temperature, humidity)
        VALUES (:sensor_id, :timestamp, :pm25, :co2, :nox, :temperature, :humidity)
    """, reading)
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id


def insert_readings_bulk(readings: List[dict]) -> int:
    """Inserta múltiples lecturas de sensores en la base de datos."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany("""
        INSERT INTO sensor_readings (sensor_id, timestamp, pm25, co2, nox, temperature, humidity)
        VALUES (:sensor_id, :timestamp, :pm25, :co2, :nox, :temperature, :humidity)
    """, readings)
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count


def get_recent_readings(hours: int = 24, limit: int = 200) -> List[dict]:
    """Obtiene las lecturas más recientes de la base de datos."""
    conn = get_connection()
    cursor = conn.cursor()
    since = (datetime.now() - timedelta(hours=hours)).isoformat()
    cursor.execute("""
        SELECT * FROM sensor_readings
        WHERE timestamp >= ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (since, limit))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_all_readings_for_training() -> List[dict]:
    """Obtiene todos los datos históricos para entrenar el modelo de IA."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp, pm25, co2, nox, temperature, humidity
        FROM sensor_readings
        ORDER BY timestamp ASC
    """)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def insert_prediction(prediction: dict) -> int:
    """Inserta una predicción del modelo de IA en la base de datos."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ai_predictions (predicted_at, target_timestamp, pm25_predicted, co2_predicted, model_version)
        VALUES (:predicted_at, :target_timestamp, :pm25_predicted, :co2_predicted, :model_version)
    """, prediction)
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id


def get_latest_predictions(limit: int = 24) -> List[dict]:
    """Obtiene las predicciones más recientes."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM ai_predictions
        ORDER BY target_timestamp ASC
        LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_stats() -> dict:
    """Obtiene estadísticas generales de la base de datos."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM sensor_readings")
    total = cursor.fetchone()["total"]
    cursor.execute("SELECT MIN(timestamp) as first, MAX(timestamp) as last FROM sensor_readings")
    row = cursor.fetchone()
    conn.close()
    return {
        "total_readings": total,
        "first_reading": row["first"],
        "last_reading": row["last"]
    }


if __name__ == "__main__":
    init_db()
    stats = get_stats()
    print("Estadísticas de la base de datos:", stats)
