from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Medico, ConfiguracionHorario, Turno, ObraSocial
from .utils import generar_intervalos_turnos
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view  
from .serializers import TurnoReservaSerializer
import random # Para generar el código de 6 números
from .models import Paciente, CodigoVerificacion

from django.http import JsonResponse
from django.utils import timezone

from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Q

from django.views.decorators.csrf import csrf_exempt

class AgendaMedicoAPI(APIView):
    def get(self, request, medico_id, fecha_str=None):
        try:
            medico = Medico.objects.get(id=medico_id)
            
            # 1. Manejo de fecha (si no viene, usamos hoy)
            if fecha_str:
                fecha_seleccionada = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            else:
                fecha_seleccionada = datetime.today().date()

            dia_semana = fecha_seleccionada.weekday()
            
            # 2. Buscar configuración activa
            config = ConfiguracionHorario.objects.filter(
                medico=medico, 
                dia_semana=dia_semana, 
                activo=True,
                fecha_desde__lte=fecha_seleccionada 
            ).order_by('-fecha_desde').first()

            turnos_data = []
            if config:
                horarios_posibles = generar_intervalos_turnos(
                    config.hora_inicio, 
                    config.hora_fin, 
                    config.duracion_turno
                )
                
                turnos_ocupados = Turno.objects.filter(
                    medico=medico, 
                    fecha=fecha_seleccionada,
                    estado__in=['programado', 'espera', 'atendido']
                ).values_list('hora', flat=True)

                for h in horarios_posibles:
                    turnos_data.append({
                        'hora': h.strftime('%H:%M'),
                        'libre': h not in turnos_ocupados
                    })

            # 3. En lugar de renderizar HTML, devolvemos JSON
            return Response({
                'medico': medico.user.get_full_name() or medico.user.username,
                'fecha': fecha_seleccionada,
                'turnos': turnos_data
            }, status=status.HTTP_200_OK)

        except Medico.DoesNotExist:
            return Response({'error': 'Médico no encontrado'}, status=status.HTTP_404_NOT_FOUND)
@api_view(['GET'])
def disponibilidad_proxima(request, medico_id, dia_semana):
    # 1. Buscamos al médico
    medico = get_object_or_404(Medico, id=medico_id)
    
    # 2. Preparativos
    hoy = datetime.today().date()
    proximos_dias_data = []
    fecha_chequeo = hoy + timedelta(days=1) # Regla: empezamos desde mañana
    
    intentos = 0
    # Buscamos hasta tener 4 días o haber revisado 60 días a futuro
    while len(proximos_dias_data) < 4 and intentos < 60:
        
        # Si el día de la semana coincide (0=Lunes, 6=Domingo)
        if fecha_chequeo.weekday() == int(dia_semana):
            
            # Buscamos si el médico tiene configuración para ese día
            config = ConfiguracionHorario.objects.filter(
                medico=medico, 
                dia_semana=dia_semana, 
                activo=True
            ).first()

            if config:
                # Generamos los horarios base usando tu función de utils.py
                # Pasamos (hora_inicio, hora_fin, duracion) como pide tu imagen de utils.py
                horas_generadas = generar_intervalos_turnos(
                    config.hora_inicio, 
                    config.hora_fin, 
                    config.duracion_turno
                )
                
                # Ahora chequeamos cuáles de esas horas están ocupadas en la DB
                turnos_con_estado = []
                for hora_obj in horas_generadas:
                    # Buscamos si ya existe un Turno reservado
                    esta_ocupado = Turno.objects.filter(
                        medico=medico, 
                        fecha=fecha_chequeo, 
                        hora=hora_obj
                    ).exists()
                    
                    turnos_con_estado.append({
                        "hora": hora_obj.strftime('%H:%M'),
                        "libre": not esta_ocupado # Si no existe, está libre
                    })

                # Si el día tuvo horarios, lo agregamos a la respuesta
                if turnos_con_estado:
                    proximos_dias_data.append({
                        "dia": fecha_chequeo.strftime('%Y-%m-%d'),
                        "turnos": turnos_con_estado
                    })
        
        # Pasamos al siguiente día para seguir buscando
        fecha_chequeo += timedelta(days=1)
        intentos += 1

    return Response({"proximos_dias": proximos_dias_data})


@api_view(['POST'])
def solicitar_codigo(request):
    dni = request.data.get('dni')
    email_ingresado = request.data.get('email')

    paciente = Paciente.objects.filter(dni=dni).first()
    
    # 1. Si el paciente NO existe y NO nos mandaron un email todavía...
    if not paciente and not email_ingresado:
        # Avisamos a Vue que es nuevo, pero no cortamos con error 400
        return Response({
            "status": "paciente_nuevo",
            "mensaje": "DNI no registrado, por favor ingrese su email."
        }, status=200) # Usamos 200 para que Vue pueda leer la respuesta

    # 2. Definimos el destino del código
    email_destino = paciente.email if paciente else email_ingresado

    # 3. Generamos y guardamos el código
    codigo = str(random.randint(100000, 999999))
    CodigoVerificacion.objects.update_or_create(
        email=email_destino,
        defaults={'codigo': codigo}
    )

    print(f"--- CÓDIGO ENVIADO A: {email_destino} --- {codigo}")

    return Response({
        "status": "paciente_existente" if paciente else "paciente_nuevo",
        "email_pista": f"{email_destino[:3]}***@..." 
    })

