import streamlit as st
import requests
from streamlit_cookies_controller import CookieController
import base64
from streamlit_option_menu import option_menu
from datetime import datetime

  # Configuración de la página
st.set_page_config(
    page_title="Gestor de Procesos",
    page_icon="📦", # Puedes usar un emoji o la ruta a un archivo .png
    layout="wide"    # Aprovecha todo el ancho de la pantalla
    )

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file: # Funcion que convierte imagen a base64
        return base64.b64encode(img_file.read()).decode()    

    
img_base64 = get_base64_image("banner.png") # Carga imagen para banner

def test_server():
    respuesta = requests.get("http://10.0.9.227:8090")
    if respuesta.status_code == 200:
        return respuesta
    return "Servidor con Falla, Checar con TI"

controller = CookieController()

# 1. Inicializar el estado de autenticación
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

cookie_session = controller.get("zeutica_session")
if cookie_session and not st.session_state.autenticado:
    st.session_state.autenticado = True
    st.session_state.usuario_nombre = cookie_session

def validar_acceso(user, pw):
    try:
        res = requests.post("http://10.0.9.227:8090/login", json={"usuario": user, "password": pw})
        if res.status_code == 200:
            st.session_state.autenticado = True
            st.session_state.usuario_nombre = usuario
            controller.set("zeutica_session", usuario, max_age=1800)
            st.success("¡Bienvenido!")
            st.rerun()
        else:
            st.error("Credenciales inválidas")

    except Exception as e:

        st.error(f"Error de conexión: {e}")

# 2. Lógica de visualización
if not st.session_state.autenticado:
    # Mostramos solo el formulario de login
    fondo_url = "https://bucket-prueban8n.s3.us-east-2.amazonaws.com/logo.png"
    
    st.markdown(f"""
    <style>
    /* 1. Fondo general */
    [data-testid="stAppViewContainer"] {{
        background-image: url("{fondo_url}");
        background-size: cover;
        background-position: center;
    }}
    
    /* 2. Contenedor del Login (Más opaco para legibilidad) */
    .login-box {{
        background: rgba(0, 0, 0, 0.6); /* Fondo oscuro semitransparente */
        backdrop-filter: blur(12px);
        padding: 50px;
        border-radius: 25px;
        border: 2px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5);
        max-width: 450px;
        margin: auto;
    }}
    
    /* 3. Etiquetas (Usuario/Contraseña) en blanco con sombra */
    label[data-testid="stWidgetLabel"] p {{
        color: white !important;
        font-size: 18px !important;
        font-weight: bold !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,1);
    }}
    
    /* 4. Inputs (Campos de escritura) resaltados */
    .stTextInput input {{
        background-color: white !important;
        color: #1E1E1E !important;
        border-radius: 10px !important;
        border: 2px solid #004A99 !important; /* Borde azul Zeutica */
        height: 45px !important;
    }}

    /* 5. Título */
    .login-title {{
        color: white;
        font-size: 30px;
        font-weight: 800;
        margin-bottom: 35px;
        text-align: center;
        text-shadow: 2px 2px 5px rgba(0,0,0,0.8);
    }}
    </style>
""", unsafe_allow_html=True)

    with st.container():
        st.title("🔐 Acceso Privado Zeutica")
        usuario = st.text_input("Usuario")
        clave = st.text_input("Contraseña", type="password")
        
        if st.button("Entrar"):
            validar_acceso(usuario, clave)
else:  

    st.title("📦 Panel de Servicios")
    st.markdown("Consulta el stock actual del inventario.")

    st.markdown(f"""
    <style>
    .main-banner {{
        background-image: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), 
                          url("data:image/jpg;base64,{img_base64}");
        background-size: cover;
        background-position: center;
        padding: 50px;
        color: white;
        text-align: center;
        border-radius: 10px;
    }}
    </style>
    <div class="main-banner">
        <h1>Sistema de Inventario Zeutica</h1>
        <p>Hola {st.session_state.get("usuario_nombre", "usuario")}, Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</p>
    </div>
    """, unsafe_allow_html=True)

    selected = option_menu(
    menu_title=None,  # No necesitamos título de menú
    options=["Inventario", "Ventas", "Cotizaciones", "Clientes", "Reportes", "Traspaso FULL", "Gastos Operativos"], # Opciones del menú
    icons=["archive", "cash-stack", "file-earmark-text", "people", "archive","archive", "people"], # Iconos de bootstrap
    menu_icon="cast", 
    default_index=0, 
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#f0f2f6"},
        "icon": {"color": "#004a99", "font-size": "18px"}, 
        "nav-link": {
            "font-size": "16px", 
            "text-align": "center", 
            "margin": "0px", 
            "color": "#444"
        },
        "nav-link-selected": {"background-color": "#004a99", "color": "white"},
    }
    )

    # --- 3. LÓGICA DE PÁGINAS ---
    if selected == "Inventario":
        # Lee y ejecuta el archivo de inventario
        with open("paginas/inventario.py", encoding="utf-8") as f:
            exec(f.read())

    elif selected == "Cotizaciones":
        # Lee y ejecuta tu generador de cotizaciones [cite: 5]
        with open("paginas/cotizaciones.py", encoding="utf-8") as f:
            exec(f.read())

    elif selected == "Ventas":  
        # Lee y ejecuta el registro de ventas 
        with open("paginas/ventasPagina.py", encoding="utf-8") as f:
            exec(f.read())

    elif selected == "Clientes":
        # Lee y ejecuta el directorio de clientes 
        with open("paginas/nvocliente.py", encoding="utf-8") as f:
            exec(f.read())

    elif selected == "Reportes":
        # Lee y ejecuta el directorio de clientes 
        with open("paginas/reporteVentas.py", encoding="utf-8") as f:
            exec(f.read())

    elif selected == "Traspaso FULL":
        # Lee y ejecuta full
        with open("paginas/full.py", encoding="utf-8") as f:
            exec(f.read()) 
    
    elif selected == "Gastos Operativos":
        # Lee y ejecuta full        
        with open("paginas/gastos.py", encoding="utf-8") as f:
            exec(f.read())
        

    with st.sidebar: # datos al costado
        st.image("logo.png", use_container_width=True)
        st.title("Panel de Procesos")
        s = test_server()
        st.sidebar.info(s.json())
        #st.info("Conectado a Zeutica Server")
        if st.button("Limpiar Caché"):
            st.cache_data.clear()
        st.sidebar.info("Panel Gestion Procesos")
        st.sidebar.info(f"Usuario logeado: {st.session_state.get("usuario_nombre", "usuario")}")    
        #st.sidebar.button("Cerrar Sesión", on_click=lambda: st.session_state.update({"autenticado": False}))
        if st.sidebar.button("Cerrar Sesión"):
            controller.remove("zeutica_session")
            st.session_state.autenticado = False
            st.rerun()

        
   

    