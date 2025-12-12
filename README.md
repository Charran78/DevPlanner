# 🚀 DevPlanner

**DevPlanner** es una aplicación web inteligente de gestión de proyectos de desarrollo de software, potenciada por IA (Inteligencia Artificial), que te ayuda a planificar, desglosar y visualizar tareas de forma automática.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.22+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🎥 Preview

![Demo](https://i.picasion.com/pic93/313f0c8838c8e21b6fea84d356b7374f.gif)

## ✨ Características Principales

- **🤖 Asistente de IA Integrado**: Genera automáticamente tareas y estimaciones de tiempo para tus proyectos
- **📊 Diagramas de Gantt Interactivos**: Visualiza la planificación temporal de tus proyectos
- **📈 KPIs y Métricas**: Analiza el progreso, precisión de estimaciones y rendimiento de proyectos
- **🔄 Soporte Multi-IA**: Compatible con OpenAI (GPT-3.5/4) y Ollama (modelos locales)
- **💾 Base de Datos SQLite**: Almacenamiento local y persistente de proyectos y tareas
- **🎨 Interfaz Moderna**: UI intuitiva construida con Streamlit y estilos personalizados

## 🛠️ Tecnologías Utilizadas

- **Backend**: Python 3.8+
- **Framework Web**: Streamlit
- **Base de Datos**: SQLite3
- **Visualización**: Plotly, Pandas
- **IA**: OpenAI API, Ollama (local)
- **Gestión de Dependencias**: pip, requirements.txt

## 📋 Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- (Opcional) Ollama instalado para IA local
- (Opcional) API Key de OpenAI para usar GPT-3.5/4

## 🚀 Instalación

### 1. Clonar o descargar el proyecto

```bash
git clone <repository-url>
cd DevPlanner
```

### 2. Crear entorno virtual (recomendado)

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

## 🎯 Uso

### Iniciar la aplicación

```bash
streamlit run devplanner.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

### Configuración de IA

#### Opción 1: OpenAI (Nube)

1. Ve a la sección **⚙️ Configuración de IA**
2. Selecciona **OpenAI** como proveedor
3. Elige el modelo (gpt-3.5-turbo, gpt-4, gpt-4-turbo)
4. Ingresa tu [API Key de OpenAI](https://platform.openai.com/api-keys)
5. Prueba la conexión y guarda

#### Opción 2: Ollama (Local)

1. [Instala Ollama](https://ollama.ai/)
2. Descarga un modelo: `ollama pull phi3` (o llama3, mistral, etc.)
3. Inicia Ollama: `ollama serve`
4. En DevPlanner, selecciona **Ollama** como proveedor
5. Elige el modelo instalado
6. Prueba la conexión y guarda

## 📚 Funcionalidades

### Gestión de Proyectos

- **Crear proyectos**: Define nombre, descripción y estado
- **Generación automática de tareas**: Usa IA para desglosar proyectos en tareas detalladas
- **Añadir tareas manualmente**: Crea tareas personalizadas con estimaciones de tiempo
- **Actualizar estado**: Trackea el progreso (pendiente, en progreso, completado)
- **Gestión de fechas**: Define fechas de inicio y fin para cada tarea

### Visualización

- **Diagrama de Gantt**: Visualización temporal de todas las tareas del proyecto
- **Gráficos de estado**: Distribución de tareas por estado (pendiente/en progreso/completado)
- **Comparativa de horas**: Gráfico de horas estimadas vs horas reales

### Análisis y KPIs

- Total de tareas y tareas completadas
- Ratio de progreso del proyecto
- Horas estimadas vs horas reales
- Precisión de estimaciones
- Recomendaciones automáticas basadas en métricas

## 📁 Estructura del Proyecto

```
DevPlanner/
│
├── devplanner.py          # Aplicación principal
├── devplanner.db          # Base de datos SQLite (generada automáticamente)
├── requirements.txt       # Dependencias del proyecto
├── README.md             # Este archivo
│
├── venv/                 # Entorno virtual (no incluido en repositorio)
│
└── OLD/                  # Versiones anteriores del código
    ├── devp2.py
    ├── devp3.py
    ├── devp4.py
    └── devp5.py
```

## 🗄️ Esquema de Base de Datos

### Tabla: `projects`

- `id`: INTEGER PRIMARY KEY
- `name`: TEXT (nombre del proyecto)
- `description`: TEXT (descripción)
- `created_at`: TIMESTAMP
- `status`: TEXT (planning, active, completed, on_hold)

### Tabla: `tasks`

- `id`: INTEGER PRIMARY KEY
- `project_id`: INTEGER (FK a projects)
- `description`: TEXT (descripción de la tarea)
- `estimated_hours`: REAL (horas estimadas)
- `actual_hours`: REAL (horas reales)
- `status`: TEXT (pending, in_progress, completed)
- `start_date`: DATE
- `end_date`: DATE
- `dependencies`: TEXT (JSON de dependencias)

### Tabla: `ai_config`

- `id`: INTEGER PRIMARY KEY
- `ai_provider`: TEXT (openai, ollama)
- `ai_model`: TEXT (nombre del modelo)
- `api_key`: TEXT (API key si aplica)
- `created_at`: TIMESTAMP

## 🔒 Seguridad

- Las API keys se almacenan localmente en la base de datos SQLite
- No se transmiten datos a servidores externos excepto a los proveedores de IA configurados
- Se recomienda no compartir el archivo `devplanner.db` si contiene API keys sensibles
- Usa variables de entorno o archivos `.env` para mayor seguridad en producción

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Para cambios importantes:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Roadmap

- [ ] Exportación de proyectos a PDF
- [ ] Integración con calendarios (Google Calendar, Outlook)
- [ ] Colaboración multi-usuario
- [ ] Notificaciones y recordatorios
- [ ] Integración con herramientas de seguimiento de tiempo
- [ ] Plantillas de proyectos predefinidas
- [ ] API REST para integración externa

## 🐛 Reportar Issues

Si encuentras algún bug o tienes sugerencias, por favor:

1. Verifica que no exista un issue similar
2. Crea un nuevo issue con una descripción detallada
3. Incluye pasos para reproducir el problema (si aplica)

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 👨‍💻 Autor

Desarrollado con ❤️ usando Python y Streamlit

---

**¿Preguntas o comentarios?** Abre un issue o contacta al equipo de desarrollo.
