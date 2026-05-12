from datetime import datetime, timedelta

def generar_intervalos_turnos(hora_inicio, hora_fin, duracion):
    """
    Toma un rango de horas y lo divide en pedacitos según la duración.
    Ej: 08:00 a 09:00 con 20min -> [08:00, 08:20, 08:40]
    """
    intervalos = []
    # Convertimos a objetos de tiempo para poder sumar minutos
    actual = datetime.combine(datetime.today(), hora_inicio)
    final = datetime.combine(datetime.today(), hora_fin)

    while actual + timedelta(minutes=duracion) <= final:
        intervalos.append(actual.time())
        actual += timedelta(minutes=duracion)
    
    return intervalos