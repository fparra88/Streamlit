import streamlit as st
import requests
from datetime import datetime

# Configuración de la API
API_BASE_URL = st.session_state.ip

toks = {
            "Authorization": f"Bearer {st.session_state.token}"
        }

st.title("📦 Registrar Compra")
st.divider()

# ============================================================================
# FUNCIÓN PARA OBTENER PRODUCTOS DE LA API
# ============================================================================
@st.cache_data(ttl=300)  # Cache de 5 minutos
def obtener_productos():
    """
    Obtiene la lista de productos de la API y los mapea por SKU.
    
    Returns:
        dict: Diccionario con estructura {sku: {sku, nombre, ...}} o {}
        list: Lista de tuplas (sku, nombre) para el selectbox
    """
    try:
        with st.spinner("Cargando productos..."):
            response = requests.get(f"{API_BASE_URL}/zeutica/productos", headers= toks ,timeout=5)
        
        if response.status_code == 200:
            productos = response.json()
            
            # Mapeo: {sku: {datos completos del producto}}
            productos_dict = {prod['sku']: prod for prod in productos}
            
            # Lista para selectbox: [(sku, nombre), ...]
            opciones = [(prod['sku'], f"{prod['sku']} - {prod.get('nombre', 'Sin nombre')}") 
                        for prod in productos]
            
            return productos_dict, opciones
        else:
            st.error(f"Error al obtener productos: Código {response.status_code}")
            return {}, []
            
    except requests.exceptions.Timeout:
        st.error("Timeout: El servidor tardó demasiado en responder.")
        return {}, []
    except requests.exceptions.ConnectionError:
        st.error("Error de conexión: No se puede conectar con el servidor.")
        return {}, []
    except Exception as e:
        st.error(f"Error inesperado: {str(e)}")
        return {}, []

# ============================================================================
# CARGAR PRODUCTOS
# ============================================================================
productos_dict, opciones_productos = obtener_productos()

if not opciones_productos:
    st.info("No hay productos disponibles o hay un problema de conexión.")
    st.stop()

# ============================================================================
# FORMULARIO DE COMPRA
# ============================================================================
with st.form("formulario_compra", clear_on_submit=True):
    st.subheader("Detalles de la Compra")
    
    # SELECTBOX: SKU del producto
    col1, col2 = st.columns([1, 2])
    with col1:
        sku_seleccionado = st.selectbox(
            "🔍 Selecciona Producto (SKU)",
            options=[opt[0] for opt in opciones_productos],
            format_func=lambda x: next((opt[1] for opt in opciones_productos if opt[0] == x), x),
            help="Selecciona el SKU del producto que estás comprando"
        )
    
    # Obtener datos del producto seleccionado
    producto_seleccionado = productos_dict.get(sku_seleccionado, {})
    nombre_producto = producto_seleccionado.get('nombre', 'Sin nombre')
    
    # CAMPO: Nombre del producto (solo lectura)
    with col2:
        st.text_input(
            "📝 Nombre del Producto",
            value=nombre_producto,
            disabled=True,
            help="Campo auto-completado según el SKU seleccionado"
        )
    
    st.divider()
    
    # CAMPOS NUMÉRICOS
    col3, col4 = st.columns(2)
    
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
    
    st.divider()
    
    # BOTÓN DE ENVÍO
    submitted = st.form_submit_button(
        "✅ Registrar Compra",
        use_container_width=True,
        type="primary"
    )
    
    # PROCESAR ENVÍO DEL FORMULARIO
    if submitted:
        # Validaciones
        errores = []
        
        if not sku_seleccionado:
            errores.append("Debe seleccionar un producto válido.")
        if stock_bodega <= 0:
            errores.append("El stock en bodega debe ser mayor a 0.")
        if costo_total <= 0:
            errores.append("El costo total debe ser mayor a 0.")
        
        # Mostrar errores si existen
        if errores:
            for error in errores:
                st.error(f"❌ {error}")
        else:
            # PREPARAR DATOS SEGÚN CompraModel
            datos_compra = {
                "sku": sku_seleccionado,
                "nombre": nombre_producto,
                "stock_bodega": int(stock_bodega),
                "costo_total": float(costo_total),
                "usuario": st.session_state.usuario_nombre
            }
            
            # MOSTRAR DATOS A ENVIAR
            st.success("✅ Datos validados correctamente!")
            st.info("📤 Datos a registrar:")
            st.json(datos_compra)
            
            # TODO: ENVIAR A LA API (descomenta cuando el endpoint esté listo)
            try:
                response = requests.post(
                    f"{API_BASE_URL}/zeutica/compras", headers= toks,
                    json=datos_compra,
                    timeout=5
                )
                if response.status_code in [200, 201]:
                    st.balloons()
                    st.success("¡Compra registrada exitosamente!")
                    st.write(response)
                else:
                    st.error(f"Error al registrar: {response.status_code}")
            except Exception as e:
                st.error(f"Error de conexión: {str(e)}")

# ============================================================================
# PANEL INFORMATIVO
# ============================================================================
with st.sidebar:
    st.info(
        "📋 **Guía de uso:**\n"
        "1. Selecciona el producto del catálogo\n"
        "2. El nombre se autocompleta automáticamente\n"
        "3. Ingresa la cantidad en bodega\n"
        "4. Indica el costo total\n"
        "5. Haz clic en 'Registrar Compra'"
    )
