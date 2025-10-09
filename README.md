# 🎥 AdiclaVideo - Plataforma Integral de Gestión y Streaming

<div align="center">

![AdiclaVideo Logo](AdiclaVideo/videos/static/videos/img/logo-adicla.png)

**Sistema completo de gestión de contenido multimedia, streaming automatizado y administración de proyectos para ADICLA**

[![Django](https://img.shields.io/badge/Django-5.2.6-092E20?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![SQL Server](https://img.shields.io/badge/SQL%20Server-CC2927?style=for-the-badge&logo=microsoft-sql-server&logoColor=white)](https://www.microsoft.com/sql-server)
[![HLS](https://img.shields.io/badge/HLS-Streaming-FF6B6B?style=for-the-badge&logo=html5&logoColor=white)](https://developer.apple.com/streaming/)

</div>

---

## 🌟 **Descripción**

**AdiclaVideo** es una plataforma integral desarrollada para ADICLA que combina gestión de contenido multimedia, streaming adaptativo en tiempo real, y un sistema completo de administración de proyectos y tareas. Diseñada para optimizar la comunicación interna y la distribución de contenido audiovisual en entornos corporativos.

---

## ✨ **Características Principales**

### 🎬 **Sistema de Streaming Avanzado**

- **Streaming HLS Adaptativo** con múltiples calidades automáticas
- **Reproducción Sincronizada** para múltiples clientes simultáneos
- **Duplicado Automático** de videos verticales para aprovechar pantalla completa
- **Streaming Automático** con horarios de oficina (7:30 AM - 6:00 PM)
- **Monitoreo Windows** integrado con Task Scheduler

### 👥 **Gestión de Usuarios Completa**

- **Perfiles Detallados** con nombres, apellidos, área de trabajo y cargo
- **Sistema de Autenticación** robusto con sesiones personalizadas
- **Configuración de Preferencias** individualizadas
- **Gestión de Permisos** por roles y áreas

### 📋 **Sistema de Proyectos y Tareas**

- **Gestión Completa de Proyectos** con estados, fechas y asignaciones
- **Sistema de Tareas** con prioridades, dependencias y seguimiento temporal
- **Subida de Archivos** integrada en proyectos y tareas
- **Sistema de Comentarios** colaborativo
- **Dashboard Interactivo** con métricas en tiempo real

### 📁 **Gestión de Archivos Multimedia**

- **Subida Múltiple** de videos e imágenes
- **Transcodificación Automática** a HLS para streaming
- **Previsualización** integrada de contenido
- **Organización** por categorías y metadatos

---

## 🏗️ **Arquitectura del Sistema**

### **Backend (Django 5.2.6)**

```
AdiclaVideo/
├── 🎵 videos/                    # App principal
│   ├── 📊 models.py              # Modelos de datos
│   ├── 🎮 views.py               # Lógica de negocio
│   ├── 🎨 templates/             # Interfaces de usuario
│   ├── 🎯 static/                # Recursos estáticos
│   └── 📋 management/commands/   # Comandos personalizados
├── ⚙️ AdiclaVideo/               # Configuración
├── 📄 requirements.txt          # Dependencias
└── 🚀 run_waitress.py           # Servidor de producción
```

### **Frontend (HTML5 + CSS3 + JavaScript)**

- **Diseño Responsivo** adaptable a múltiples dispositivos
- **Reproductor HLS.js** para streaming adaptativo
- **Interfaces AJAX** para actualizaciones en tiempo real
- **Dashboard Interactivo** con métricas visuales

### **Base de Datos (SQL Server)**

- **Modelos Relacionales** optimizados
- **Índices Estratégicos** para alto rendimiento
- **Migraciones Automáticas** para actualizaciones

---

## 🚀 **Instalación y Configuración**

### **Prerrequisitos**

- Python 3.11+
- SQL Server 2019+
- FFmpeg (para transcodificación)
- Windows Server (para automatización)

### **1. Clonación del Repositorio**

```bash
git clone https://github.com/jhony-23/WebVideoA.git
cd WebVideoA/AdiclaVideo
```

### **2. Entorno Virtual**

```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### **3. Instalación de Dependencias**

```bash
pip install -r requirements.txt
```

### **4. Configuración de Base de Datos**

```python
# AdiclaVideo/settings_production.py
DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': 'PlataformaVideosA',
        'HOST': 'tu-servidor-sql',
        'PORT': '1433',
        'USER': 'tu-usuario',
        'PASSWORD': 'tu-password',
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
        },
    }
}
```

### **5. Migraciones**

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
```

### **6. Inicio del Servidor**

```bash
# Desarrollo
python manage.py runserver

# Producción
python run_waitress.py --settings=AdiclaVideo.settings_production
```

---

## 🔧 **Funcionalidades Detalladas**

### **📺 Sistema de Streaming**

#### **Reproducción Sincronizada**

- API `/api/sync/` para sincronización de clientes
- Estado global de playlist compartido
- Calculación automática de posición temporal
- Manejo de diferentes tipos de media (video/imagen)

#### **Streaming Automático**

```bash
# Comandos disponibles
python manage.py streaming_auto start      # Iniciar streaming
python manage.py streaming_auto stop       # Detener streaming
python manage.py streaming_auto status     # Ver estado
python manage.py streaming_auto monitor    # Monitoreo automático
python manage.py streaming_auto cleanup    # Limpieza de archivos
```

#### **Configuración de Automatización Windows**

```bash
# Configuración automática de Task Scheduler
configurar_scheduler_mejorado.bat

# Monitoreo cada 30 minutos durante horario de oficina
monitor_streaming_mejorado.bat

# Scripts PowerShell avanzados
Monitor-Streaming.ps1 -Force  # Ejecución forzada
```

### **👤 Gestión de Usuarios**

#### **Registro Completo**

- Formulario de registro con validaciones
- Perfiles automáticos basados en email
- Completado de perfil obligatorio
- Sistema de áreas de trabajo predefinidas

#### **Autenticación Avanzada**

- Sistema de sesiones personalizadas para tareas
- Middleware de autenticación especializado
- Redirección inteligente post-login
- Gestión de permisos granular

### **📊 Sistema de Proyectos**

#### **Creación y Gestión**

- Códigos únicos automáticos
- Estados configurables (planificacion, desarrollo, revision, completado)
- Fechas estimadas y reales
- Sistema de colores e iconos
- Visibilidad pública/privada

#### **Características Avanzadas**

- Asignación de miembros
- Archivos adjuntos ilimitados
- Sistema de comentarios anidados
- Métricas de progreso automáticas
- Dashboard personalizable

### **✅ Sistema de Tareas**

#### **Gestión Completa**

- Prioridades (baja, media, alta, critica)
- Estados dinámicos (pendiente, en_progreso, revision, completada)
- Fechas de vencimiento con alertas
- Tiempo estimado vs tiempo real
- Sistema de dependencias entre tareas

#### **Funcionalidades Avanzadas**

- Asignación múltiple de usuarios
- Tags personalizables
- Archivos adjuntos por tarea
- Comentarios colaborativos
- Métricas de productividad

---

## 📱 **Interfaces de Usuario**

### **🏠 Dashboard Principal**

- Métricas en tiempo real
- Gráficos interactivos
- Accesos rápidos
- Notificaciones centralizadas

### **🎥 Reproductor de Streaming**

- Interfaz fullscreen adaptativa
- Controles intuitivos
- Información de estado en tiempo real
- Duplicado automático para contenido vertical

### **📋 Gestión de Proyectos**

- Vista de lista con filtros avanzados
- Vista detallada con toda la información
- Formularios inteligentes
- Sistema de archivos integrado

### **✔️ Gestión de Tareas**

- Dashboard tipo Kanban
- Filtros por estado, prioridad, fecha
- Vista de calendario integrada
- Métricas de rendimiento

---

## 🛠️ **Tecnologías Utilizadas**

### **Backend**

- **Django 5.2.6** - Framework web principal
- **Python 3.13** - Lenguaje de programación
- **Waitress** - Servidor WSGI de producción
- **django-mssql** - Conector SQL Server
- **Pillow** - Procesamiento de imágenes
- **psutil** - Monitoreo del sistema

### **Frontend**

- **HTML5** - Estructura semántica
- **CSS3** - Estilos modernos y responsivos
- **JavaScript ES6+** - Interactividad avanzada
- **HLS.js** - Reproductor de streaming adaptativo
- **AJAX** - Comunicación asíncrona

### **Base de Datos**

- **SQL Server 2019+** - Base de datos principal
- **Modelos relacionales** optimizados
- **Índices estratégicos** para rendimiento
- **Procedimientos almacenados** para operaciones complejas

### **Multimedia**

- **FFmpeg** - Transcodificación de video
- **HLS (HTTP Live Streaming)** - Protocolo de streaming
- **Múltiples calidades** automáticas (240p, 480p, 720p, 1080p)
- **Streaming adaptativo** según ancho de banda

### **Infraestructura**

- **Windows Server** - Servidor de producción
- **Task Scheduler** - Automatización de tareas
- **PowerShell** - Scripts de administración
- **IIS** - Proxy inverso (opcional)

---

## ⚡ **Rendimiento y Optimización**

### **Streaming Optimizado**

- **Buffer inteligente** para reducir interrupciones
- **Múltiples calidades** generadas automáticamente
- **CDN-ready** para distribución global
- **Compresión avanzada** de archivos HLS

### **Base de Datos**

- **Índices optimizados** en campos críticos
- **Consultas eficientes** con ORM de Django
- **Paginación inteligente** para grandes datasets
- **Cache de consultas** frecuentes

### **Frontend**

- **Carga asíncrona** de componentes
- **Minificación** de CSS y JavaScript
- **Compresión GZIP** habilitada
- **Lazy loading** de imágenes

---

## 🔐 **Seguridad**

### **Autenticación y Autorización**

- **Sesiones seguras** con tokens CSRF
- **Validación de entrada** exhaustiva
- **Sanitización** de archivos subidos
- **Control de acceso** basado en roles

### **Protección de Archivos**

- **Validación de tipos** de archivo
- **Límites de tamaño** configurables
- **Escaneo de contenido** malicioso
- **Almacenamiento seguro** con permisos restringidos

### **Comunicación Segura**

- **HTTPS** obligatorio en producción
- **Headers de seguridad** configurados
- **Protección XSS** integrada
- **Validación CSRF** en formularios

---

## 📊 **API y Endpoints**

### **API de Streaming**

```http
GET /api/sync/                    # Estado de sincronización
POST /api/play/                   # Iniciar reproducción
POST /api/stop/                   # Detener reproducción
GET /api/playlist/                # Obtener playlist actual
```

### **API de Proyectos**

```http
GET /proyectos/                   # Lista de proyectos
POST /proyectos/crear/            # Crear proyecto
GET /proyectos/{id}/              # Detalle de proyecto
POST /proyectos/{id}/archivos/    # Subir archivo
```

### **API de Tareas**

```http
GET /tareas/                      # Lista de tareas
POST /tareas/crear/               # Crear tarea
PUT /tareas/{id}/estado/          # Cambiar estado
POST /tareas/{id}/comentar/       # Agregar comentario
```

---

## 🤖 **Automatización**

### **Streaming Automático**

- **Horario configurado**: 7:30 AM - 6:00 PM, Lunes a Viernes
- **Monitoreo cada 30 minutos** durante horario de oficina
- **Reinicio automático** en caso de fallos
- **Limpieza automática** de archivos temporales
- **Logs detallados** de todas las operaciones

### **Scripts de Mantenimiento**

```bash
# Instalación completa automatizada
Instalar-Sistema-Completo.bat

# Configuración de monitoreo
configurar_scheduler_mejorado.bat

# Monitoreo avanzado con PowerShell
Monitor-Streaming.ps1

# Limpieza automática
python manage.py streaming_auto cleanup --force
```

### **Task Scheduler Integration**

- **Configuración automática** de tareas programadas
- **Ejecución como usuario SYSTEM** para máximos privilegios
- **Logging centralizado** de todas las ejecuciones
- **Recuperación automática** ante errores

---

## 📝 **Comandos Útiles**

### **Gestión del Sistema**

```bash
# Ver estado de migraciones
python manage.py showmigrations

# Crear superusuario
python manage.py createsuperuser

# Recopilar archivos estáticos
python manage.py collectstatic --noinput

# Limpiar sesiones expiradas
python manage.py clearsessions
```

### **Streaming y Multimedia**

```bash
# Verificar estado del streaming
python manage.py streaming_auto status

# Listar videos disponibles
python manage.py streaming_auto list --videos

# Generar estadísticas de uso
python manage.py streaming_auto stats --last-7-days

# Optimizar base de datos
python manage.py streaming_auto optimize --database
```

### **Monitoreo y Diagnóstico**

```bash
# Ver procesos activos
python manage.py streaming_auto monitor --verbose

# Verificar configuración
python manage.py streaming_auto check --settings

# Rotar logs antiguos
python manage.py streaming_auto rotate-logs --days=30
```

---

## 🔄 **Despliegue y Actualizaciones**

### **Despliegue Inicial**

```bash
# 1. Clonar repositorio
git clone https://github.com/jhony-23/WebVideoA.git

# 2. Configurar entorno
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 3. Configurar base de datos
python manage.py migrate
python manage.py collectstatic --noinput

# 4. Iniciar servidor
python run_waitress.py --settings=AdiclaVideo.settings_production
```

### **Actualizaciones**

```bash
# 1. Actualizar código
git pull origin main

# 2. Instalar nuevas dependencias
pip install -r requirements.txt

# 3. Aplicar migraciones
python manage.py migrate

# 4. Recopilar estáticos
python manage.py collectstatic --noinput

# 5. Reiniciar servidor
# (Detener proceso actual y reiniciar)
```

---

## 📚 **Documentación Adicional**

### **Archivos de Documentación**

- `STREAMING_AUTOMATICO_v2.md` - Guía completa del sistema de streaming
- `requirements.txt` - Lista de dependencias de Python
- `requirements-production.txt` - Dependencias optimizadas para producción

### **Scripts de Automatización**

- `configurar_scheduler_mejorado.bat` - Configuración avanzada de Task Scheduler
- `monitor_streaming_mejorado.bat` - Script de monitoreo robusto
- `Monitor-Streaming.ps1` - Monitoreo PowerShell con características empresariales
- `Instalar-Sistema-Completo.bat` - Instalador automatizado completo

---

## 🐛 **Solución de Problemas**

### **Problemas Comunes**

#### **Error de conexión a base de datos**

```bash
# Verificar configuración
python -c "from AdiclaVideo.settings_production import *; print(DATABASES)"

# Probar conexión
python manage.py dbshell
```

#### **Archivos estáticos no se cargan**

```bash
# Recopilar archivos forzadamente
python manage.py collectstatic --noinput --clear

# Verificar configuración
python -c "from AdiclaVideo.settings_production import *; print(STATIC_ROOT)"
```

#### **Streaming no funciona**

```bash
# Verificar estado
python manage.py streaming_auto status

# Ver logs
type "logs\streaming_auto.log"

# Reiniciar sistema
python manage.py streaming_auto restart
```

#### **Migraciones fallan**

```bash
# Ver migraciones pendientes
python manage.py showmigrations

# Aplicar migraciones forzadamente
python manage.py migrate --fake-initial
```

---

## 🤝 **Contribución**

### **Estructura de Contribución**

1. **Fork** del repositorio
2. **Crear rama** para nueva funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. **Commit** de cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. **Push** a la rama (`git push origin feature/nueva-funcionalidad`)
5. **Pull Request** con descripción detallada

### **Estándares de Código**

- **PEP 8** para código Python
- **Comentarios descriptivos** en funciones complejas
- **Tests unitarios** para nuevas funcionalidades
- **Documentación** actualizada para cambios importantes

---

## 📄 **Licencia**

Este proyecto es propietario de **ADICLA (Asociación de Desarrollo Integral Comunitario Local de Atitlán)**.

Todos los derechos reservados. El uso, distribución o modificación de este software requiere autorización expresa de ADICLA.

---

## 👨‍💻 **Equipo de Desarrollo**

### **Desarrollador Principal**

- **GitHub**: [@jhony-23](https://github.com/jhony-23)
- **Especialización**: Full Stack Development, Streaming Technologies, Database Architecture

### **Organización**

- **ADICLA** - Asociación de Desarrollo Integral Comunitario Local de Atitlán
- **Sitio Web**: [adicla.org](https://adicla.org)
- **Email**: contacto@adicla.org

---

## 📞 **Soporte Técnico**

### **Contacto de Emergencia**

- **Email**: ixcamparicpablo@gmail.com
- **WhatsApp**: +502 59328539
- **Horario**: 24/7 para emergencias críticas

### **Soporte General**

- **Email**: soporte@adicla.com
- **Horario**: Lunes a Viernes, 8:00 AM - 5:00 PM (GMT-6)
- **Tiempo de respuesta**: Máximo 24 horas

### **Documentación y Recursos**

- **Wiki**: [Documentación completa del proyecto]
- **Issues**: [GitHub Issues](https://github.com/jhony-23/WebVideoA/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jhony-23/WebVideoA/discussions)

---

## 🏆 **Estado del Proyecto**

### **Versión Actual: v2.0.0**

- ✅ **Sistema de streaming**: Completamente funcional
- ✅ **Gestión de usuarios**: Implementado y probado
- ✅ **Sistema de proyectos**: Funcional con todas las características
- ✅ **Sistema de tareas**: Implementado con métricas avanzadas
- ✅ **Automatización**: Scripts y monitoreo funcionando
- ✅ **Base de datos**: Sincronizada y optimizada
- ✅ **Despliegue**: Exitoso en producción

### **Próximas Funcionalidades (v2.1.0)**

- 📱 **App móvil nativa** para iOS y Android
- 🔔 **Notificaciones push** en tiempo real
- 📊 **Analytics avanzados** con dashboard ejecutivo
- 🌐 **Multi-idioma** (Español, Inglés, K'iche')
- ☁️ **Integración en la nube** con Azure/AWS

---

<div align="center">

## 🌟 **¡Gracias por usar AdiclaVideo!**

**Desarrollado con ❤️ para ADICLA por el Licenciado e Ingeniero en
Tecnologia de Sistemas Informaticos Juan Pablo Ixcamparic Escún Octubre 2025**

</div>
