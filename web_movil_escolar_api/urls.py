from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import users, alumnos, maestros, materias, auth

# Agrupamos todo bajo 'api/' para coincidir con el environment de Angular
urlpatterns = [
    path('api/', include([
        # Create Admin
        path('admin/', users.AdminView.as_view()),
        # Admin Data
        path('lista-admins/', users.AdminAll.as_view()),
        # Create Alumno
        path('alumnos/', alumnos.AlumnosView.as_view()),
        # Alumno Data
        path('lista-alumnos/', alumnos.AlumnosAll.as_view()),
        # Create Maestro
        path('maestros/', maestros.MaestrosView.as_view()),
        # Maestro Data
        path('lista-maestros/', maestros.MaestrosAll.as_view()),
        # Create/Update/Delete Materia
        path('materias/', materias.MateriasView.as_view()),
        # Materia Data
        path('lista-materias/', materias.MateriasAll.as_view()),
        # Verificar NRC
        path('verificar-nrc/', materias.VerificarNRCView.as_view()),
        # Total Users
        path('total-usuarios/', users.TotalUsers.as_view()),
        # Login
        path('login/', auth.CustomAuthToken.as_view()),
        # Logout
        path('logout/', auth.Logout.as_view())
    ]))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)