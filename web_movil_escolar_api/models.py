# models.py - versión simplificada
from django.db import models
from django.contrib.auth.models import User
from rest_framework.authentication import TokenAuthentication

class BearerTokenAuthentication(TokenAuthentication):
    keyword = "Bearer"

class Administradores(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False, default=None)
    clave_admin = models.CharField(max_length=255, null=True, blank=True)
    telefono = models.CharField(max_length=255, null=True, blank=True)
    rfc = models.CharField(max_length=255, null=True, blank=True)
    edad = models.IntegerField(null=True, blank=True)
    ocupacion = models.CharField(max_length=255, null=True, blank=True)
    creation = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    update = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Admin: {self.user.first_name} {self.user.last_name}"

class Alumnos(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False, default=None)
    matricula = models.CharField(max_length=255, null=True, blank=True)
    curp = models.CharField(max_length=255, null=True, blank=True)
    rfc = models.CharField(max_length=255, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)  # Cambiado a DateField
    edad = models.IntegerField(null=True, blank=True)
    telefono = models.CharField(max_length=255, null=True, blank=True)
    ocupacion = models.CharField(max_length=255, null=True, blank=True)
    creation = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    update = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Alumno: {self.user.first_name} {self.user.last_name}"

class Maestros(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False, default=None)
    id_trabajador = models.CharField(max_length=255, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)  # Cambiado a DateField
    telefono = models.CharField(max_length=255, null=True, blank=True)
    rfc = models.CharField(max_length=255, null=True, blank=True)
    cubiculo = models.CharField(max_length=255, null=True, blank=True)
    edad = models.IntegerField(null=True, blank=True)
    area_investigacion = models.CharField(max_length=255, null=True, blank=True)
    materias_json = models.TextField(null=True, blank=True)
    creation = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    update = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Maestro: {self.user.first_name} {self.user.last_name}"

class Materia(models.Model):
    id = models.BigAutoField(primary_key=True)
    nrc = models.CharField(max_length=6, unique=True, null=False, blank=False)
    nombre_materia = models.CharField(max_length=200, null=False, blank=False)
    seccion = models.CharField(max_length=3, null=False, blank=False)
    dias = models.JSONField(null=False, blank=False, default=list)
    hora_inicio = models.TimeField(null=False, blank=False)
    hora_fin = models.TimeField(null=False, blank=False)
    salon = models.CharField(max_length=15, null=False, blank=False)
    programa_educativo = models.CharField(max_length=100, null=False, blank=False)
    profesor_asignado = models.ForeignKey(Maestros, on_delete=models.SET_NULL, null=True, blank=True, related_name='materias')
    creditos = models.CharField(max_length=2, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre_materia} - {self.nrc}"