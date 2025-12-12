import streamlit as st
import sqlite3
import json
import plotly.express as px
import pandas as pd
import requests
import datetime
from datetime import timedelta
import time
import os
from openai import OpenAI

# Configuración de la página
st.set_page_config(
    page_title="DevPlanner - Gestión de Proyectos con IA",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #0D47A1;
        border-bottom: 2px solid #64B5F6;
        padding-bottom: 0.5rem;
    }
    .success-box {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4CAF50;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2196F3;
        margin-bottom: 1rem;
    }
    .project-card {
        background-color: #F5F5F5;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        font-weight: bold;
    }
    .config-section {
        background-color: #FFF8E1;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #FFC107;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Inicialización de la base de datos
def init_db():
    conn = sqlite3.connect('devplanner.db')
    c = conn.cursor()
    
    # Tabla de proyectos
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'planning'
        )
    ''')
    
    # Tabla de tareas
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            description TEXT NOT NULL,
            estimated_hours REAL,
            actual_hours REAL DEFAULT 0,
            status TEXT DEFAULT 'pending',
            start_date DATE,
            end_date DATE,
            dependencies TEXT,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
    ''')
    
    # Tabla de configuraciones de IA
    c.execute('''
        CREATE TABLE IF NOT EXISTS ai_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ai_provider TEXT DEFAULT 'openai',
            ai_model TEXT DEFAULT 'gpt-3.5-turbo',
            api_key TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insertar configuración por defecto si no existe
    c.execute('SELECT COUNT(*) FROM ai_config')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO ai_config (ai_provider, ai_model) VALUES (?, ?)', 
                 ('openai', 'gpt-3.5-turbo'))
    
    conn.commit()
    conn.close()

# Funciones de base de datos
def get_db_connection():
    return sqlite3.connect('devplanner.db')

# Funciones para proyectos
def create_project(name, description, status='planning'):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO projects (name, description, status) VALUES (?, ?, ?)', 
             (name, description, status))
    project_id = c.lastrowid
    conn.commit()
    conn.close()
    return project_id

def get_projects():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM projects ORDER BY created_at DESC')
    projects = c.fetchall()
    conn.close()
    return projects

def get_project(project_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
    project = c.fetchone()
    conn.close()
    return project

# Funciones para tareas
def add_task(project_id, description, estimated_hours, start_date, end_date, dependencies=None):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO tasks (project_id, description, estimated_hours, start_date, end_date, dependencies)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (project_id, description, estimated_hours, start_date, end_date, dependencies))
    conn.commit()
    conn.close()

def get_tasks(project_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM tasks WHERE project_id = ? ORDER BY start_date', (project_id,))
    tasks = c.fetchall()
    conn.close()
    return tasks

# Funciones para IA
def get_ai_config():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM ai_config ORDER BY created_at DESC LIMIT 1')
    config = c.fetchone()
    conn.close()
    return config

def save_ai_config(ai_provider, ai_model, api_key=None):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO ai_config (ai_provider, ai_model, api_key)
        VALUES (?, ?, ?)
    ''', (ai_provider, ai_model, api_key))
    conn.commit()
    conn.close()

def test_ollama_connection():
    """Prueba la conexión con Ollama"""
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=10)
        return response.status_code == 200
    except:
        return False

def test_openai_connection(api_key):
    """Prueba la conexión con OpenAI"""
    try:
        client = OpenAI(api_key=api_key)
        response = client.models.list()
        return True
    except:
        return False

