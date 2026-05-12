from rest_framework import serializers
from .models import Medico, Especialidad, Turno, Paciente, Evolucion

# --- Lo que ya tenías ---
class EspecialidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Especialidad
        fields = ['id', 'nombre']

class MedicoSerializer(serializers.ModelSerializer):
    especialidades = EspecialidadSerializer(many=True, read_only=True)
    class Meta:
        model = Medico
        fields = ['id', 'user', 'matricula', 'especialidades']

# --- LO NUEVO PARA LA RESERVA ---
class TurnoReservaSerializer(serializers.ModelSerializer):
    # Campos que vienen de Vue
    paciente = serializers.PrimaryKeyRelatedField(queryset=Paciente.objects.all(), required=False)
    paciente_dni = serializers.CharField(write_only=True)
    paciente_nombre = serializers.CharField(source='paciente.nombre',read_only=True)
    paciente_apellido = serializers.CharField(source='paciente.apellido',read_only=True)
    paciente_telefono = serializers.CharField(write_only=True)
    paciente_email = serializers.EmailField(write_only=True)

    class Meta:
        model = Turno
        fields = [
            'id',
            'paciente', 
            'medico', 
            'fecha', 
            'hora', 
            'estado',
            'paciente_dni', 
            'paciente_nombre', 
            'paciente_apellido', 
            'paciente_telefono',
            'paciente_email'
        ]

    # --- NUEVA FUNCIÓN DE VALIDACIÓN ---
    def validate(self, data):
        dni = data.get('paciente_dni')
        # Limpiamos espacios y pasamos a minúsculas para una comparación justa
        nombre_nuevo = data.get('paciente_nombre').strip().lower()
        apellido_nuevo = data.get('paciente_apellido').strip().lower()

        # Buscamos si el paciente ya existe en la DB
        paciente_existente = Paciente.objects.filter(dni=dni).first()

        if paciente_existente:
            # Comparamos lo que hay en la DB con lo que mandó el usuario
            nombre_db = paciente_existente.nombre.strip().lower()
            apellido_db = paciente_existente.apellido.strip().lower()

            if nombre_db != nombre_nuevo or apellido_db != apellido_nuevo:
                # Si el DNI existe pero el nombre/apellido no coinciden, lanzamos error
                raise serializers.ValidationError({
                    "paciente_dni": f"El DNI {dni} ya está registrado a nombre de {paciente_existente.nombre} {paciente_existente.apellido}. Verifique los datos."
                })
        
        return data

    def create(self, validated_data):
        # 1. Sacamos los datos del paciente
        dni = validated_data.pop('paciente_dni','')
        nombre = validated_data.pop('paciente_nombre','')
        apellido = validated_data.pop('paciente_apellido','')
        telefono = validated_data.pop('paciente_telefono','')
        email = validated_data.pop('paciente_email','')

        # 2. Lógica de "Si no existe, crealo". 
        # Si llegó acá es porque validate() dio el OK.
        paciente, created = Paciente.objects.get_or_create(
            dni=dni,
            defaults={
                'nombre': nombre,
                'apellido': apellido,
                'telefono': telefono,
                'email': email
            }
        )

        # 3. Creamos el turno
        turno = Turno.objects.create(paciente=paciente, **validated_data)
        return turno
    

class EvolucionSerializer(serializers.ModelSerializer):
    # Esto está perfecto en tu código: permite ver los IDs de los anexos
    anexos = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    medico_nombre = serializers.ReadOnlyField(source='medico.user.get_full_name')

    class Meta:
        model = Evolucion
        fields = [
            'id', 'paciente', 'medico', 'medico_nombre', 'turno', 
            'evolucion_padre', 'especialidad_nombre', 'fecha_creacion', 
            'motivo', 'descripcion', 'bloqueado', 'anexos'
        ]
        read_only_fields = ['especialidad_nombre', 'fecha_creacion', 'bloqueado']
        
        # AGREGAMOS ESTO:
        extra_kwargs = {
            'turno': {'required': False, 'allow_null': True},
            'evolucion_padre': {'required': False, 'allow_null': True}
        }