@api_view(['POST'])
def confirmar_y_reservar(request):
    # Usamos .get(key, default) para que NUNCA tire KeyError
    codigo_usuario = request.data.get('codigo', '')
    dni = request.data.get('paciente_dni', '')
    email_vue = request.data.get('paciente_email', '') 

    if not dni or not codigo_usuario:
        return Response({"error": "DNI y Código son obligatorios"}, status=400)
                         
    # 2. Buscar el email para validar (Prioridad al de la DB si el paciente existe)
    paciente = Paciente.objects.filter(dni=dni).first()
    email_a_validar = paciente.email if paciente else email_vue

    if not email_a_validar:
        return Response({"error": "No se encontró un email asociado a este pedido"}, status=400)

    # 3. Validar Código
    registro_codigo = CodigoVerificacion.objects.filter(email=email_a_validar).last()

    if not registro_codigo or not registro_codigo.es_valido() or registro_codigo.codigo != str(codigo_usuario):
        return Response({"error": "Código inválido o expirado."}, status=400)

    # 4. Procesar con el Serializer
    # OJO: Si el paciente ya existe, el Serializer necesita nombre/apellido 
    # para la validación que escribimos. Los sacamos de la DB si vienen vacíos.
    datos_reserva = request.data.copy()
    if paciente:
        datos_reserva['paciente_nombre'] = paciente.nombre
        datos_reserva['paciente_apellido'] = paciente.apellido
        datos_reserva['paciente_email'] = paciente.email
        datos_reserva['paciente_telefono'] = paciente.telefono

    serializer = TurnoReservaSerializer(data=datos_reserva)
    if serializer.is_valid():
        serializer.save()
        registro_codigo.delete()
        return Response({"mensaje": "¡Reserva confirmada!"}, status=201)
    
    return Response(serializer.errors, status=400)



def api_turnos_hoy(request):
    hoy = timezone.now().date()
    
    # Filtramos y optimizamos la consulta con select_related
    turnos = Turno.objects.filter(fecha=hoy).select_related('paciente', 'medico__user')
    
    # IMPORTANTE: Usamos el serializer que ya tiene los campos paciente_nombre y paciente_apellido
    serializer = TurnoReservaSerializer(turnos, many=True)
    
    return JsonResponse(serializer.data, safe=False)

@require_POST
def marcar_llegada_paciente(request, turno_id):
    turno = get_object_or_404(Turno, id=turno_id)
    
    # Usamos el string exacto que tenés en ESTADO_CHOICES
    turno.estado = 'espera' 
    turno.save()
    
    return JsonResponse({'status': 'ok', 'mensaje': 'El paciente ya está en sala de espera'})




@csrf_exempt
def api_login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Verificamos si es médico o secretaria
            rol = 'paciente' # Por defecto
            especialidades = []
            
            if hasattr(user, 'medico'):
                rol = 'medico'
                # Obtenemos sus especialidades gracias a tu relación N:M
                especialidades = list(user.medico.especialidades.values_list('nombre', flat=True))
            elif user.is_staff:
                rol = 'secretaria'
            
            return JsonResponse({
                'status': 'success',
                'user': user.username,
                'rol': rol,
                'especialidades': especialidades
            })
        else:
            return JsonResponse({'status': 'error', 'message': 'Credenciales inválidas'}, status=401)
        
    # --- NUEVAS FUNCIONES PARA EL CONSULTORIO MÉDICO ---

@api_view(['GET', 'PATCH']) # Agregamos PATCH para poder guardar cambios
def api_detalle_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    if request.method == 'GET':
        return Response({
            'id': paciente.id,
            'nombre': paciente.nombre,
            'apellido': paciente.apellido,
            'dni': paciente.dni,
            'fecha_nacimiento': paciente.fecha_nacimiento,
            'es_particular': paciente.es_particular,
            'nro_afiliado': paciente.nro_afiliado,
            # Enviamos el ID y el Nombre para que el buscador de Vue sepa qué mostrar
            'obra_social': paciente.obra_social.id if paciente.obra_social else None,
            'obra_social_nombre': str(paciente.obra_social) if paciente.obra_social else None,
            'medico_cabecera': paciente.medico_cabecera.id if paciente.medico_cabecera else None,
            'medico_cabecera_nombre': f"{paciente.medico_cabecera.user.last_name}, {paciente.medico_cabecera.user.first_name}" if paciente.medico_cabecera else None,
        })
    
    elif request.method == 'PATCH':
        # Esta parte guardará los cambios cuando aprietes "Guardar Cambios Administrativos"
        data = request.data
        paciente.es_particular = data.get('es_particular', paciente.es_particular)
        paciente.nro_afiliado = data.get('nro_afiliado', paciente.nro_afiliado)
        paciente.fecha_nacimiento = data.get('fecha_nacimiento', paciente.fecha_nacimiento)
        
        # Para las FK (Foreign Keys)
        if 'obra_social' in data:
            paciente.obra_social_id = data.get('obra_social')
        if 'medico_cabecera' in data:
            paciente.medico_cabecera_id = data.get('medico_cabecera')
            
        paciente.save()
        return Response({'status': 'ok'})
    
