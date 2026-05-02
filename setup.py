"""
Script de Configuración Inicial - Sistema de Monitoreo de Calidad del Aire
Inicializa la base de datos, genera datos históricos y entrena el modelo de IA.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, insert_readings_bulk, get_all_readings_for_training, get_stats
from iot_simulator import generate_historical_data
from ai_model import train_model
import json


def setup():
    print("=" * 60)
    print("  Sistema de Monitoreo de Calidad del Aire - Setup Inicial")
    print("=" * 60)
    
    # 1. Inicializar base de datos
    print("\n[1/3] Inicializando base de datos...")
    init_db()
    
    # 2. Generar datos históricos
    stats = get_stats()
    if stats["total_readings"] < 100:
        print("\n[2/3] Generando datos históricos (30 días, cada 15 min)...")
        data = generate_historical_data(days=30, interval_minutes=15)
        count = insert_readings_bulk(data)
        print(f"      Se insertaron {count} registros en la base de datos.")
    else:
        print(f"\n[2/3] Base de datos ya tiene {stats['total_readings']} registros. Omitiendo generación.")
    
    # 3. Entrenar modelo de IA
    print("\n[3/3] Entrenando modelo de IA (Gradient Boosting)...")
    records = get_all_readings_for_training()
    print(f"      Usando {len(records)} registros para entrenamiento...")
    metrics = train_model(records)
    
    print("\n" + "=" * 60)
    print("  Setup completado exitosamente!")
    print("=" * 60)
    print("\nMétricas del Modelo:")
    print(f"  PM2.5 - RMSE: {metrics['pm25']['rmse']:.4f} µg/m³  |  R²: {metrics['pm25']['r2']:.4f}")
    print(f"  CO2   - RMSE: {metrics['co2']['rmse']:.4f} ppm    |  R²: {metrics['co2']['r2']:.4f}")
    print(f"\n  Muestras de entrenamiento: {metrics['training_samples']}")
    print(f"  Muestras de prueba:        {metrics['test_samples']}")
    print("\nPara iniciar el servidor, ejecuta:")
    print("  python3 backend/app.py")
    print("=" * 60)
    
    return metrics


if __name__ == "__main__":
    metrics = setup()