def generate_tasks_with_ai(project_description, ai_provider, ai_model, api_key=None):
    """
    Genera tareas para un proyecto usando IA (OpenAI u Ollama)
    """
    prompt = f"""
    Como experto en planificación de proyectos de desarrollo de software, desglosa el siguiente proyecto en tareas técnicas detalladas.
    Para cada tarea, proporciona una estimación de tiempo en horas.
    
    Proyecto: {project_description}
    
    Devuelve la respuesta en formato JSON con la siguiente estructura:
    {{
        "tasks": [
            {{
                "description": "Descripción de la tarea",
                "estimated_hours": 8.0,
                "dependencies": []  // opcional: índices de tareas de las que depende (0-indexed)
            }}
        ]
    }}
    
    Sé preciso y realista con las estimaciones. Considera dependencias entre tareas cuando sea necesario.
    """
    
    if ai_provider == 'ollama':
        # Usar Ollama local
        try:
            # Verificar que Ollama esté disponible
            if not test_ollama_connection():
                st.error("Ollama no está disponible. Asegúrate de que esté instalado y ejecutándose.")
                return []
                
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': ai_model,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': 0.7
                    }
                },
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                # Parsear la respuesta para extraer el JSON
                response_text = result['response']
                # Intentar encontrar JSON en la respuesta
                try:
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}') + 1
                    json_str = response_text[start_idx:end_idx]
                    tasks_data = json.loads(json_str)
                    return tasks_data.get('tasks', [])
                except json.JSONDecodeError:
                    st.error("Error al analizar la respuesta de la IA. La respuesta no tenía formato JSON válido.")
                    st.text(f"Respuesta recibida: {response_text}")
                    return []
            else:
                st.error(f"Error al conectar con Ollama: {response.status_code}")
                return []
        except requests.exceptions.RequestException as e:
            st.error(f"Error de conexión con Ollama: {str(e)}")
            return []
    
    elif ai_provider == 'openai':
        # Usar OpenAI (requiere API key)
        try:
            if not api_key:
                st.error("Se requiere una API key de OpenAI")
                return []
                
            client = OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model=ai_model,
                messages=[
                    {"role": "system", "content": "Eres un asistente experto en planificación de proyectos de desarrollo de software."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content
            # Intentar encontrar JSON en la respuesta
            try:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                json_str = response_text[start_idx:end_idx]
                tasks_data = json.loads(json_str)
                return tasks_data.get('tasks', [])
            except json.JSONDecodeError:
                st.error("Error al analizar la respuesta de la IA. La respuesta no tenía formato JSON válido.")
                st.text(f"Respuesta recibida: {response_text}")
                return []
                
        except Exception as e:
            st.error(f"Error al conectar con OpenAI: {str(e)}")
            return []
    
    return []

# Funciones para visualización
def create_gantt_chart(tasks):
    if not tasks:
        return None
    
    task_data = []
    for i, task in enumerate(tasks):
        # task structure: (id, project_id, description, estimated_hours, actual_hours, status, start_date, end_date, dependencies)
        start_date = datetime.datetime.strptime(task[6], '%Y-%m-%d').date() if isinstance(task[6], str) else task[6]
        end_date = datetime.datetime.strptime(task[7], '%Y-%m-%d').date() if isinstance(task[7], str) else task[7]
        
        task_data.append({
            'Task': task[2],
            'Start': start_date,
            'Finish': end_date,
            'Hours': task[3],
            'Status': task[5]
        })
    
    df = pd.DataFrame(task_data)
    
    color_map = {
        'pending': '#FFC107',
        'in_progress': '#2196F3',
        'completed': '#4CAF50'
    }
    
    fig = px.timeline(
        df, 
        x_start="Start", 
        x_end="Finish", 
        y="Task",
        color="Status",
        color_discrete_map=color_map,
        hover_data=["Hours"],
        title="Diagrama de Gantt del Proyecto"
    )
    
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        height=400,
        showlegend=True,
        xaxis_title="Fecha",
        yaxis_title="Tareas"
    )
    
    return fig

def calculate_kpis(tasks):
    if not tasks:
        return {}
    
    total_estimated = sum(task[3] for task in tasks if task[3])
    total_actual = sum(task[4] for task in tasks if task[4])
    completed_tasks = sum(1 for task in tasks if task[5] == 'completed')
    total_tasks = len(tasks)
    
    completion_ratio = completed_tasks / total_tasks if total_tasks > 0 else 0
    accuracy_ratio = 1 - abs(total_estimated - total_actual) / total_estimated if total_estimated > 0 else 0
    
    return {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'completion_ratio': completion_ratio,
        'total_estimated_hours': total_estimated,
        'total_actual_hours': total_actual,
        'accuracy_ratio': accuracy_ratio
    }

# Interfaz de usuario principal
def main():
    # Inicializar base de datos
    init_db()
    
    st.markdown('<h1 class="main-header">🚀 DevPlanner</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem;">Tu asistente de planificación de proyectos con IA integrada</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/rocket.png", width=80)
        st.title("Menú de Navegación")
        
        menu_option = st.radio(
            "Selecciona una opción:",
            ["📋 Proyectos", "⚙️ Configuración de IA", "📊 KPIs y Métricas"]
        )
        
        st.markdown("---")
        st.markdown("### Acerca de DevPlanner")
        st.info("""
        DevPlanner te ayuda a:
        - Desglosar proyectos en tareas
        - Estimar tiempos con IA
        - Generar diagramas de Gantt
        - Analizar KPIs de proyectos
        """)
    
    # Página de Proyectos
    if menu_option == "📋 Proyectos":
        st.markdown('<h2 class="sub-header">Gestión de Proyectos</h2>', unsafe_allow_html=True)
        
        # Crear nuevo proyecto
        with st.expander("➕ Crear Nuevo Proyecto", expanded=True):
            col1, col2 = st.columns([2, 1])
            with col1:
                project_name = st.text_input("Nombre del Proyecto")
            with col2:
                project_status = st.selectbox("Estado", ["planning", "active", "completed", "on_hold"])
            
            project_description = st.text_area("Descripción del Proyecto", height=100,
                                             placeholder="Describe tu proyecto en detalle. Cuanta más información proporciones, mejores serán las recomendaciones de IA.")
            
            if st.button("🎯 Crear Proyecto", use_container_width=True):
                if project_name:
                    project_id = create_project(project_name, project_description, project_status)
                    st.success(f"Proyecto '{project_name}' creado exitosamente!")
                    st.rerun()
                else:
                    st.error("Por favor, ingresa un nombre para el proyecto.")
        
        # Lista de proyectos existentes
        st.markdown("### Mis Proyectos")
        projects = get_projects()
        
        if not projects:
            st.info("Aún no hay proyectos creados. ¡Comienza creando uno nuevo!")
        else:
            for project in projects:
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f'<div class="project-card">', unsafe_allow_html=True)
                        st.markdown(f"#### {project[1]}")
                        st.markdown(f"**Descripción:** {project[2]}")
                        st.markdown(f"**Estado:** {project[4]}")
                        st.markdown(f"**Creado:** {project[3]}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col2:
                        if st.button("Abrir", key=f"btn_{project[0]}"):
                            st.session_state.current_project = project[0]
                    
                    # Mostrar tareas si el proyecto está seleccionado
                    if 'current_project' in st.session_state and st.session_state.current_project == project[0]:
                        tasks = get_tasks(project[0])
                        
                        # Generar tareas con IA
                        with st.expander("🤖 Generar Tareas con IA", expanded=False):
                            ai_config = get_ai_config()
                            if ai_config:
                                st.info("Usando configuración: " + ai_config[1] + " - " + ai_config[2])
                                
                                if st.button("Generar plan de tareas con IA", key=f"ai_btn_{project[0]}"):
                                    with st.spinner("Generando tareas con IA..."):
                                        ai_tasks = generate_tasks_with_ai(
                                            project[2],  # Usar la descripción del proyecto actual
                                            ai_config[1], 
                                            ai_config[2],
                                            ai_config[3] if ai_config[3] else None
                                        )
                                        
                                        if ai_tasks:
                                            st.success(f"IA ha generado {len(ai_tasks)} tareas!")
                                            
                                            # Calcular fechas basadas en duraciones
                                            start_date = datetime.date.today()
                                            for i, task in enumerate(ai_tasks):
                                                duration = max(1, round(task['estimated_hours'] / 8))  # Mínimo 1 día
                                                end_date = start_date + timedelta(days=duration)
                                                
                                                # Guardar tarea
                                                add_task(
                                                    project[0],
                                                    task['description'],
                                                    task['estimated_hours'],
                                                    start_date,
                                                    end_date,
                                                    str(task.get('dependencies', []))
                                                )
                                                
                                                # La siguiente tarea comienza después de esta (a menos que tenga dependencias)
                                                if not task.get('dependencies'):
                                                    start_date = end_date
                                            
                                            st.rerun()
                                        else:
                                            st.error("No se pudieron generar tareas. Revisa la configuración de IA.")
                            
                        # Añadir tareas manualmente
                        with st.expander("✏️ Añadir Tarea Manualmente", expanded=False):
                            col1, col2 = st.columns(2)
                            with col1:
                                task_desc = st.text_input("Descripción de la tarea", key=f"desc_{project[0]}")
                                estimated_hours = st.number_input("Horas estimadas", min_value=0.5, step=0.5, value=8.0, key=f"hours_{project[0]}")
                            with col2:
                                start_date = st.date_input("Fecha de inicio", value=datetime.date.today(), key=f"start_{project[0]}")
                                end_date = st.date_input("Fecha de fin", value=datetime.date.today() + timedelta(days=7), key=f"end_{project[0]}")
                            
                            if st.button("Añadir Tarea", key=f"add_task_{project[0]}"):
                                if task_desc:
                                    add_task(project[0], task_desc, estimated_hours, start_date, end_date)
                                    st.success("Tarea añadida exitosamente!")
                                    st.rerun()
                                else:
                                    st.error("Por favor, ingresa una descripción para la tarea.")
                        
                        # Mostrar tareas existentes
                        if tasks:
                            st.markdown("### Tareas del Proyecto")
                            for task in tasks:
                                col1, col2, col3, col4 = st.columns([3, 1, 1, 0.5])
                                with col1:
                                    st.markdown(f"**{task[2]}**")
                                    st.markdown(f"Estimado: {task[3]} horas | Real: {task[4]} horas")
                                    st.markdown(f"Fechas: {task[6]} a {task[7]}")
                                with col2:
                                    status = st.selectbox("Estado", ["pending", "in_progress", "completed"], 
                                                        key=f"status_{task[0]}", index=["pending", "in_progress", "completed"].index(task[5]))
                                    if status != task[5]:
                                        # Actualizar estado en la base de datos
                                        conn = get_db_connection()
                                        c = conn.cursor()
                                        c.execute('UPDATE tasks SET status = ? WHERE id = ?', (status, task[0]))
                                        conn.commit()
                                        conn.close()
                                        st.rerun()
                                with col3:
                                    actual_hours = st.number_input("Horas reales", min_value=0.0, value=float(task[4]), step=0.5, key=f"actual_{task[0]}")
                                    if actual_hours != task[4]:
                                        conn = get_db_connection()
                                        c = conn.cursor()
                                        c.execute('UPDATE tasks SET actual_hours = ? WHERE id = ?', (actual_hours, task[0]))
                                        conn.commit()
                                        conn.close()
                                        st.rerun()
                                with col4:
                                    if st.button("🗑️", key=f"delete_{task[0]}"):
                                        conn = get_db_connection()
                                        c = conn.cursor()
                                        c.execute('DELETE FROM tasks WHERE id = ?', (task[0],))
                                        conn.commit()
                                        conn.close()
                                        st.success("Tarea eliminada!")
                                        st.rerun()
                            
                            # Mostrar diagrama de Gantt
                            st.markdown("### Diagrama de Gantt")
                            gantt_chart = create_gantt_chart(tasks)
                            if gantt_chart:
                                st.plotly_chart(gantt_chart, use_container_width=True)
                            else:
                                st.info("No hay suficientes tareas para generar un diagrama de Gantt.")
                            
                            # Mostrar KPIs
                            st.markdown("### Métricas del Proyecto")
                            kpis = calculate_kpis(tasks)
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Tareas", kpis['total_tasks'])
                                st.metric("Tareas Completadas", kpis['completed_tasks'])
                            with col2:
                                st.metric("Horas Estimadas", f"{kpis['total_estimated_hours']:.1f}")
                                st.metric("Horas Reales", f"{kpis['total_actual_hours']:.1f}")
                            with col3:
                                st.metric("Progreso", f"{kpis['completion_ratio']*100:.1f}%")
                                st.metric("Precisión Estimación", f"{kpis['accuracy_ratio']*100:.1f}%")
                        else:
                            st.info("Este proyecto no tiene tareas aún. ¡Añade algunas tareas manualmente o genera un plan con IA!")
    
    # Página de Configuración de IA
    elif menu_option == "⚙️ Configuración de IA":
        st.markdown('<h2 class="sub-header">Configuración de Asistente de IA</h2>', unsafe_allow_html=True)
        
        ai_config = get_ai_config()
        
        with st.form("ai_config_form"):
            st.markdown('<div class="config-section">', unsafe_allow_html=True)
            st.markdown("### Proveedor de IA")
            
            ai_provider = st.radio(
                "Selecciona tu proveedor de IA preferido:",
                ["openai", "ollama"],
                index=0 if ai_config[1] == "openai" else 1,
                help="OpenAI para máxima compatibilidad, Ollama para uso local"
            )
            
            if ai_provider == "openai":
                st.markdown("### Configuración de OpenAI")
                ai_model = st.selectbox(
                    "Modelo de OpenAI:",
                    ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
                    index=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"].index(ai_config[2]) if ai_config[2] in ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"] else 0
                )
                api_key = st.text_input("API Key de OpenAI", type="password", value=ai_config[3] if ai_config[3] else "", 
                                      help="Tu clave API de OpenAI. Se almacenará localmente de forma segura.")
            
            else:
                st.markdown("### Configuración de Ollama (Local)")
                ai_model = st.selectbox(
                    "Modelo de Ollama:",
                    ["phi3", "llama2", "mistral", "mixtral", "codellama", "gemma", "llama3"],
                    index=["phi3", "llama2", "mistral", "mixtral", "codellama", "gemma", "llama3"].index(ai_config[2]) if ai_config[2] in ["phi3", "llama2", "mistral", "mixtral", "codellama", "gemma", "llama3"] else 0
                )
                api_key = None
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            if st.form_submit_button("💾 Guardar Configuración", use_container_width=True):
                save_ai_config(ai_provider, ai_model, api_key)
                st.success("Configuración de IA guardada exitosamente!")
        
        # Botones de prueba fuera del formulario
        st.markdown("---")
        st.markdown("### 🔌 Probar Conexión")
        
        current_config = get_ai_config()
        if current_config:
            if current_config[1] == "openai":
                if current_config[3]:
                    if st.button("🧪 Probar conexión con OpenAI"):
                        if test_openai_connection(current_config[3]):
                            st.success("✅ Conexión exitosa con OpenAI!")
                        else:
                            st.error("❌ No se pudo conectar con OpenAI. Verifica tu API key.")
                else:
                    st.warning("⚠️ Primero guarda tu API key de OpenAI para poder probar la conexión.")
            else:  # ollama
                if st.button("🧪 Probar conexión con Ollama"):
                    if test_ollama_connection():
                        st.success("✅ Conexión exitosa con Ollama!")
                    else:
                        st.error("❌ No se pudo conectar con Ollama. Asegúrate de que esté instalado y ejecutándose.")
        
        st.markdown("---")
        st.markdown("### Información de Configuración")
        
        if ai_provider == "ollama":
            st.info("""
            **Configuración para Ollama (IA Local):**
            1. Asegúrate de tener [Ollama instalado](https://ollama.ai/)
            2. Descarga el modelo seleccionado: `ollama pull [modelo]`
            3. Inicia el servicio de Ollama
            4. ¡Listo! DevPlanner se conectará automáticamente
            
            **Recomendación:** Los modelos más ligeros como Phi-3 o TinyLlama son suficientes para la planificación de proyectos.
            """)
        else:
            st.info("""
            **Configuración para OpenAI (Nube):**
            1. Necesitas una [clave API de OpenAI](https://platform.openai.com/api-keys)
            2. Ingresa tu clave API en el campo correspondiente
            3. Selecciona el modelo que deseas usar
            4. ¡Listo! DevPlanner usará la API de OpenAI
            
            **Ventajas:** Mayor potencia y disponibilidad, sin necesidad de instalar software adicional.
            """)
            
        st.markdown("---")
        st.markdown("### 🔒 Seguridad de Datos")
        st.warning("""
        **Importante:** Tu API key se almacena localmente en tu dispositivo y solo se utiliza para realizar 
        solicitudes a los servicios de IA. Nunca se transmite a nuestros servidores.
        
        Para mayor seguridad:
        - Usa siempre conexiones seguras (HTTPS)
        - No compartas tu API key con nadie
        - Revoca tus keys API si las comprometes
        """)
    
    # Página de KPIs y Métricas
    elif menu_option == "📊 KPIs y Métricas":
        st.markdown('<h2 class="sub-header">Métricas y Análisis de Proyectos</h2>', unsafe_allow_html=True)
        
        projects = get_projects()
        if not projects:
            st.info("No hay proyectos para analizar. ¡Crea tu primer proyecto!")
            return
        
        project_options = {f"{p[1]} (ID: {p[0]})": p[0] for p in projects}
        selected_project = st.selectbox("Selecciona un proyecto para analizar:", list(project_options.keys()))
        
        if selected_project:
            project_id = project_options[selected_project]
            tasks = get_tasks(project_id)
            
            if tasks:
                kpis = calculate_kpis(tasks)
                
                # Mostrar KPIs principales
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total de Tareas", kpis['total_tasks'])
                with col2:
                    st.metric("Tareas Completadas", kpis['completed_tasks'], 
                             f"{kpis['completion_ratio']*100:.1f}%")
                with col3:
                    st.metric("Horas Estimadas", f"{kpis['total_estimated_hours']:.1f}")
                with col4:
                    st.metric("Horas Reales", f"{kpis['total_actual_hours']:.1f}", 
                             f"{kpis['accuracy_ratio']*100:.1f}%")
                
                # Gráficos de análisis
                col1, col2 = st.columns(2)
                
                with col1:
                    # Gráfico de estado de tareas
                    status_counts = {}
                    for task in tasks:
                        status = task[5]
                        status_counts[status] = status_counts.get(status, 0) + 1
                    
                    if status_counts:
                        status_df = pd.DataFrame({
                            'Estado': list(status_counts.keys()),
                            'Cantidad': list(status_counts.values())
                        })
                        fig_status = px.pie(status_df, values='Cantidad', names='Estado', 
                                          title="Distribución de Estados de Tareas")
                        st.plotly_chart(fig_status, use_container_width=True)
                
                with col2:
                    # Gráfico de horas estimadas vs reales
                    hours_data = {
                        'Tipo': ['Estimadas', 'Reales'],
                        'Horas': [kpis['total_estimated_hours'], kpis['total_actual_hours']]
                    }
                    hours_df = pd.DataFrame(hours_data)
                    fig_hours = px.bar(hours_df, x='Tipo', y='Horas', 
                                     title="Horas Estimadas vs Reales",
                                     color='Tipo')
                    st.plotly_chart(fig_hours, use_container_width=True)
                
                # Diagrama de Gantt
                st.markdown("### Diagrama de Gantt")
                gantt_chart = create_gantt_chart(tasks)
                if gantt_chart:
                    st.plotly_chart(gantt_chart, use_container_width=True)
                
                # Recomendaciones basadas en análisis
                st.markdown("### Recomendaciones de IA")
                
                if kpis['accuracy_ratio'] < 0.7:
                    st.warning("""
                    **⚠️ Baja precisión en estimaciones:**
                    - Considera revisar tus técnicas de estimación
                    - Usa la función de IA para generar estimaciones más precisas
                    - Desglosa tareas grandes en subtareas más pequeñas
                    """)
                
                if kpis['completion_ratio'] < 0.3 and len(tasks) > 5:
                    st.warning("""
                    **⚠️ Progreso lento del proyecto:**
                    - Revisa si hay cuellos de botella en las dependencias de tareas
                    - Considera reasignar recursos o ajustar el alcance
                    - Prioriza las tareas críticas para el proyecto
                    """)
                
                if kpis['completion_ratio'] > 0.8:
                    st.success("""
                    **✅ Buen progreso del proyecto:**
                    - ¡Sigue así! El proyecto avanza según lo planeado
                    - Considera realizar testing temprano si aplica
                    - Prepara la documentación final
                    """)
                
            else:
                st.info("Este proyecto no tiene tareas para analizar.")

if __name__ == "__main__":
    main()