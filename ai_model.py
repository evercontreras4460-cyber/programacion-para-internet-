"""
Módulo de Inteligencia Artificial - Sistema de Monitoreo de Calidad del Aire
Implementa un modelo de Machine Learning para predecir niveles de contaminantes.
Utiliza scikit-learn con un modelo de Gradient Boosting para predicciones robustas.
"""

import os
import json
import pickle
import math
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "air_quality_model.pkl")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "scaler.pkl")
METRICS_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "metrics.json")


def extract_features(timestamp_str: str, temperature: float, humidity: float,
                     pm25_lag1: float = 0.0, co2_lag1: float = 0.0) -> List[float]:
    """
    Extrae características (features) a partir de una lectura de sensor.
    Incluye características temporales y lecturas previas (lag features).
    
    Args:
        timestamp_str: Timestamp en formato ISO.
        temperature: Temperatura en °C.
        humidity: Humedad relativa en %.
        pm25_lag1: Valor de PM2.5 de la lectura anterior.
        co2_lag1: Valor de CO2 de la lectura anterior.
    
    Returns:
        Lista de características numéricas para el modelo.
    """
    dt = datetime.fromisoformat(timestamp_str)
    hour = dt.hour
    day_of_week = dt.weekday()  # 0=Lunes, 6=Domingo
    month = dt.month
    
    # Codificación cíclica de la hora (para capturar periodicidad)
    hour_sin = math.sin(2 * math.pi * hour / 24)
    hour_cos = math.cos(2 * math.pi * hour / 24)
    
    # Codificación cíclica del día de la semana
    dow_sin = math.sin(2 * math.pi * day_of_week / 7)
    dow_cos = math.cos(2 * math.pi * day_of_week / 7)
    
    # Indicador de hora pico (7-9am y 5-7pm)
    is_peak_hour = 1.0 if (7 <= hour <= 9 or 17 <= hour <= 19) else 0.0
    
    # Indicador de fin de semana
    is_weekend = 1.0 if day_of_week >= 5 else 0.0
    
    return [
        hour_sin, hour_cos,
        dow_sin, dow_cos,
        month,
        temperature,
        humidity,
        is_peak_hour,
        is_weekend,
        pm25_lag1,
        co2_lag1,
    ]


