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
from django.shortcuts import get_object_or_404
import json
from rest_framework.pagination import PageNumberPagination

class AdminPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class AdminAll(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = AdminPagination
    
    def get(self, request, *args, **kwargs):
        # Obtener parámetros de búsqueda y ordenamiento
        search = request.GET.get('search', '')
        sort_by = request.GET.get('sort_by', 'id')
        sort_order = request.GET.get('sort_order', 'asc')
        page_size = request.GET.get('page_size', 10)
        
        # Construir queryset base
        admins = Administradores.objects.filter(user__is_active=1)
        
        # Aplicar filtro de búsqueda
        if search:
            admins = admins.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(clave_admin__icontains=search) |
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
            'clave_admin': 'clave_admin'
        }
        
        sort_field = sort_mapping.get(sort_by, 'id')
        admins = admins.order_by(sort_field)
        
        # Paginación
        paginator = self.pagination_class()
        paginator.page_size = page_size
        result_page = paginator.paginate_queryset(admins, request, view=self)
        
        # Serializar datos
        serializer = AdminSerializer(result_page, many=True)
        
        # Agregar datos del usuario a cada admin
        data = []
        for admin_data in serializer.data:
            admin_obj = Administradores.objects.get(id=admin_data['id'])
            admin_data['first_name'] = admin_obj.user.first_name
            admin_data['last_name'] = admin_obj.user.last_name
            admin_data['email'] = admin_obj.user.email
            data.append(admin_data)
        
        return paginator.get_paginated_response(data)

class AdminView(generics.CreateAPIView):
    # Permisos por método (sobrescribe el comportamiento default)
    # Verifica que el usuario esté autenticado para las peticiones GET, PUT y DELETE
    def get_permissions(self):
        if self.request.method in ['GET', 'PUT', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return []  # POST no requiere autenticación
    
    #Obtener usuario por ID
    def get(self, request, *args, **kwargs):
        admin = get_object_or_404(Administradores, id = request.GET.get("id"))
        admin_data = AdminSerializer(admin, many=False).data
        # Agregar datos del usuario
        admin_data['first_name'] = admin.user.first_name
        admin_data['last_name'] = admin.user.last_name
        admin_data['email'] = admin.user.email
        # Si todo es correcto, regresamos la información
        return Response(admin_data, 200)
    
    #Registrar nuevo usuario
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # Serializamos los datos del administrador para volverlo de nuevo JSON
        user = UserSerializer(data=request.data)
        
        if user.is_valid():
            #Grab user data
            role = request.data['rol']
            first_name = request.data['first_name']
            last_name = request.data['last_name']
            email = request.data['email']
            password = request.data['password']
            #Valida si existe el usuario o bien el email registrado
            existing_user = User.objects.filter(email=email).first()

            if existing_user:
                return Response({"message":"Username "+email+", is already taken"},400)

            user = User.objects.create( username = email,
                                        email = email,
                                        first_name = first_name,
                                        last_name = last_name,
                                        is_active = 1)


            user.save()
            #Cifrar la contraseña
            user.set_password(password)
            user.save()

            group, created = Group.objects.get_or_create(name=role)
            group.user_set.add(user)
            user.save()

            #Almacenar los datos adicionales del administrador
            admin = Administradores.objects.create(user=user,
                                            clave_admin= request.data["clave_admin"],
                                            telefono= request.data["telefono"],
                                            rfc= request.data["rfc"].upper(),
                                            edad= request.data["edad"],
                                            ocupacion= request.data["ocupacion"])
            admin.save()

            return Response({"admin_created_id": admin.id }, 201)

        return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Actualizar datos del administrador
    # Actualizar datos del administrador - VERSIÓN CORREGIDA
    @transaction.atomic
    def put(self, request, *args, **kwargs):
        # Primero obtenemos el administrador a actualizar
        admin_id = request.data.get("id")
        if not admin_id:
            return Response({"message": "Se requiere el ID del administrador"}, 400)
        
        admin = get_object_or_404(Administradores, id=admin_id)
        
        # Actualizamos los datos del administrador
        admin.clave_admin = request.data.get("clave_admin", admin.clave_admin)
        admin.telefono = request.data.get("telefono", admin.telefono)
        admin.rfc = request.data.get("rfc", admin.rfc).upper()
        admin.edad = request.data.get("edad", admin.edad)
        admin.ocupacion = request.data.get("ocupacion", admin.ocupacion)
        admin.save()
        
        # Actualizamos los datos del usuario asociado
        user = admin.user
        user.first_name = request.data.get("first_name", user.first_name)
        user.last_name = request.data.get("last_name", user.last_name)
        user.email = request.data.get("email", user.email)
        
        # Si se proporcionó password, la actualizamos
        password = request.data.get("password")
        if password:
            user.set_password(password)
        
        user.save()
        
        return Response({"message": "Administrador actualizado correctamente"}, 200)
        
    # Eliminar administrador con delete (Borrar realmente)
    def delete(self, request, *args, **kwargs):
        admin_id = request.GET.get("id")
        if not admin_id:
            return Response({"message": "Se requiere el ID del administrador"}, 400)
            
        admin = get_object_or_404(Administradores, id=admin_id)
        try:
            admin.user.delete()
            return Response({"details": "Administrador eliminado"}, 200)
        except Exception as e:
            return Response({"details": "Error al eliminar administrador"}, 400)

class TotalUsers(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request, *args, **kwargs):
        # TOTAL ADMINISTRADORES
        admin_qs = Administradores.objects.filter(user__is_active=True)
        total_admins = admin_qs.count()

        # TOTAL MAESTROS
        maestros_qs = Maestros.objects.filter(user__is_active=True)
        total_maestros = maestros_qs.count()

        # TOTAL ALUMNOS
        alumnos_qs = Alumnos.objects.filter(user__is_active=True)
        total_alumnos = alumnos_qs.count()

        # Respuesta final SIEMPRE válida
        return Response(
            {
                "admins": total_admins,
                "maestros": total_maestros,
                "alumnos": total_alumnos
            },
            status=200
        )