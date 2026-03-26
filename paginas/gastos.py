import streamlit as st
import requests
from paginas.ventasPagina import obtener_inventario
from datetime import datetime

# 1. Validación de seguridad (Evita crasheos si recargan la página)
if "token" not in st.session_state or "ip" not in st.session_state:
    st.error("⚠️ No hay sesión activa. Por favor, inicia sesión.")
    st.stop() # Detiene la ejecución de esta página si no hay token

API_BASE_URL = st.session_state.ip

# Armamos el header correctamente
toks = {
    "Authorization": f"Bearer {st.session_state.get('token')}"
}

st.header("Plataforma de registro de gastos Operativos")
st.info("Ingresa los gastos realizados para la operacion")

# --- FORMULARIO 1: GASTOS ---
with st.form("Registro de Ventas"):
    col1, col2 = st.columns(2)

    with col1:
        descripcion = st.text_input("Ingresa la descripcion del gasto")
        costo = st.text_input("Ingresa el monto del gasto")

    with col2:
        cantidad = st.text_input("Ingresa la cantidad de piezas")

    envio_datos = st.form_submit_button("Registra el gasto")

if envio_datos:
    payload = {
        "usuario_registro": st.session_state.get("usuario_nombre", "usuario"),
        "descripcion": descripcion,
        "costo": costo,
        "cantidad": cantidad
    }
    try:
        with st.spinner("Enviando datos al servidor en AWS..."):
            res = requests.post(f"{API_BASE_URL}/zeutica/gastos", headers=toks, json=payload)
            
        if res.status_code == 200:
            st.success("✅ Registro aceptado")
        else:
            # AHORA SÍ VERÁS POR QUÉ FALLA SI NO ES 200
            st.error(f"❌ Error del servidor: {res.status_code} - {res.text}") 
    except Exception as e:
        st.error(f"❌ Error de conexion: {e}")

st.divider()
st.subheader("Ingresa SKU como gasto OPERATIVO.")

# --- FORMULARIO 2: REGISTRO DE SKU ---
with st.form("Registro de SKU"):
    col1, col2 = st.columns(2)
    with col1:
        sku_input = obtener_inventario() 
        
        # Validamos que haya inventario antes de llenar el selectbox
        opciones_validas = list(sku_input.keys()) if sku_input else []
        seleccion = st.selectbox("Selecciona el sku", options=opciones_validas)

    with col2:
        cantidad = st.number_input("Ingresa la cantidad a descontar", min_value=1)
        fecha_actual = datetime.now().isoformat()

    # Botón dentro del form
    if st.form_submit_button("Ingresar", use_container_width=True, type="primary"):
        
        # Validación extra: Asegurarnos de que seleccionó algo
        if seleccion and sku_input:
            # CORRECCIÓN VITAL: Extraemos el diccionario real del producto
            producto_data = sku_input[seleccion]
            
            payload = {
                "id_venta": 0,
                "sku": producto_data.get('sku', ''), # Sacamos el SKU real
                "stock_bodega": cantidad,
                "precio": 0.00,
                "producto": producto_data.get('nombre', 'Sin nombre'), # Sacamos el nombre real
                "fecha": fecha_actual,
                "nombreComprador": "USO DE BODEGA",
                "otros": "ESTE ARTICULO FUE USADO EN ALMACEN",
                "plataforma": "BODEGA"
            }
            
            # CORRECCIÓN DE INDENTACIÓN: El try ahora está DENTRO del botón
            try:
                res = requests.post(f"{API_BASE_URL}/zeutica/producto/venta", headers=toks, json=payload)
                
                if res.status_code == 200:
                    st.success("✅ Gasto registrado correctamente")
                else:
                    st.error(f"❌ Fallo al guardar: Código {res.status_code} - {res.text}")
            except Exception as e:
                st.error(f"❌ Excepción al guardar: {e}")
        else:
            st.warning("⚠️ No se seleccionó un producto válido.")

# --- SECCIÓN DE CONSULTA ---
st.divider()
st.subheader("Consulta de Gastos Registrados")

if st.button("Consultar Gastos", key="btn_consulta_gastos"):
    payload_consulta = {
        "usuario": st.session_state.get("usuario_nombre", "usuario")
    }
    try:
        with st.spinner("Consultando gastos..."):
            res = requests.get(f"{API_BASE_URL}/zeutica/consultagastos", headers=toks, params=payload_consulta)
        
        if res.status_code == 200:
            st.success("✅ Consulta realizada exitosamente")
            datos = res.json()  
            st.dataframe(datos, use_container_width=True)
        else:
            st.error(f"❌ Error en la consulta: Código {res.status_code}")
            st.warning(res.text)
            
    except requests.exceptions.Timeout:
        st.error("❌ Tiempo de espera agotado. El servidor tardó demasiado en responder.")
    except requests.exceptions.ConnectionError:
        st.error("❌ Error de conexión. No se pudo conectar con el servidor.")
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error en la petición: {str(e)}")
    except Exception as e:
        st.error(f"❌ Error inesperado: {str(e)}")