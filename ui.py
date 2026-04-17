import streamlit as st
import requests
from streamlit_cookies_controller import CookieController
import base64
from streamlit_option_menu import option_menu
from streamlit_javascript import st_javascript

API_BASE_URL = "http://10.0.9.227:8090" #url produccion
#API_BASE_URL = "http://127.0.0.1:8000"
cliente_hora = st_javascript("new Date().toLocaleString()")

# Configuración de la página
st.set_page_config(
    page_title="Gestor de Procesos",
    page_icon="📦", # Puedes usar un emoji o la ruta a un archivo .png
    layout="wide"    # Aprovecha todo el ancho de la pantalla
)

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file: # Funcion que convierte imagen a base64
        return base64.b64encode(img_file.read()).decode()    

img_base64 = get_base64_image("zeuticaBanner.png") # Carga imagen para banner

def test_server():
    respuesta = requests.get(API_BASE_URL)
    if respuesta.status_code == 200:
        return respuesta
    return "Servidor con Falla, Checar con TI"

controller = CookieController()

# 1. Inicializar el estado de autenticación
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# El CookieController necesita un ciclo de render para leer las cookies del browser;
# en el primer render puede lanzar TypeError, lo capturamos y esperamos el rerun automático
try:
    cookie_session = controller.get("zeutica_session")
    cookie_token = controller.get("zeutica_token")
except Exception:
    cookie_session = None
    cookie_token = None

# Restauramos sesión completa desde cookies; sin token no hay acceso a la API
if cookie_session and cookie_token and not st.session_state.autenticado:
    st.session_state.autenticado = True
    st.session_state.usuario_nombre = cookie_session
    st.session_state.token = cookie_token
    st.session_state.ip = "http://10.0.9.227:8090" #url produccion
    #st.session_state.ip = "http://127.0.0.1:8000"

def validar_acceso(user, pw):
    try:
        res = requests.post(f"{API_BASE_URL}/login", json={"usuario": user, "password": pw})
        if res.status_code == 200:
            token = res.json()["access_token"]
            st.session_state.autenticado = True
            st.session_state.usuario_nombre = user  # Corregido: era 'usuario'
            st.session_state.token = token
            st.session_state.ip = "http://10.0.9.227:8090" #url produccion
            #st.session_state.ip = "http://127.0.0.1:8000"
            # Guardamos usuario y token en cookies para sobrevivir el refresh
            controller.set("zeutica_session", user, max_age=1800)
            controller.set("zeutica_token", token, max_age=1800)
            st.success("¡Bienvenido!")
            st.rerun()
        else:
            st.error("Credenciales inválidas")
    except Exception as e:
        st.error(f"Error de conexión: {e}")

# 2. Lógica de visualización
if not st.session_state.autenticado:
    # Mostramos solo el formulario de login
    fondo_url = "https://bucket-prueban8n.s3.us-east-2.amazonaws.com/zeuticaBanner.png"
    
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

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("Actualizacion de sistema:\n" \
        "Fallos en relacion cotizacion/factura")
    with col3:
        st.error("NO OLVIDES INGRESAR LAS VENTAS DE AMAZON!")

    with col2:
        with st.container():
            st.title("🔐 Acceso Consola Zeutica")
            usuario = st.text_input("Usuario")
            clave = st.text_input("Contraseña", type="password")
        
        if st.button("Entrar"):
            usuario = usuario.lower()
            validar_acceso(usuario, clave)

