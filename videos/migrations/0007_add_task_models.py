# Generated manually for task management system

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0006_auto_20250926_1223'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PerfilUsuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('foto', models.ImageField(blank=True, null=True, upload_to='perfiles/')),
                ('telefono', models.CharField(blank=True, max_length=20)),
                ('departamento', models.CharField(blank=True, max_length=100)),
                ('puesto', models.CharField(blank=True, max_length=100)),
                ('habilidades', models.TextField(blank=True, help_text='Separar habilidades con comas')),
                ('bio', models.TextField(blank=True, max_length=500)),
                ('fecha_ingreso', models.DateField(blank=True, null=True)),
                ('configuracion_notificaciones', models.JSONField(blank=True, default=dict)),
                ('tema_preferido', models.CharField(choices=[('light', 'Claro'), ('dark', 'Oscuro')], default='light', max_length=20)),
                ('idioma', models.CharField(default='es', max_length=10)),
                ('zona_horaria', models.CharField(default='America/Guatemala', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='perfil', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Perfil de Usuario',
                'verbose_name_plural': 'Perfiles de Usuario',
                'db_table': 'perfil_usuario',
            },
        ),
        migrations.CreateModel(
            name='Proyecto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('descripcion', models.TextField(blank=True)),
                ('codigo', models.CharField(help_text='Código único del proyecto', max_length=20, unique=True)),
                ('fecha_inicio', models.DateField()),
                ('fecha_fin_estimada', models.DateField(blank=True, null=True)),
                ('fecha_fin_real', models.DateField(blank=True, null=True)),
                ('estado', models.CharField(choices=[('activo', 'Activo'), ('pausado', 'Pausado'), ('completado', 'Completado'), ('cancelado', 'Cancelado')], default='activo', max_length=20)),
                ('visibilidad', models.CharField(choices=[('publico', 'Público'), ('privado', 'Privado')], default='privado', max_length=20)),
                ('color', models.CharField(default='#3498db', help_text='Color en formato hex', max_length=7)),
                ('icono', models.CharField(default='📋', help_text='Emoji o icono', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('creador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='proyectos_creados', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Proyecto',
                'verbose_name_plural': 'Proyectos',
                'db_table': 'proyecto',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Tarea',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=200)),
                ('descripcion', models.TextField(blank=True)),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('en_proceso', 'En Proceso'), ('en_revision', 'En Revisión'), ('completada', 'Completada')], default='pendiente', max_length=20)),
                ('prioridad', models.CharField(choices=[('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta'), ('critica', 'Crítica')], default='media', max_length=20)),
                ('fecha_vencimiento', models.DateTimeField(blank=True, null=True)),
                ('fecha_inicio_estimada', models.DateField(blank=True, null=True)),
                ('fecha_inicio_real', models.DateTimeField(blank=True, null=True)),
                ('fecha_completada', models.DateTimeField(blank=True, null=True)),
                ('tiempo_estimado', models.DurationField(blank=True, help_text='Tiempo estimado en formato HH:MM:SS', null=True)),
                ('tiempo_real', models.DurationField(blank=True, null=True)),
                ('tags', models.CharField(blank=True, help_text='Etiquetas separadas por comas', max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('asignados', models.ManyToManyField(blank=True, related_name='tareas_asignadas', to=settings.AUTH_USER_MODEL)),
                ('creador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tareas_creadas', to=settings.AUTH_USER_MODEL)),
                ('dependencias', models.ManyToManyField(blank=True, related_name='dependientes', to='videos.tarea')),
                ('proyecto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tareas', to='videos.proyecto')),
            ],
            options={
                'verbose_name': 'Tarea',
                'verbose_name_plural': 'Tareas',
                'db_table': 'tarea',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MiembroProyecto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rol', models.CharField(choices=[('usuario', 'Usuario'), ('jefe', 'Jefe de Proyecto'), ('admin', 'Administrador')], default='usuario', max_length=20)),
                ('fecha_incorporacion', models.DateTimeField(auto_now_add=True)),
                ('activo', models.BooleanField(default=True)),
                ('proyecto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='miembros', to='videos.proyecto')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='miembro_proyectos', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Miembro de Proyecto',
                'verbose_name_plural': 'Miembros de Proyecto',
                'db_table': 'miembro_proyecto',
            },
        ),
        migrations.AlterUniqueTogether(
            name='miembroproyecto',
            unique_together={('proyecto', 'usuario')},
        ),
    ]