def prepare_training_data(records: List[dict]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepara los datos históricos para el entrenamiento del modelo.
    
    Args:
        records: Lista de registros históricos de sensores.
    
    Returns:
        Tupla (X, y_pm25, y_co2) con features y targets.
    """
    X, y_pm25, y_co2 = [], [], []
    
    for i in range(1, len(records)):
        rec = records[i]
        prev = records[i - 1]
        
        features = extract_features(
            timestamp_str=rec["timestamp"],
            temperature=rec["temperature"],
            humidity=rec["humidity"],
            pm25_lag1=prev["pm25"],
            co2_lag1=prev["co2"]
        )
        X.append(features)
        y_pm25.append(rec["pm25"])
        y_co2.append(rec["co2"])
    
    return np.array(X), np.array(y_pm25), np.array(y_co2)


def train_model(records: List[dict]) -> dict:
    """
    Entrena el modelo de IA con los datos históricos.
    Usa Gradient Boosting Regressor para PM2.5 y CO2.
    
    Args:
        records: Lista de registros históricos.
    
    Returns:
        Diccionario con métricas de evaluación del modelo.
    """
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    
    print(f"Preparando datos de entrenamiento con {len(records)} registros...")
    X, y_pm25, y_co2 = prepare_training_data(records)
    
    # División entrenamiento/prueba (80/20)
    X_train, X_test, y_pm25_train, y_pm25_test = train_test_split(
        X, y_pm25, test_size=0.2, random_state=42
    )
    _, _, y_co2_train, y_co2_test = train_test_split(
        X, y_co2, test_size=0.2, random_state=42
    )
    
    # Normalización de características
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Entrenamiento del modelo para PM2.5
    print("Entrenando modelo para PM2.5...")
    model_pm25 = GradientBoostingRegressor(
        n_estimators=150, learning_rate=0.1, max_depth=4, random_state=42
    )
    model_pm25.fit(X_train_scaled, y_pm25_train)
    
    # Entrenamiento del modelo para CO2
    print("Entrenando modelo para CO2...")
    model_co2 = GradientBoostingRegressor(
        n_estimators=150, learning_rate=0.1, max_depth=4, random_state=42
    )
    model_co2.fit(X_train_scaled, y_co2_train)
    
    # Evaluación del modelo
    pm25_pred = model_pm25.predict(X_test_scaled)
    co2_pred = model_co2.predict(X_test_scaled)
    
    metrics = {
        "pm25": {
            "rmse": round(float(np.sqrt(mean_squared_error(y_pm25_test, pm25_pred))), 4),
            "mae": round(float(mean_absolute_error(y_pm25_test, pm25_pred)), 4),
            "r2": round(float(r2_score(y_pm25_test, pm25_pred)), 4),
        },
        "co2": {
            "rmse": round(float(np.sqrt(mean_squared_error(y_co2_test, co2_pred))), 4),
            "mae": round(float(mean_absolute_error(y_co2_test, co2_pred)), 4),
            "r2": round(float(r2_score(y_co2_test, co2_pred)), 4),
        },
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "trained_at": datetime.now().isoformat(),
        "model_version": "1.0"
    }
    
    # Guardar modelo y scaler
    model_bundle = {
        "model_pm25": model_pm25,
        "model_co2": model_co2,
    }
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model_bundle, f)
    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    
    print(f"Modelo guardado en: {MODEL_PATH}")
    print(f"Métricas PM2.5 - RMSE: {metrics['pm25']['rmse']}, R²: {metrics['pm25']['r2']}")
    print(f"Métricas CO2   - RMSE: {metrics['co2']['rmse']}, R²: {metrics['co2']['r2']}")
    
    return metrics


def load_model() -> Tuple[dict, object]:
    """Carga el modelo y el scaler desde disco."""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("Modelo no encontrado. Ejecuta el entrenamiento primero.")
    with open(MODEL_PATH, "rb") as f:
        model_bundle = pickle.load(f)
    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)
    return model_bundle, scaler


def predict_next_hours(last_reading: dict, hours_ahead: int = 12) -> List[dict]:
    """
    Genera predicciones de PM2.5 y CO2 para las próximas horas.
    
    Args:
        last_reading: Última lectura del sensor.
        hours_ahead: Número de horas a predecir.
    
    Returns:
        Lista de predicciones con timestamps y valores estimados.
    """
    model_bundle, scaler = load_model()
    model_pm25 = model_bundle["model_pm25"]
    model_co2 = model_bundle["model_co2"]
    
    predictions = []
    current_time = datetime.fromisoformat(last_reading["timestamp"])
    prev_pm25 = last_reading["pm25"]
    prev_co2 = last_reading["co2"]
    temp = last_reading["temperature"]
    humidity = last_reading["humidity"]
    
    for h in range(1, hours_ahead + 1):
        future_time = current_time + timedelta(hours=h)
        features = extract_features(
            timestamp_str=future_time.isoformat(),
            temperature=temp,
            humidity=humidity,
            pm25_lag1=prev_pm25,
            co2_lag1=prev_co2
        )
        X = scaler.transform([features])
        pm25_pred = float(model_pm25.predict(X)[0])
        co2_pred = float(model_co2.predict(X)[0])
        
        predictions.append({
            "predicted_at": datetime.now().isoformat(),
            "target_timestamp": future_time.isoformat(),
            "pm25_predicted": round(max(0, pm25_pred), 2),
            "co2_predicted": round(max(350, co2_pred), 2),
            "model_version": "1.0"
        })
        
        # Usar predicción como lag para la siguiente iteración
        prev_pm25 = pm25_pred
        prev_co2 = co2_pred
    
    return predictions


def get_air_quality_index(pm25: float) -> dict:
    """
    Calcula el Índice de Calidad del Aire (AQI) basado en PM2.5.
    Basado en los estándares de la EPA de EE.UU.
    """
    if pm25 <= 12.0:
        return {"level": "Buena", "color": "#00e400", "description": "La calidad del aire es satisfactoria."}
    elif pm25 <= 35.4:
        return {"level": "Moderada", "color": "#ffff00", "description": "Calidad aceptable, posible riesgo para sensibles."}
    elif pm25 <= 55.4:
        return {"level": "Insalubre para grupos sensibles", "color": "#ff7e00", "description": "Grupos sensibles pueden verse afectados."}
    elif pm25 <= 150.4:
        return {"level": "Insalubre", "color": "#ff0000", "description": "Todos pueden experimentar efectos adversos."}
    elif pm25 <= 250.4:
        return {"level": "Muy Insalubre", "color": "#8f3f97", "description": "Advertencias de emergencia sanitaria."}
    else:
        return {"level": "Peligrosa", "color": "#7e0023", "description": "Alerta sanitaria: todos afectados gravemente."}


if __name__ == "__main__":
    # Prueba del módulo
    from iot_simulator import generate_historical_data
    from database import init_db, insert_readings_bulk, get_all_readings_for_training
    
    print("=== Prueba del Módulo de IA ===")
    init_db()
    
    print("Generando datos históricos...")
    data = generate_historical_data(days=30)
    insert_readings_bulk(data)
    
    records = get_all_readings_for_training()
    print(f"Registros disponibles para entrenamiento: {len(records)}")
    
    metrics = train_model(records)
    print("\nMétricas del modelo:")
    print(json.dumps(metrics, indent=2))
