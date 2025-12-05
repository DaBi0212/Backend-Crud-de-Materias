from django.db.models import Q
from django.db import transaction
from web_movil_escolar_api.serializers import *
from web_movil_escolar_api.models import *
from rest_framework import permissions
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from datetime import datetime
import re
import json


class MateriaPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class MateriasAll(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = MateriaPagination
    
    def get(self, request, *args, **kwargs):
        search = request.GET.get('search', '')
        sort_by = request.GET.get('sort_by', 'id')
        sort_order = request.GET.get('sort_order', 'asc')
        page_size = request.GET.get('page_size', 10)
        
        materias = Materia.objects.all().select_related('profesor_asignado')
        
        if search:
            materias = materias.filter(
                Q(nrc__icontains=search) |
                Q(nombre_materia__icontains=search) |
                Q(salon__icontains=search)
            )
        
        sort_mapping = {
            'id': 'id',
            'nrc': 'nrc',
            'nombre_materia': 'nombre_materia',
            'seccion': 'seccion',
            'salon': 'salon',
        }
        
        sort_field = sort_mapping.get(sort_by, 'id')
        if sort_order == 'desc':
            sort_field = f'-{sort_field}'
        
        materias = materias.order_by(sort_field)
        
        paginator = self.pagination_class()
        paginator.page_size = page_size
        result_page = paginator.paginate_queryset(materias, request)
        
        serializer = MateriaSerializer(result_page, many=True)
        
        return paginator.get_paginated_response(serializer.data)


def is_admin_user(user):
    return user.groups.filter(name='administrador').exists()


def parse_time_string(time_str):
    """Convierte string de hora a objeto time, aceptando múltiples formatos"""
    if not time_str:
        return None
    
    time_str = str(time_str).strip().upper()
    
    # Si contiene AM/PM
    if 'AM' in time_str or 'PM' in time_str:
        try:
            # Intentar con espacio
            return datetime.strptime(time_str, '%I:%M %p').time()
        except ValueError:
            try:
                # Intentar sin espacio
                return datetime.strptime(time_str, '%I:%M%p').time()
            except ValueError:
                # Intentar con diferentes formatos
                time_str_clean = time_str.replace('AM', '').replace('PM', '').strip()
                if ':' in time_str_clean:
                    hours, minutes = time_str_clean.split(':')
                    hours = int(hours)
                    if 'PM' in time_str and hours < 12:
                        hours += 12
                    if 'AM' in time_str and hours == 12:
                        hours = 0
                    return datetime.strptime(f"{hours:02d}:{minutes}", '%H:%M').time()
                return None
    else:
        # Formato 24h
        try:
            return datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            # Intentar extraer solo los números
            match = re.search(r'(\d{1,2}):(\d{2})', time_str)
            if match:
                hours, minutes = match.groups()
                return datetime.strptime(f"{int(hours):02d}:{minutes}", '%H:%M').time()
            return None


def validate_materia_data(data, exclude_id=None):
    """Valida los datos de materia"""
    errors = {}
    
    nrc = data.get('nrc', '')
    if not nrc:
        errors['nrc'] = 'El NRC es requerido'
    elif not re.match(r'^\d{6}$', str(nrc)):
        errors['nrc'] = 'El NRC debe ser exactamente 6 dígitos numéricos'
    else:
        try:
            query = Materia.objects.filter(nrc=nrc)
            if exclude_id:
                query = query.exclude(id=exclude_id)
            if query.exists():
                errors['nrc'] = 'NRC ya existe en la base de datos'
        except Exception:
            pass
    
    nombre_materia = data.get('nombre_materia', '')
    if not nombre_materia:
        errors['nombre_materia'] = 'El nombre de la materia es requerido'
    
    seccion = data.get('seccion', '')
    if not seccion:
        errors['seccion'] = 'La sección es requerida'
    
    dias = data.get('dias', [])
    dias_validos = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    
    if not dias:
        errors['dias'] = 'Debe seleccionar al menos un día'
    else:
        if isinstance(dias, str):
            try:
                dias = json.loads(dias)
            except json.JSONDecodeError:
                dias = [d.strip() for d in dias.split(',') if d.strip()]
        
        if not isinstance(dias, list) or len(dias) == 0:
            errors['dias'] = 'Debe contener al menos un día'
        else:
            for dia in dias:
                if dia not in dias_validos:
                    errors['dias'] = f'Día inválido: {dia}. Valores válidos: {", ".join(dias_validos)}'
                    break
    
    hora_inicio_str = data.get('hora_inicio', '')
    hora_fin_str = data.get('hora_fin', '')
    
    hora_inicio = parse_time_string(hora_inicio_str)
    hora_fin = parse_time_string(hora_fin_str)
    
    if not hora_inicio_str:
        errors['hora_inicio'] = 'La hora de inicio es requerida'
    elif hora_inicio is None:
        errors['hora_inicio'] = 'Formato de hora inválido'
    
    if not hora_fin_str:
        errors['hora_fin'] = 'La hora de fin es requerida'
    elif hora_fin is None:
        errors['hora_fin'] = 'Formato de hora inválido'
    
    if hora_inicio and hora_fin and hora_inicio >= hora_fin:
        errors['hora_fin'] = 'La hora de fin debe ser mayor que la hora de inicio'
    
    salon = data.get('salon', '')
    if not salon:
        errors['salon'] = 'El salón es requerido'
    
    programa_educativo = data.get('programa_educativo', '')
    programas_validos = [
        'Ingeniería en Ciencias de la Computación',
        'Licenciatura en Ciencias de la Computación',
        'Ingeniería en Tecnologías de la Información'
    ]
    if not programa_educativo:
        errors['programa_educativo'] = 'El programa educativo es requerido'
    elif programa_educativo not in programas_validos:
        errors['programa_educativo'] = 'Programa educativo inválido'
    
    profesor_id = data.get('profesor_asignado')
    if profesor_id is not None and profesor_id != '':
        try:
            profesor_id_int = int(profesor_id)
            if not Maestros.objects.filter(id=profesor_id_int).exists():
                errors['profesor_asignado'] = 'El profesor asignado no existe'
        except (ValueError, TypeError):
            if profesor_id != '':
                errors['profesor_asignado'] = 'ID de profesor inválido'
    
    creditos = data.get('creditos', '')
    if not creditos:
        errors['creditos'] = 'Los créditos son requeridos'
    
    return errors


class MateriasView(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request, *args, **kwargs):
        materia_id = request.GET.get("id")
        if materia_id:
            try:
                materia_id_int = int(materia_id)
                materia = get_object_or_404(Materia, id=materia_id_int)
                serializer = MateriaSerializer(materia, many=False)
                return Response(serializer.data, 200)
            except ValueError:
                return Response({"error": "ID de materia inválido"}, 400)
            except Exception as e:
                return Response({"error": "Materia no encontrada"}, 404)
        return Response({"error": "Se requiere el ID de la materia"}, 400)
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            return Response({"error": "No tienes permisos para realizar esta acción"}, 403)
        
        errors = validate_materia_data(request.data)
        if errors:
            return Response({"error": errors}, 400)
        
        try:
            hora_inicio = parse_time_string(request.data['hora_inicio'])
            hora_fin = parse_time_string(request.data['hora_fin'])
            
            dias = request.data['dias']
            if isinstance(dias, str):
                try:
                    dias = json.loads(dias)
                except json.JSONDecodeError:
                    dias = [d.strip() for d in dias.split(',') if d.strip()]
            
            profesor_id = request.data.get('profesor_asignado')
            if profesor_id == '' or profesor_id is None:
                profesor_id = None
            
            materia = Materia.objects.create(
                nrc=request.data['nrc'],
                nombre_materia=request.data['nombre_materia'],
                seccion=request.data['seccion'],
                dias=dias,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                salon=request.data['salon'],
                programa_educativo=request.data['programa_educativo'],
                profesor_asignado_id=profesor_id,
                creditos=request.data['creditos']
            )
            
            serializer = MateriaSerializer(materia, many=False)
            return Response(serializer.data, 201)
        except Exception as e:
            return Response({"error": {"general": str(e)}}, 400)
    
    @transaction.atomic
    def put(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            return Response({"error": "No tienes permisos para realizar esta acción"}, 403)
        
        materia_id = request.data.get("id")
        if not materia_id:
            return Response({"error": "Se requiere el ID de la materia"}, 400)
        
        try:
            materia_id_int = int(materia_id)
            materia = get_object_or_404(Materia, id=materia_id_int)
        except ValueError:
            return Response({"error": "ID de materia inválido"}, 400)
        
        errors = validate_materia_data(request.data, exclude_id=materia_id_int)
        if errors:
            return Response({"error": errors}, 400)
        
        try:
            materia.nrc = request.data.get('nrc', materia.nrc)
            materia.nombre_materia = request.data.get('nombre_materia', materia.nombre_materia)
            materia.seccion = request.data.get('seccion', materia.seccion)
            
            dias = request.data.get('dias', materia.dias)
            if isinstance(dias, str):
                try:
                    dias = json.loads(dias)
                except json.JSONDecodeError:
                    dias = [d.strip() for d in dias.split(',') if d.strip()]
            materia.dias = dias
            
            if request.data.get('hora_inicio'):
                materia.hora_inicio = parse_time_string(request.data['hora_inicio'])
            if request.data.get('hora_fin'):
                materia.hora_fin = parse_time_string(request.data['hora_fin'])
            
            materia.salon = request.data.get('salon', materia.salon)
            materia.programa_educativo = request.data.get('programa_educativo', materia.programa_educativo)
            
            if 'profesor_asignado' in request.data:
                profesor_id = request.data['profesor_asignado']
                materia.profesor_asignado_id = profesor_id if profesor_id and profesor_id != '' else None
            
            materia.creditos = request.data.get('creditos', materia.creditos)
            materia.save()
            
            serializer = MateriaSerializer(materia, many=False)
            return Response(serializer.data, 200)
        except Exception as e:
            return Response({"error": {"general": str(e)}}, 400)
    
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            return Response({"error": "No tienes permisos para realizar esta acción"}, 403)
        
        materia_id = request.GET.get("id")
        if not materia_id:
            return Response({"error": "Se requiere el ID de la materia"}, 400)
        
        try:
            materia_id_int = int(materia_id)
            materia = get_object_or_404(Materia, id=materia_id_int)
            materia.delete()
            return Response({"message": "Materia eliminada correctamente"}, 200)
        except ValueError:
            return Response({"error": "ID de materia inválido"}, 400)
        except Exception as e:
            return Response({"error": "Error al eliminar materia"}, 400)


class VerificarNRCView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request, *args, **kwargs):
        nrc = request.GET.get('nrc')
        exclude_id = request.GET.get('exclude_id')
        
        if not nrc:
            return Response({"error": "Se requiere el parámetro 'nrc'"}, 400)
        
        try:
            query = Materia.objects.filter(nrc=nrc)
            if exclude_id:
                try:
                    exclude_id_int = int(exclude_id)
                    query = query.exclude(id=exclude_id_int)
                except ValueError:
                    return Response({"error": "ID de exclusión inválido"}, 400)
            
            exists = query.exists()
            return Response({"exists": exists}, 200)
        except Exception:
            return Response({"exists": False}, 200)