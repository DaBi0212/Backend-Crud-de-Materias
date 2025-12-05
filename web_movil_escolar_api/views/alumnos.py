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
from rest_framework.pagination import PageNumberPagination

class AlumnoPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class AlumnosAll(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = AlumnoPagination
    
    def get(self, request, *args, **kwargs):
        # Obtener parámetros de búsqueda y ordenamiento
        search = request.GET.get('search', '')
        sort_by = request.GET.get('sort_by', 'id')
        sort_order = request.GET.get('sort_order', 'asc')
        page_size = request.GET.get('page_size', 10)
        
        # Construir queryset base
        alumnos = Alumnos.objects.filter(user__is_active=1)
        
        # Aplicar filtro de búsqueda
        if search:
            alumnos = alumnos.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(matricula__icontains=search) |
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
            'matricula': 'matricula',
            'nombre': 'user__first_name'
        }
        
        sort_field = sort_mapping.get(sort_by, 'id')
        alumnos = alumnos.order_by(sort_field)
        
        # Paginación
        paginator = self.pagination_class()
        paginator.page_size = page_size
        result_page = paginator.paginate_queryset(alumnos, request, view=self)
        
        # Serializar datos
        serializer = AlumnoSerializer(result_page, many=True)
        
        # Agregar datos del usuario a cada alumno
        data = []
        for alumno_data in serializer.data:
            alumno_obj = Alumnos.objects.get(id=alumno_data['id'])
            alumno_data['first_name'] = alumno_obj.user.first_name
            alumno_data['last_name'] = alumno_obj.user.last_name
            alumno_data['email'] = alumno_obj.user.email
            data.append(alumno_data)
        
        return paginator.get_paginated_response(data)

class AlumnosView(generics.CreateAPIView):
    def get_permissions(self):
        if self.request.method in ['GET', 'PUT', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return []  # POST no requiere autenticación
    
    # Obtener alumno por ID
    def get(self, request, *args, **kwargs):
        alumno_id = request.GET.get("id")
        if alumno_id:
            alumno = get_object_or_404(Alumnos, id=alumno_id)
            alumno_data = AlumnoSerializer(alumno, many=False).data
            alumno_data['first_name'] = alumno.user.first_name
            alumno_data['last_name'] = alumno.user.last_name
            alumno_data['email'] = alumno.user.email
            return Response(alumno_data, 200)
        return Response({"message": "Se requiere el ID del alumno"}, 400)
    
    # Registrar nuevo alumno
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

            alumno = Alumnos.objects.create(
                user=user,
                matricula=request.data["matricula"],
                curp=request.data["curp"].upper(),
                rfc=request.data["rfc"].upper(),
                fecha_nacimiento=request.data["fecha_nacimiento"],
                edad=request.data["edad"],
                telefono=request.data["telefono"],
                ocupacion=request.data["ocupacion"]
            )
            alumno.save()

            return Response({"Alumno creado con ID: ": alumno.id}, 201)

        return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Actualizar datos del alumno
    @transaction.atomic
    def put(self, request, *args, **kwargs):
        alumno_id = request.data.get("id")
        if not alumno_id:
            return Response({"message": "Se requiere el ID del alumno"}, 400)
            
        alumno = get_object_or_404(Alumnos, id=alumno_id)
        alumno.matricula = request.data.get("matricula", alumno.matricula)
        alumno.curp = request.data.get("curp", alumno.curp).upper()
        alumno.rfc = request.data.get("rfc", alumno.rfc).upper()
        alumno.fecha_nacimiento = request.data.get("fecha_nacimiento", alumno.fecha_nacimiento)
        alumno.edad = request.data.get("edad", alumno.edad)
        alumno.telefono = request.data.get("telefono", alumno.telefono)
        alumno.ocupacion = request.data.get("ocupacion", alumno.ocupacion)
        alumno.save()
        
        user = alumno.user
        user.first_name = request.data.get("first_name", user.first_name)
        user.last_name = request.data.get("last_name", user.last_name)
        user.email = request.data.get("email", user.email)
        user.save()
        
        return Response({"message": "Alumno actualizado correctamente"}, 200)
    
    # Eliminar alumno
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        alumno_id = request.GET.get("id")
        if not alumno_id:
            return Response({"message": "Se requiere el ID del alumno"}, 400)
            
        alumno = get_object_or_404(Alumnos, id=alumno_id)
        try:
            alumno.user.delete()
            return Response({"details": "Alumno eliminado"}, 200)
        except Exception as e:
            return Response({"details": "Error al eliminar alumno"}, 400)