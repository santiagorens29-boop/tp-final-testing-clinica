from django.urls import path
from . import views

urlpatterns = [
    # --- RUTAS DE GESTIÓN (Secretaria/Médico) ---
    path('turnos-hoy/', views.api_turnos_hoy, name='api_turnos_hoy'),
    path('marcar-llegada/<int:turno_id>/', views.marcar_llegada_paciente, name='marcar_llegada'),

    # Rutas para los buscadores predictivos
    path('buscar-obras-sociales/', views.buscar_obras_sociales, name='buscar_obras_sociales'),
    path('buscar-medicos/', views.buscar_medicos, name='buscar_medicos'),
    
    # RUTAS QUE FALTAN PARA EL CONSULTORIO (Basado en tus errores 404)
    path('detalle-paciente/<int:paciente_id>/', views.api_detalle_paciente, name='api_detalle_paciente'),
    path('perfil-clinico/<int:paciente_id>/', views.api_perfil_clinico, name='api_perfil_clinico'),
    path('evoluciones-paciente/<int:paciente_id>/', views.api_evoluciones_paciente, name='api_evoluciones_paciente'),
    path('evoluciones/', views.api_crear_evolucion, name='api_crear_evolucion'),

    
    path('login/', views.api_login, name='api_login'),
]