@api_view(['GET'])
def api_perfil_clinico(request, paciente_id):
    """
    Busca el Perfil Clínico (Alergias, Antecedentes). 
    Si no existe, devuelve uno vacío en lugar de dar error 404.
    """
    from .models import PerfilClinico # Asegurate de tener este modelo
    perfil = PerfilClinico.objects.filter(paciente_id=paciente_id).first()
    
    if not perfil:
        return Response({
            'alergias': 'Sin registrar',
            'antecedentes': 'Sin registrar',
            'grupo_sanguineo': 'S/D'
        })
    
    return Response({
        'alergias': perfil.alergias,
        'antecedentes': perfil.antecedentes,
        'grupo_sanguineo': perfil.grupo_sanguineo
    })

@api_view(['GET'])
def api_evoluciones_paciente(request, paciente_id):
    """Trae el historial de consultas del paciente"""
    from .models import Evolucion
    
    # Usamos filter y luego checkeamos si el campo existe. 
    # Si te sigue dando error de 'ordering', quitá el .order_by('-fecha') para probar.
    try:
        evoluciones = Evolucion.objects.filter(paciente_id=paciente_id).select_related('medico__user').order_by('-fecha')
        
        data = []
        for evo in evoluciones:
            data.append({
                'fecha': evo.fecha.strftime('%d/%m/%Y %H:%M') if evo.fecha else "Sin fecha",
                'motivo': evo.motivo,
                'descripcion': evo.descripcion,
                'medico': evo.medico.user.get_full_name() or evo.medico.user.username
            })
        return Response(data)
    except Exception as e:
        print(f"Error en evoluciones: {e}")
        return Response([], status=200) # Devolvemos lista vacía para que Vue no se rompa

@csrf_exempt
@api_view(['POST'])
def api_crear_evolucion(request):
    """Guarda una nueva consulta médica y finaliza el turno"""
    from .models import Evolucion, Turno
    
    turno_id = request.data.get('turno_id')
    paciente_id = request.data.get('paciente_id')
    medico_user = request.user # El médico logueado
    
    if not hasattr(medico_user, 'medico'):
        return Response({'error': 'Solo los médicos pueden evolucionar'}, status=403)

    # Creamos la evolución
    Evolucion.objects.create(
        paciente_id=paciente_id,
        medico=medico_user.medico,
        motivo=request.data.get('motivo'),
        descripcion=request.data.get('descripcion'),
        fecha=timezone.now()
    )

    # IMPORTANTÍSIMO: Marcamos el turno como atendido/finalizado
    if turno_id:
        turno = Turno.objects.filter(id=turno_id).first()
        if turno:
            turno.estado = 'atendido' # O el estado que uses para finalizado
            turno.save()

    return Response({'status': 'success', 'message': 'Evolución guardada correctamente'})



# --- NUEVAS VISTAS PARA BUSCADORES PREDICTIVOS ---

@api_view(['GET'])
def buscar_obras_sociales(request):
    query = request.GET.get('q', '')
    if len(query) < 2:
        return Response([])
    
    # Busca por nombre o por sigla (ej: "Swiss" o "SMG")
    resultados = ObraSocial.objects.filter(
        Q(nombre__icontains=query) | Q(sigla__icontains=query)
    ) # Limitamos a 10 para que sea rápido
    
    data = [{'id': os.id, 'text': str(os)} for os in resultados]
    return Response(data)

@api_view(['GET'])
def buscar_medicos(request):
    query = request.GET.get('q', '')
    if len(query) < 2:
        return Response([])
    
    # Busca por apellido, nombre o especialidad
    resultados = Medico.objects.filter(
        Q(user__last_name__icontains=query) | 
        Q(user__first_name__icontains=query) |
        Q(especialidades__nombre__icontains=query)
    ).distinct()
    
    data = [
        {
            'id': m.id, 
            'text': f"{m.user.last_name}, {m.user.first_name} ({m.especialidades.first().nombre if m.especialidades.exists() else 'Sin esp.'})"
        } for m in resultados
    ]
    return Response(data)