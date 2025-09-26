from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import IntegrityError

class Command(BaseCommand):
    help = 'Crea el usuario admin para el panel de upload'

    def handle(self, *args, **options):
        email = 'publicidad@adicla.org.gt'
        password = 'AdiclaPublicidad2025'
        
        try:
            # Verificar si ya existe
            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f'El usuario {email} ya existe')
                )
                return
            
            # Crear usuario
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                is_staff=True,
                is_superuser=False
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Usuario admin creado exitosamente: {email}')
            )
            
        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(f'Error creando usuario: {str(e)}')
            )