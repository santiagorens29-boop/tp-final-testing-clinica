import json
import random
from datetime import datetime, timedelta

from django.contrib.auth import authenticate, login
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

# Todas las importaciones de modelos agrupadas y limpias
from .models import (
    Medico, ConfiguracionHorario, Turno, ObraSocial, 
    Paciente, CodigoVerificacion, Evolucion, PerfilClinico
)
from .serializers import TurnoReservaSerializer
from .utils import generar_intervalos_turnos

from django.db import IntegrityError 

class AgendaMedicoAPI(APIView):
    def get(self, request, medico_id, fecha_str=None):
        try:
            medico = Medico.objects.get(id=medico_id)
            
            if fecha_str:
                fecha_seleccionada = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            else:
                fecha_seleccionada = datetime.today().date()

            dia_semana = fecha_seleccionada.weekday()
            
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

            return Response({
                'medico': medico.user.get_full_name() or medico.user.username,
                'fecha': fecha_seleccionada,
                'turnos': turnos_data
            }, status=status.HTTP_200_OK)

        except Medico.DoesNotExist:
            return Response({'error': 'Médico no encontrado'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def disponibilidad_proxima(request, medico_id, dia_semana):
    medico = get_object_or_404(Medico, id=medico_id)
    hoy = datetime.today().date()
    proximos_dias_data = []
    fecha_chequeo = hoy + timedelta(days=1)
    
    intentos = 0
    while len(proximos_dias_data) < 4 and intentos < 60:
        if fecha_chequeo.weekday() == int(dia_semana):
            config = ConfiguracionHorario.objects.filter(
                medico=medico, 
                dia_semana=dia_semana, 
                activo=True
            ).first()

            if config:
                horas_generadas = generar_intervalos_turnos(
                    config.hora_inicio, 
                    config.hora_fin, 
                    config.duracion_turno
                )
                
                turnos_con_estado = []
                for hora_obj in horas_generadas:
                    esta_ocupado = Turno.objects.filter(
                        medico=medico, 
                        fecha=fecha_chequeo, 
                        hora=hora_obj
                    ).exists()
                    
                    turnos_con_estado.append({
                        "hora": hora_obj.strftime('%H:%M'),
                        "libre": not esta_ocupado
                    })

                if turnos_con_estado:
                    proximos_dias_data.append({
                        "dia": fecha_chequeo.strftime('%Y-%m-%d'),
                        "turnos": turnos_con_estado
                    })
        
        fecha_chequeo += timedelta(days=1)
        intentos += 1

    return Response({"proximos_dias": proximos_dias_data})


@api_view(['POST'])
def solicitar_codigo(request):
    dni = request.data.get('dni')
    email_ingresado = request.data.get('email')

    paciente = Paciente.objects.filter(dni=dni).first()
    
    if not paciente and not email_ingresado:
        return Response({
            "status": "paciente_nuevo",
            "mensaje": "DNI no registrado, por favor ingrese su email."
        }, status=200)

    email_destino = paciente.email if paciente else email_ingresado
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


@csrf_exempt
@api_view(['POST'])
def confirmar_y_reservar(request):
    """
    Función de confirmación de reserva médica estándar.
    """
    codigo_usuario = request.data.get('codigo', '')
    dni = request.data.get('paciente_dni', request.data.get('dni', ''))
    email_vue = request.data.get('paciente_email', request.data.get('email', '')) 

    # --- ERROR 1 (SPRINT 3): PARÁMETRO - FORMATO DE CORREO INVÁLIDO (CP-02) ---
    if email_vue and "@" not in email_vue:
        raise ValueError("Error de Parámetro (Sprint Final): El correo ingresado no posee un formato sintáctico válido.")

    if not dni or not codigo_usuario:
        return Response({"error": "DNI y Código son obligatorios"}, status=400)
                             
    paciente = Paciente.objects.filter(dni=dni).first()
    email_a_validar = paciente.email if paciente else email_vue

    if not email_a_validar:
        return Response({"error": "No se encontró un email asociado a este pedido"}, status=400)

    registro_codigo = CodigoVerificacion.objects.filter(email=email_a_validar).last()

    if not registro_codigo or not registro_codigo.es_valido() or registro_codigo.codigo != str(codigo_usuario):
        return Response({"error": "Código inválido o expirado."}, status=400)

    # (Lógica original de preparación de datos_reserva...)
    datos_reserva = request.data.copy()
    
    if 'medico' in datos_reserva and 'medico_id' not in datos_reserva:
        datos_reserva['medico_id'] = datos_reserva.get('medico')

    if paciente:
        datos_reserva['paciente_nombre'] = paciente.nombre or ''
        datos_reserva['paciente_apellido'] = paciente.apellido or ''
        datos_reserva['paciente_email'] = paciente.email or ''
        datos_reserva['paciente_telefono'] = paciente.telefono or ''
    else:
        datos_reserva['paciente_nombre'] = request.data.get('nombre') or ''
        datos_reserva['paciente_apellido'] = request.data.get('apellido') or ''
        datos_reserva['paciente_email'] = email_vue or ''
        datos_reserva['paciente_telefono'] = request.data.get('telefono') or ''

    serializer = TurnoReservaSerializer(data=datos_reserva)
    if serializer.is_valid():
        serializer.save()
        registro_codigo.delete()
        return Response({"mensaje": "¡Reserva confirmada!"}, status=201)
    
    return Response(serializer.errors, status=400)

@api_view(['GET'])
def api_turnos_hoy(request):
    """Lista los turnos para el médico y la secretaría"""
    hoy = timezone.now().date()
    turnos = Turno.objects.filter(fecha=hoy).select_related('paciente', 'medico__user')
    
    data = []
    for t in turnos:
        data.append({
            'id': t.id,
            'hora': t.hora.strftime('%H:%M') if t.hora else "00:00",
            'paciente': t.paciente.id,
            'paciente_id': t.paciente.id,
            'paciente_nombre': t.paciente.nombre,
            'paciente_apellido': t.paciente.apellido,
            'estado': t.estado if t.estado else 'programado',
            'medico': t.medico.user.get_full_name() or t.medico.user.username
        })
        
    return Response(data, status=200)


@csrf_exempt
def api_actualizar_estado_turno(request, turno_id):
    """Cambia el estado del turno sin trabas de CSRF"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    turno = get_object_or_404(Turno, id=turno_id)
    
    try:
        data = json.loads(request.body)
        nuevo_estado = data.get('estado')
    except Exception:
        return JsonResponse({'error': 'JSON inválido o vacío'}, status=400)
    
    if not nuevo_estado:
        return JsonResponse({'error': 'Falta el campo estado'}, status=400)

    turno.estado = nuevo_estado
    turno.save()
    
    return JsonResponse({
        'status': 'success',
        'mensaje': f'El turno fue cambiado a: {turno.estado}'
    }, status=200)


@csrf_exempt
def api_login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            rol = 'paciente'
            especialidades = []
            
            if hasattr(user, 'medico'):
                rol = 'medico'
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


@api_view(['GET', 'PATCH'])
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
            'obra_social': paciente.obra_social.id if paciente.obra_social else None,
            'obra_social_nombre': str(paciente.obra_social) if paciente.obra_social else None,
            'medico_cabecera': paciente.medico_cabecera.id if paciente.medico_cabecera else None,
            'medico_cabecera_nombre': f"{paciente.medico_cabecera.user.last_name}, {paciente.medico_cabecera.user.first_name}" if paciente.medico_cabecera else None,
        })
    
    elif request.method == 'PATCH':
        data = request.data
        paciente.es_particular = data.get('es_particular', paciente.es_particular)
        paciente.nro_afiliado = data.get('nro_afiliado', paciente.nro_afiliado)
        paciente.fecha_nacimiento = data.get('fecha_nacimiento', paciente.fecha_nacimiento)
        
        if 'obra_social' in data:
            paciente.obra_social_id = data.get('obra_social')
        if 'medico_cabecera' in data:
            paciente.medico_cabecera_id = data.get('medico_cabecera')
            
            
        paciente.save()
        return Response({'status': 'ok'})


@api_view(['GET'])
def api_perfil_clinico(request, paciente_id):
    perfil = PerfilClinico.objects.filter(paciente_id=paciente_id).first()
    
    if not perfil:
        return Response({
            'alergias': 'Sin registrar',
            'antecedentes': 'Sin registrar',
            'grupo_sanguineo': 'S/D'
        })
    
    return Response({
        'alergias': perfil.alergias,
        'antecedentes': getattr(perfil, 'antecedentes', ''),
        'grupo_sanguineo': perfil.grupo_sanguineo
    })


@api_view(['GET'])
def api_evoluciones_paciente(request, paciente_id):
    """Trae el historial agrupando las evoluciones hijas (anexos) adentro de sus padres"""
    try:
        principales = Evolucion.objects.filter(
            paciente_id=paciente_id, 
            evolucion_padre__isnull=True
        ).select_related('medico__user').order_by('-fecha_creacion')
        
        data = []
        for evo in principales:
            anexos_db = evo.anexos.all().select_related('medico__user').order_by('fecha_creacion')
            anexos_lista = []
            
            for anexo in anexos_db:
                anexos_lista.append({
                    'id': anexo.id,
                    'fecha': anexo.fecha_creacion.strftime('%d/%m/%Y %H:%M') if anexo.fecha_creacion else "Sin fecha",
                    'motivo': anexo.motivo,
                    'descripcion': anexo.descripcion,
                    'medico': anexo.medico.user.get_full_name() or anexo.medico.user.username
                })

            # Evita el error strftime / None de tus registros de prueba anteriores
            especialidad_display = evo.especialidad_nombre if evo.especialidad_nombre else "General"

            data.append({
                'id': evo.id,
                'fecha': evo.fecha_creacion.strftime('%d/%m/%Y %H:%M') if evo.fecha_creacion else "Sin fecha",
                'motivo': evo.motivo,
                'descripcion': evo.descripcion,
                'medico': evo.medico.user.get_full_name() or evo.medico.user.username,
                'especialidad': especialidad_display,
                'anexos': anexos_lista
            })
            
        return Response(data, status=200)
    except Exception as e:
        print(f"Error en el listado de evoluciones: {e}")
        return Response([], status=200)

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny

@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def api_crear_evolucion(request):
    """
    Guarda una nueva consulta médica (Principal o Anexo/Hija) y cierra el turno.
    SE MODIFICÓ ESTA VERSIÓN PARA GENERAR ERRORES LÓGICOS DE PRUEBA CONTROLADOS.
    """
    turno_id = request.data.get('turno_id')
    paciente_id = request.data.get('paciente_id')
    evolucion_padre_id = request.data.get('evolucion_padre_id')
    descripcion = request.data.get('descripcion', '')
    
    # --- ERROR 3 (SPRINT 4): LÓGICA - INTENTO DE EDICIÓN DE EVOLUCIÓN HISTÓRICA ---
    # Si detectamos que el texto intenta alterar un registro cerrado, disparamos la excepción.
    if "editar" in str(descripcion).lower() or "modificar" in str(descripcion).lower():
        raise PermissionError("Error de Lógica (Sprint Final): Las evoluciones firmadas y bloqueadas no admiten modificaciones.")

    # Buscamos médico de pruebas
    if request.user and hasattr(request.user, 'medico'):
        medico_obj = request.user.medico
    else:
        medico_obj = Medico.objects.first()

    if not medico_obj:
        return Response({'error': 'No hay perfiles médicos cargados'}, status=403)

    # Si es una evolución hija (ANEXO)
    padre_obj = None
    if evolucion_padre_id:
        padre_obj = get_object_or_404(Evolucion, id=int(evolucion_padre_id))
        paciente_id = padre_obj.paciente_id
        turno_id_int = None 
    else:
        # Si es una consulta normal, sí procesamos el turno
        try:
            turno_id_int = int(turno_id) if turno_id else None
        except (ValueError, TypeError):
            turno_id_int = None

    try:
        paciente_id_int = int(paciente_id) if paciente_id else None
    except (ValueError, TypeError):
        return Response({'error': 'ID de paciente inválido.'}, status=400)

    try:
        # Creación del registro en la base de datos
        nueva_evo = Evolucion.objects.create(
            paciente_id=paciente_id_int,
            medico=medico_obj,
            turno_id=turno_id_int,  # Evita el choque UNIQUE si es anexo
            evolucion_padre=padre_obj,
            motivo=request.data.get('motivo'),
            descripcion=descripcion
        )

        # Si es consulta principal y tiene turno, lo pasamos a atendido
        if turno_id_int and not padre_obj:
            turno = Turno.objects.filter(id=turno_id_int).first()
            if turno:
                turno.estado = 'atendido'
                turno.save()

        return Response({'status': 'success', 'message': 'Registro grabado correctamente.'}, status=201)

    except IntegrityError as ie:
        print(f"Error de integridad en la base de datos: {ie}")
        return Response({'error': 'Este turno ya tiene una evolución principal asignada. Si querés agregar información, creá un Anexo.'}, status=400)
    except Exception as e:
        print(f"Error crítico al crear evolución: {e}")
        return Response({'error': str(e)}, status=500)
    
@api_view(['GET'])
def buscar_obras_sociales(request):
    query = request.GET.get('q', '')
    if len(query) < 2:
        return Response([])
    
    resultados = ObraSocial.objects.filter(
        Q(nombre__icontains=query) | Q(sigla__icontains=query)
    )
    
    data = [{'id': os.id, 'text': str(os)} for os in resultados]
    return Response(data)


@api_view(['GET'])
def buscar_medicos(request):
    query = request.GET.get('q', '')
    if len(query) < 2:
        return Response([])
    
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

@api_view(['GET'])
def api_buscar_pacientes_general(request):
    """Buscador predictivo e incremental de pacientes para el acceso directo a la Historia Clínica"""
    query = request.GET.get('q', '').strip()
    
    # Regla de rendimiento: si tiene menos de 2 caracteres, devolvemos lista vacía
    if len(query) < 2:
        return Response([])

    # Verificamos si la consulta es puramente numérica (potencial DNI)
    if query.isdigit():
        # Búsqueda súper veloz por coincidencia inicial o exacta en el DNI (Árbol binario)
        resultados = Paciente.objects.filter(dni__startswith=query)[:15]
    else:
        # Búsqueda optimizada por el INICIO del apellido o nombre (Estante alfabético)
        resultados = Paciente.objects.filter(
            Q(apellido__istartswith=query) | 
            Q(nombre__istartswith=query)
        )[:15] # Ponemos un tope de 15 resultados para cuidar el ancho de banda del front

    # Estructuramos la respuesta con los datos clave para que Vue los dibuje prolijamente
    data = [
        {
            'id': p.id,
            'nombre': p.nombre,
            'apellido': p.apellido,
            'dni': p.dni,
            'text': f"{p.apellido.upper()}, {p.nombre} (DNI: {p.dni})"
        } for p in resultados
    ]
    
    return Response(data, status=200)