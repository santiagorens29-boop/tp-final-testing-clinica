from django.urls import path
from . import views
# Lo dejamos vacío por ahora para que Django no tire error
urlpatterns = [
    # --- RUTAS DE RESERVA (Paciente) ---
    path('agenda/<int:medico_id>/', views.AgendaMedicoAPI.as_view(), name='api_agenda_hoy'),
    path('agenda/<int:medico_id>/<str:fecha_str>/', views.AgendaMedicoAPI.as_view(), name='api_agenda_fecha'),
    path('disponibilidad/<int:medico_id>/<int:dia_semana>/', views.disponibilidad_proxima, name='disponibilidad_proxima'),
    path('solicitar-codigo/', views.solicitar_codigo, name='solicitar-codigo'),
    path('confirmar-reserva/', views.confirmar_y_reservar, name='confirmar-reserva'),
]