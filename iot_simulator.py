"""
Simulador de Sensores IoT - Sistema de Monitoreo de Calidad del Aire
Este módulo simula los datos que enviaría un microcontrolador ESP32 con sensores
de calidad del aire (PM2.5, CO2, NOx, Temperatura, Humedad).
"""

import random
import math
import datetime


def simulate_sensor_reading(sensor_id: str = "ESP32_001", timestamp: datetime.datetime = None) -> dict:
    """
    Simula una lectura de sensores de calidad del aire.
    Los valores siguen patrones realistas con variaciones diurnas y ruido aleatorio.
    
    Args:
        sensor_id: Identificador del sensor/dispositivo IoT.
        timestamp: Momento de la lectura. Si es None, usa el tiempo actual.
    
    Returns:
        Diccionario con los valores de los sensores.
    """
    if timestamp is None:
        timestamp = datetime.datetime.now()

    # Patrón diurno: mayor contaminación en horas pico (7-9am, 5-7pm)
    hour = timestamp.hour
    diurnal_factor = 1.0 + 0.5 * (
        math.exp(-((hour - 8) ** 2) / 4) + math.exp(-((hour - 18) ** 2) / 4)
    )

    # PM2.5 (µg/m³) - OMS recomienda < 15 µg/m³ (media 24h)
    pm25_base = 20.0
    pm25 = round(pm25_base * diurnal_factor + random.gauss(0, 3), 2)
    pm25 = max(1.0, pm25)

    # CO2 (ppm) - Nivel exterior normal ~415 ppm
    co2_base = 420.0
    co2 = round(co2_base + 80 * diurnal_factor + random.gauss(0, 15), 2)
    co2 = max(380.0, co2)

    # NOx (ppb) - Óxidos de nitrógeno
    nox_base = 25.0
    nox = round(nox_base * diurnal_factor + random.gauss(0, 5), 2)
    nox = max(0.1, nox)

    # Temperatura (°C)
    temp_base = 22.0
    temp = round(temp_base + 5 * math.sin((hour - 6) * math.pi / 12) + random.gauss(0, 1), 2)

    # Humedad relativa (%)
    humidity = round(60.0 - 10 * math.sin((hour - 6) * math.pi / 12) + random.gauss(0, 3), 2)
    humidity = max(20.0, min(100.0, humidity))

    return {
        "sensor_id": sensor_id,
        "timestamp": timestamp.isoformat(),
        "pm25": pm25,
        "co2": co2,
        "nox": nox,
        "temperature": temp,
        "humidity": humidity,
    }


def generate_historical_data(days: int = 30, interval_minutes: int = 15) -> list:
    """
    Genera un dataset histórico de lecturas de sensores para entrenar el modelo de IA.
    
    Args:
        days: Número de días de datos históricos a generar.
        interval_minutes: Intervalo entre lecturas en minutos.
    
    Returns:
        Lista de diccionarios con las lecturas históricas.
    """
    records = []
    start_time = datetime.datetime.now() - datetime.timedelta(days=days)
    current_time = start_time

    while current_time <= datetime.datetime.now():
        reading = simulate_sensor_reading(timestamp=current_time)
        records.append(reading)
        current_time += datetime.timedelta(minutes=interval_minutes)

    return records


if __name__ == "__main__":
    # Prueba del simulador
    reading = simulate_sensor_reading()
    print("Lectura de sensor simulada:")
    for key, value in reading.items():
        print(f"  {key}: {value}")
    
    print(f"\nGenerando datos históricos de 30 días...")
    data = generate_historical_data(days=30)
    print(f"Total de registros generados: {len(data)}")
