from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Especialidad, Medico, Paciente, ObraSocial, Turno, Visita, ConfiguracionHorario, Ausencia

# Registramos cada modelo para que sea visible en el panel
admin.site.register(Especialidad)
admin.site.register(Medico)
admin.site.register(Paciente)
admin.site.register(ObraSocial)
admin.site.register(Turno)
admin.site.register(Visita)
admin.site.register(ConfiguracionHorario)
admin.site.register(Ausencia)