from django.db.models import *
from django.db import transaction
from web_movil_escolar_api.serializers import UserSerializer
from web_movil_escolar_api.serializers import *
from web_movil_escolar_api.models import *
from rest_framework import permissions
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import Group
import json
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination

class MaestroPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class MaestrosAll(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = MaestroPagination
    
    def get(self, request, *args, **kwargs):
        # Obtener parámetros de búsqueda y ordenamiento
        search = request.GET.get('search', '')
        sort_by = request.GET.get('sort_by', 'id')
        sort_order = request.GET.get('sort_order', 'asc')
        page_size = request.GET.get('page_size', 10)
        
        # Construir queryset base
        maestros = Maestros.objects.filter(user__is_active=1)
        
        # Aplicar filtro de búsqueda
        if search:
            maestros = maestros.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(id_trabajador__icontains=search) |
                Q(user__email__icontains=search)
            )
        
        # Aplicar ordenamiento
        if sort_order == 'desc':
            sort_by = f'-{sort_by}'
        
        # Mapear campos de ordenamiento CORREGIDO
        sort_mapping = {
            'id': 'id',
            'first_name': 'user__first_name',
            'last_name': 'user__last_name',
            'email': 'user__email',
            'id_trabajador': 'id_trabajador'
        }
        
        sort_field = sort_mapping.get(sort_by, 'id')
        maestros = maestros.order_by(sort_field)
        
        # Paginación
        paginator = self.pagination_class()
        paginator.page_size = page_size
        result_page = paginator.paginate_queryset(maestros, request, view=self)
        
        # Serializar datos
        serializer = MaestroSerializer(result_page, many=True)
        
        # Agregar datos del usuario y procesar materias_json
        data = []
        for maestro_data in serializer.data:
            maestro_obj = Maestros.objects.get(id=maestro_data['id'])
            maestro_data['first_name'] = maestro_obj.user.first_name
            maestro_data['last_name'] = maestro_obj.user.last_name
            maestro_data['email'] = maestro_obj.user.email
            
            # Procesar materias_json
            if isinstance(maestro_data, dict) and "materias_json" in maestro_data:
                try:
                    maestro_data["materias_json"] = json.loads(maestro_data["materias_json"])
                except Exception:
                    maestro_data["materias_json"] = []
            
            data.append(maestro_data)
        
        return paginator.get_paginated_response(data)

class MaestrosView(generics.CreateAPIView):
    def get_permissions(self):
        if self.request.method in ['GET', 'PUT', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return []  # POST no requiere autenticación
    
    # Obtener maestro por ID
    def get(self, request, *args, **kwargs):
        maestro_id = request.GET.get("id")
        if maestro_id:
            maestro = get_object_or_404(Maestros, id=maestro_id)
            maestro_data = MaestroSerializer(maestro, many=False).data
            maestro_data['first_name'] = maestro.user.first_name
            maestro_data['last_name'] = maestro.user.last_name
            maestro_data['email'] = maestro.user.email
            
            # Procesar materias_json
            if isinstance(maestro_data, dict) and "materias_json" in maestro_data:
                try:
                    maestro_data["materias_json"] = json.loads(maestro_data["materias_json"])
                except Exception:
                    maestro_data["materias_json"] = []
            
            return Response(maestro_data, 200)
        return Response({"message": "Se requiere el ID del maestro"}, 400)
    
    # Registrar nuevo maestro
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = UserSerializer(data=request.data)
        if user.is_valid():
            role = request.data['rol']
            first_name = request.data['first_name']
            last_name = request.data['last_name']
            email = request.data['email']
            password = request.data['password']
            
            existing_user = User.objects.filter(email=email).first()
            if existing_user:
                return Response({"message":"Username "+email+", is already taken"},400)

            user = User.objects.create(
                username=email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=1
            )
            user.save()
            user.set_password(password)
            user.save()

            group, created = Group.objects.get_or_create(name=role)
            group.user_set.add(user)
            user.save()

            maestro = Maestros.objects.create(
                user=user,
                id_trabajador=request.data["id_trabajador"],
                fecha_nacimiento=request.data["fecha_nacimiento"],
                telefono=request.data["telefono"],
                rfc=request.data["rfc"].upper(),
                cubiculo=request.data["cubiculo"],
                area_investigacion=request.data["area_investigacion"],
                materias_json=json.dumps(request.data["materias_json"])
            )
            maestro.save()

            return Response({"maestro_created_id": maestro.id}, 201)

        return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Actualizar datos del maestro
    @transaction.atomic
    def put(self, request, *args, **kwargs):
        maestro_id = request.data.get("id")
        if not maestro_id:
            return Response({"message": "Se requiere el ID del maestro"}, 400)
            
        maestro = get_object_or_404(Maestros, id=maestro_id)
        
        # Verificar permisos: maestro solo puede editar su propio perfil
        user_rol = request.user.groups.first().name if request.user.groups.exists() else None
        
        if user_rol == 'maestro' and request.user.id != maestro.user.id:
            return Response({"message": "No tienes permisos para editar otros maestros"}, 403)
        
        # Resto del código de actualización...
        maestro.id_trabajador = request.data.get("id_trabajador", maestro.id_trabajador)
        maestro.fecha_nacimiento = request.data.get("fecha_nacimiento", maestro.fecha_nacimiento)
        maestro.telefono = request.data.get("telefono", maestro.telefono)
        maestro.rfc = request.data.get("rfc", maestro.rfc).upper()
        maestro.cubiculo = request.data.get("cubiculo", maestro.cubiculo)
        maestro.area_investigacion = request.data.get("area_investigacion", maestro.area_investigacion)
        maestro.materias_json = json.dumps(request.data.get("materias_json", []))
        maestro.save()
        
        user = maestro.user
        user.first_name = request.data.get("first_name", user.first_name)
        user.last_name = request.data.get("last_name", user.last_name)
        user.email = request.data.get("email", user.email)
        user.save()
        
        return Response({"message": "Maestro actualizado correctamente"}, 200)

    # Eliminar maestro
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        maestro_id = request.GET.get("id")
        if not maestro_id:
            return Response({"message": "Se requiere el ID del maestro"}, 400)
            
        maestro = get_object_or_404(Maestros, id=maestro_id)
        
        # Verificar permisos: maestro solo puede eliminar su propio perfil
        user_rol = request.user.groups.first().name if request.user.groups.exists() else None
        
        if user_rol == 'maestro' and request.user.id != maestro.user.id:
            return Response({"message": "No tienes permisos para eliminar otros maestros"}, 403)
        
        try:
            maestro.user.delete()
            return Response({"details": "Maestro eliminado"}, 200)
        except Exception as e:
            return Response({"details": "Error al eliminar maestro"}, 400)