#AQUI ESTABA EL ERROR: El else debe ir a la altura del if not autenticado
else:  
    st.title("📦 Panel de Servicios")
    st.markdown("Consulta el stock actual del inventario.")
    #st.write(st.session_state.token)
    
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
        <p>Hola {st.session_state.get('usuario_nombre', 'usuario')}, Fecha: {cliente_hora}</p>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.image("logo.png", use_container_width=True)
        st.markdown(f"👤 **{st.session_state.get('usuario_nombre', 'usuario')}**")
        st.divider()

        selected = option_menu(
            menu_title="Navegación",
            options=["Dashboard", "Inventario", "Ventas", "Cotizaciones", "Clientes",
                     "Reportes", "Traspaso FULL", "Gastos Operativos", "Cuentas Pendientes",
                     "CleanestChoice", "Compras"],
            icons=["speedometer2", "boxes", "cash-coin", "file-earmark-richtext",
                   "person-lines-fill", "bar-chart-line", "arrow-left-right",
                   "wallet2", "clock-history", "stars", "cart4"],
            menu_icon="grid-3x3-gap-fill",
            default_index=0,
            orientation="vertical",
            styles={
                "container": {
                    "padding": "8px 4px",
                    "background-color": "#0d1b2a",
                    "border-radius": "12px",
                },
                "menu-title": {
                    "color": "#7eb3e8",
                    "font-size": "13px",
                    "font-weight": "600",
                    "letter-spacing": "1px",
                    "text-transform": "uppercase",
                    "padding-bottom": "6px",
                },
                "menu-icon": {"color": "#7eb3e8", "font-size": "16px"},
                "icon": {"color": "#7eb3e8", "font-size": "16px"},
                "nav-link": {
                    "font-size": "14px",
                    "color": "#c8d8e8",
                    "border-radius": "8px",
                    "margin": "2px 0px",
                    "padding": "9px 14px",
                    "--hover-color": "#1e3a5f",
                },
                "nav-link-selected": {
                    "background-color": "#004a99",
                    "color": "white",
                    "font-weight": "600",
                    "box-shadow": "0 2px 8px rgba(0,74,153,0.4)",
                },
            },
        )

        st.divider()
        s = test_server()
        if isinstance(s, str):
            st.error(s)
        else:
            st.success("🟢 Servidor activo")

        if st.button("🗑️ Limpiar Caché", use_container_width=True):
            st.cache_data.clear()

        if st.button("🚪 Cerrar Sesión", use_container_width=True, type="primary"):
            controller.remove("zeutica_session")
            controller.remove("zeutica_token")
            st.session_state.autenticado = False
            st.rerun()

    # ---  LÓGICA DE PÁGINAS ---
    if selected == "Dashboard":
        if st.session_state.usuario_nombre == "gerencia":
            with open("paginas/dashboard.py", encoding="utf-8") as f:
                exec(f.read())
        else:
            # 3. Mensaje de error persistente
            st.error("### 🛑 ACCESO RESTRINGIDO")
            st.subheader("Sección: Dashboard")
            st.write(f"Lo sentimos **{st.session_state.get('usuario_nombre', 'Usuario')}**, no tienes los permisos necesarios para visualizar esta información.")

    elif selected == "Inventario":
        # Lee y ejecuta el archivo de inventario
        with open("paginas/inventario.py", encoding="utf-8") as f:
            exec(f.read())

    elif selected == "Cotizaciones":
        # Lee y ejecuta tu generador de cotizaciones
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

    elif selected == "Cuentas Pendientes":
        if st.session_state.usuario_nombre == "gerencia":
            # Lee y ejecuta full        
            with open("paginas/por_cobrar-pagar.py", encoding="utf-8") as f:
                exec(f.read())
        else:
            # 3. Mensaje de error persistente
            st.error("### 🛑 ACCESO RESTRINGIDO")
            st.subheader("Sección: Cuentas Pendientes")
            st.write(f"Lo sentimos **{st.session_state.get('usuario_nombre', 'Usuario')}**, no tienes los permisos necesarios para visualizar esta información.")

    elif selected == "CleanestChoice":
        # Lee y ejecuta full        
        with open("paginas/cleanestc.py", encoding="utf-8") as f:
            exec(f.read())

    elif selected == "Compras":
        if st.session_state.usuario_nombre == "gerencia":
            # Lee y ejecuta full        
            with open("paginas/compras.py", encoding="utf-8") as f:
                exec(f.read())
        else:
            # 3. Mensaje de error persistente
            st.error("### 🛑 ACCESO RESTRINGIDO")
            st.subheader("Sección: Compras")
            st.write(f"Lo sentimos **{st.session_state.get('usuario_nombre', 'Usuario')}**, no tienes los permisos necesarios para visualizar esta información.")

        