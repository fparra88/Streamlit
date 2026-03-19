import streamlit as st
import requests
from datetime import datetime

# ============================================================================
# 1. SEGURIDAD Y ESTADO INICIAL
# ============================================================================
if "token" not in st.session_state or "ip" not in st.session_state:
    st.error("⚠️ No hay sesión activa. Por favor, inicia sesión.")
    st.stop()

API_BASE_URL = st.session_state.ip
toks = {"Authorization": f"Bearer {st.session_state.token}"}

# Inicializamos el estado para que los costos no se pierdan al dar Enter
if "costos_bd" not in st.session_state:
    st.session_state.costos_bd = []

# ============================================================================
# 2. FUNCIÓN CALLBACK (Se ejecuta al cambiar el Selectbox)
# ============================================================================
def actualizar_historial():
    # Extraemos el SKU directamente de la sesión usando la 'key' del selectbox
    sku = st.session_state.mi_selector_sku
    
    try:
        res = requests.get(f"{API_BASE_URL}/zeutica/ultimos-costos/{sku}", headers=toks)
        if res.status_code == 200:
            st.session_state.costos_bd = res.json().get("costos", [])
        else:
            st.session_state.costos_bd = []
    except:
        st.session_state.costos_bd = []


st.title("📦 Registrar Compra")
st.divider()

# ============================================================================
# 3. FUNCIÓN PARA OBTENER PRODUCTOS DE LA API
# ============================================================================
@st.cache_data(ttl=300)  # Cache de 5 minutos
def obtener_productos():
    try:
        with st.spinner("Cargando productos..."):
            response = requests.get(f"{API_BASE_URL}/zeutica/productos", headers=toks, timeout=5)
        
        if response.status_code == 200:
            productos = response.json()
            productos_dict = {prod['sku']: prod for prod in productos}
            opciones = [(prod['sku'], f"{prod['sku']} - {prod.get('nombre', 'Sin nombre')}") 
                        for prod in productos]
            return productos_dict, opciones
        else:
            st.error(f"Error al obtener productos: Código {response.status_code}")
            return {}, []
            
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return {}, []

# Cargar productos
productos_dict, opciones_productos = obtener_productos()

if not opciones_productos:
    st.info("No hay productos disponibles o hay un problema de conexión.")
    st.stop()


# ============================================================================
# 4. INTERFAZ DE COMPRA (INTERACTIVA EN TIEMPO REAL)
# ============================================================================
st.subheader("Detalles de la Compra")

col1, col2 = st.columns([1, 2])
with col1:
    sku_seleccionado = st.selectbox(
        "🔍 Selecciona Producto (SKU)",
        options=[opt[0] for opt in opciones_productos],
        format_func=lambda x: next((opt[1] for opt in opciones_productos if opt[0] == x), x),
        key="mi_selector_sku",
        on_change=actualizar_historial 
    )

# --- TRUCO PARA LA PRIMERA CARGA ---
# Si cambiamos de SKU o es la primera vez, forzamos la carga de datos
if "ultimo_sku_consultado" not in st.session_state:
    st.session_state.ultimo_sku_consultado = None

if sku_seleccionado != st.session_state.ultimo_sku_consultado:
    actualizar_historial() # Forzamos la ejecución manual
    st.session_state.ultimo_sku_consultado = sku_seleccionado
# -----------------------------------

producto_seleccionado = productos_dict.get(sku_seleccionado, {})
nombre_producto = producto_seleccionado.get('nombre', 'Sin nombre')    

with col2:
    st.text_input("📝 Nombre del Producto", value=nombre_producto, disabled=True)

st.divider()

# CAMPOS NUMÉRICOS
col3, col4, col5 = st.columns(3)

with col3:
    stock_bodega = st.number_input(
        "📊 Registro de Compra",
        min_value=0,
        value=0,
        step=1,
        help="Cantidad de unidades que ingresan a bodega"
    )

with col4:
    costo_total = st.number_input(
        "💰 Costo Ultimo",
        min_value=0.0,
        value=0.0,
        step=0.01,
        format="%.2f",
        help="Costo total de la compra (en unidad de moneda)"
    )

# --- CÁLCULO DEL PROMEDIO CON DEPURACIÓN ---
historial = st.session_state.costos_bd

# Debug visual (puedes borrar esto después de probar)
if not historial:
    st.caption("⚠️ No se encontraron compras previas en la base de datos.")
else:
    st.caption(f"✅ Se promediará con {len(historial)} costos históricos encontrados.")

lista_para_promedio = historial + [costo_total] if costo_total > 0 else historial

if lista_para_promedio:
    promedio = sum(lista_para_promedio) / len(lista_para_promedio)
else:
    promedio = 0.0

with col5:
    costo_promedio = st.number_input(
        "💰 Costo promedio",
        min_value=0.0,
        value=float(round(promedio, 2)),
        step=0.01,
        format="%.2f",
        disabled=True,  # Protegemos el campo para que el usuario no lo altere
        help=f"Promedio de {len(lista_para_promedio)} registros encontrados."
    )

st.divider()

# BOTÓN DE ENVÍO (Fuera de un formulario para permitir la reactividad)
submitted = st.button(
    "✅ Registrar Compra",
    use_container_width=True,
    type="primary"
)

# PROCESAR ENVÍO
if submitted:
    errores = []
    
    if not sku_seleccionado:
        errores.append("Debe seleccionar un producto válido.")
    if stock_bodega <= 0:
        errores.append("El stock en bodega debe ser mayor a 0.")
    if costo_total <= 0:
        errores.append("El costo total debe ser mayor a 0.")
    
    if errores:
        for error in errores:
            st.error(f"❌ {error}")
    else:
        # PREPARAR DATOS 
        datos_compra = {
            "sku": sku_seleccionado,
            "nombre": nombre_producto,
            "stock_bodega": int(stock_bodega),
            "costo_total": float(costo_total),
            "usuario": st.session_state.get("usuario_nombre", "usuario")
        }
        
        try:
            with st.spinner("Registrando compra en la base de datos..."):
                response = requests.post(
                    f"{API_BASE_URL}/zeutica/compras", headers=toks,
                    json=datos_compra,
                    timeout=5
                )
            if response.status_code in [200, 201]:
                st.balloons()
                st.success("¡Compra registrada exitosamente!")                
                
            else:
                st.error(f"Error al registrar: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"Error de conexión: {str(e)}")

        try: # Registro en productos del costo promedio
            with st.spinner("Registrando compra en la base de datos..."):
                sku = st.session_state.mi_selector_sku
                response = requests.post(
                    f"{API_BASE_URL}/zeutica/costoPromedio", json={"sku":sku, "costo_prom": costo_promedio}, headers=toks,                    
                    timeout=5
                )
            if response.status_code in [200, 201]:
                st.balloons()
                st.success(response.text)                
                
            else:
                st.error(f"Error al registrar: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"Error de conexión: {str(e)}")

            # Opcional: Limpiar el formulario reiniciando la página
            import time
            time.sleep(2)
            st.rerun() 

# PANEL INFORMATIVO
with st.sidebar:
    st.info(
        "📋 **Guía de uso:**\n"
        "1. Selecciona el producto del catálogo\n"
        "2. El nombre se autocompleta automáticamente\n"
        "3. Ingresa la cantidad en bodega\n"
        "4. Indica el costo total (el promedio se calcula solo)\n"
        "5. Haz clic en 'Registrar Compra'"
    )
