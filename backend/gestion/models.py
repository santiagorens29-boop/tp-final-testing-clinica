from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from django.utils import timezone # Importante para la expiración

from django.db.models.signals import post_save
from django.dispatch import receiver

# --- 1. Especialidad ---
class Especialidad(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

# --- 2. Medico ---
class Medico(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    matricula = models.CharField(max_length=50, unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    especialidades = models.ManyToManyField(Especialidad, related_name="medicos")

    def __str__(self):
        return f"Dr/a. {self.user.last_name}, {self.user.first_name}"

# --- 3. Obra Social ---
class ObraSocial(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    sigla = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nombre

# --- 4. Paciente ---
class Paciente(models.Model):
    SEXO_CHOICES = [('M', 'Masculino'), ('F', 'Femenino'), ('X', 'Otro')]
    
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)

    es_particular = models.BooleanField(default=False)
    obra_social = models.ForeignKey(ObraSocial, on_delete=models.SET_NULL, null=True, blank=True)
    nro_afiliado = models.CharField(max_length=50, blank=True, null=True)

    medico_cabecera = models.ForeignKey(Medico, on_delete=models.SET_NULL, null=True, related_name="pacientes_asignados")
    
    
    email = models.EmailField(unique=True) 
    telefono = models.CharField(max_length=20, blank=True, null=True)
    fecha_alta = models.DateTimeField(auto_now_add=True)
    es_verificado_fisico = models.BooleanField(default=False)

    class Meta:
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"

# --- 5. Configuracion Horaria ---
class ConfiguracionHorario(models.Model):
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.CASCADE)
    DIA_CHOICES = [(i, name) for i, name in enumerate(['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'])]
    dia_semana = models.IntegerField(choices=DIA_CHOICES)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    duracion_turno = models.PositiveIntegerField()
    fecha_desde = models.DateField()
    activo = models.BooleanField(default=True)

    def clean(self):
        ventana_reserva = 28 
        hoy = date.today()
        fecha_limite = hoy + timedelta(days=ventana_reserva)
        if self.pk:
            original = ConfiguracionHorario.objects.get(pk=self.pk)
            if original.duracion_turno != self.duracion_turno:
                if self.fecha_desde < fecha_limite:
                    raise ValidationError(f"No puedes cambiar la duración...")

# --- 6. Turno ---
class Turno(models.Model):
    ESTADO_CHOICES = [('programado', 'Programado'), ('espera', 'En Espera'), ('atendido', 'Atendido'), ('cancelado', 'Cancelado')]
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora = models.TimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='programado')

# --- 7. Visita ---
class Visita(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    observacion = models.TextField()
    archivo = models.FileField(upload_to='estudios/%Y/%m/%d/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Las visitas médicas no pueden ser editadas...")
        super(Visita, self).save(*args, **kwargs)

    def __str__(self):
        return f"Visita {self.paciente} - {self.fecha.strftime('%d/%m/%Y')}"

# --- 8. Ausencia ---
class Ausencia(models.Model):
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    motivo = models.CharField(max_length=255, blank=True)

# --- 9. SEGURIDAD: Códigos de Verificación ---
class CodigoVerificacion(models.Model):
    email = models.EmailField()
    codigo = models.CharField(max_length=6)
    creado_en = models.DateTimeField(auto_now_add=True)
    
    def es_valido(self):
        # El código dura 10 minutos
        return timezone.now() < self.creado_en + timedelta(minutes=10)

    def __str__(self):
        return f"Código para {self.email}: {self.codigo}"


class ConfiguracionClinica(models.Model):
    # Definimos las tres opciones de privacidad
    PRIVACIDAD_CHOICES = [
        ('ABIERTA', 'Historia Clínica Abierta (Todos ven todo)'),
        ('AREA', 'Privacidad por Área (Solo misma especialidad)'),
        ('ESTRICTA', 'Privacidad Estricta (Solo el médico autor)'),
    ]

    nombre_institucion = models.CharField(max_length=100)
    politica_privacidad = models.CharField(
        max_length=10, 
        choices=PRIVACIDAD_CHOICES, 
        default='ABIERTA'
    )

    def __str__(self):
        return f"Configuración: {self.nombre_institucion}"


class Evolucion(models.Model):
    paciente = models.ForeignKey('Paciente', on_delete=models.CASCADE, related_name='evoluciones')
    medico = models.ForeignKey('Medico', on_delete=models.PROTECT)
    
    # Relación con el Turno (OneToOne porque un turno genera exactamente UNA evolución)
    # SET_NULL permite que si borras el turno por alguna razón, la historia clínica no se borre
    turno = models.OneToOneField('Turno', on_delete=models.SET_NULL, null=True, blank=True, related_name='evolucion')
    
    # Campo para la jerarquía: si es null, es la principal. Si tiene ID, es un anexo.
    evolucion_padre = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='anexos')
    # Guardamos el nombre de la especialidad como texto en el momento de la visita
    especialidad_nombre = models.CharField(max_length=100, editable=False)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    motivo = models.CharField(max_length=255)
    descripcion = models.TextField()
    
    # Para el bloqueo legal: una vez guardada, no se edita
    bloqueado = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # 1. Bloqueo de edición: Si el objeto ya existe en la DB (self.pk), no dejamos guardar cambios.
        if self.pk:
            raise PermissionError("Las evoluciones firmadas no pueden ser modificadas.")

        # 2. Captura de especialidad (lo que ya tenías)
        if not self.pk:
            if self.medico and self.medico.especialidad:
                self.especialidad_nombre = self.medico.especialidad.nombre
        
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Evoluciones"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.fecha_creacion.date()} - {self.paciente} ({self.especialidad_nombre})"

class EvolucionArchivo(models.Model):
    evolucion = models.ForeignKey(Evolucion, on_delete=models.CASCADE, related_name='archivos')
    archivo = models.FileField(upload_to='historias_clinicas/%Y/%m/%d/')
    descripcion_archivo = models.CharField(max_length=100, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Adjunto de {self.evolucion}"
    

class PerfilClinico(models.Model):
    # Se crea uno solo por paciente
    paciente = models.OneToOneField('Paciente', on_delete=models.CASCADE, related_name='perfil_clinico')
    
    # Información de Alerta (Visible para todos)
    grupo_sanguineo = models.CharField(max_length=5, blank=True, null=True)
    alergias = models.TextField(blank=True, help_text="Ej: Penicilina, látex, etc.")
    enfermedades_cronicas = models.TextField(blank=True, help_text="Ej: Diabetes Tipo 2, Hipertensión.")
    medicacion_habitual = models.TextField(blank=True, help_text="Lo que el paciente toma siempre.")
    antecedentes_familiares = models.TextField(blank=True)
    
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    # Guardamos quién fue el último médico que editó esta ficha
    ultimo_medico = models.ForeignKey('Medico', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Perfil Clínico de {self.paciente}"
    

@receiver(post_save, sender=Paciente) 
def crear_perfil_clinico(sender, instance, created, **kwargs):
    if created:
        PerfilClinico.objects.get_or_create(paciente=instance)