import streamlit as st
import requests
from datetime import datetime
import time

# 1. Validación de seguridad (Evita crasheos si recargan la página)
if "token" not in st.session_state or "ip" not in st.session_state:
    st.error("⚠️ No hay sesión activa. Por favor, inicia sesión.")
    st.stop() # Detiene la ejecución de esta página si no hay token

API_BASE_URL = st.session_state.ip

# Armamos el header correctamente
toks = {
    "Authorization": f"Bearer {st.session_state.get('token')}"
}

def obtener_inventario():
    try: 
        # Asegúrate de que API_BASE_URL y toks sean los correctos para producción
        res = requests.get(f"{API_BASE_URL}/zeutica/productos", headers=toks, timeout=5)
        
        if res.status_code == 200:
            datos = res.json()
            
            # VALIDACIÓN CRÍTICA: Solo procesamos si es una lista
            if isinstance(datos, list):
                return {f"{item['sku']} ({item.get('nombre', 'S/N')})": item for item in datos}
            else:
                st.error("⚠️ La API de producción no devolvió una lista de productos.")
                return {}
        else:
            # En producción, esto te dirá si es un error 401 (Token), 404, etc.
            st.error(f"❌ Error en API Producción: {res.status_code} - {res.text}")
            return {}
        
    except Exception as e:
        st.error(f"📡 Fallo de conexión en producción: {e}")
        return {}

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
    st.session_state.gasto_pendiente = {
        "descripcion": descripcion,
        "costo": costo,
        "cantidad": cantidad,
    }

if st.session_state.get("gasto_pendiente"):
    p = st.session_state.gasto_pendiente
    st.warning(
        f"⚠️ ¿Confirmas registrar el gasto **{p['descripcion']}** por **${p['costo']}**?"
    )
    col_ok, col_cancel = st.columns(2)
    with col_ok:
        if st.button("✅ Sí, registrar", type="primary", use_container_width=True, key="btn_ok_gasto"):
            payload = {
                "usuario_registro": st.session_state.get("usuario_nombre", "usuario"),
                "descripcion": p["descripcion"],
                "costo": p["costo"],
                "cantidad": p["cantidad"],
            }
            try:
                with st.spinner("Enviando datos al servidor en AWS..."):
                    res = requests.post(f"{API_BASE_URL}/zeutica/gastos", headers=toks, json=payload)
                if res.status_code == 200:
                    st.session_state.gasto_pendiente = None
                    st.success("✅ Registro aceptado")
                else:
                    st.error(f"❌ Error del servidor: {res.status_code} - {res.text}")
                    st.session_state.gasto_pendiente = None
            except Exception as e:
                st.error(f"❌ Error de conexion: {e}")
                st.session_state.gasto_pendiente = None
    with col_cancel:
        if st.button("❌ Cancelar", use_container_width=True, key="btn_cancel_gasto"):
            st.session_state.gasto_pendiente = None
            st.rerun()

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
    sku_submitted = st.form_submit_button("Ingresar", use_container_width=True, type="primary")

if sku_submitted:
    if seleccion and sku_input:
        producto_data = sku_input[seleccion]
        st.session_state.sku_gasto_pendiente = {
            "sku": producto_data.get('sku', ''),
            "nombre": producto_data.get('nombre', 'Sin nombre'),
            "cantidad": cantidad,
            "fecha_actual": fecha_actual,
        }
    else:
        st.warning("⚠️ No se seleccionó un producto válido.")

if st.session_state.get("sku_gasto_pendiente"):
    p = st.session_state.sku_gasto_pendiente
    st.warning(
        f"⚠️ ¿Confirmas registrar **{p['cantidad']} uds.** de "
        f"**{p['nombre']}** como gasto operativo de bodega?"
    )
    col_ok2, col_cancel2 = st.columns(2)
    with col_ok2:
        if st.button("✅ Sí, registrar", type="primary", use_container_width=True, key="btn_ok_sku_gasto"):
            payload = {
                "id_venta": 0,
                "sku": p["sku"],
                "stock_bodega": p["cantidad"],
                "precio": 0.00,
                "producto": p["nombre"],
                "fecha": p["fecha_actual"],
                "nombreComprador": "USO DE BODEGA",
                "otros": "ESTE ARTICULO FUE USADO EN ALMACEN",
                "plataforma": "BODEGA",
                "usuario": st.session_state.usuario_nombre,
            }
            try:
                res = requests.post(f"{API_BASE_URL}/zeutica/producto/venta", headers=toks, json=payload)
                if res.status_code == 200:
                    st.session_state.sku_gasto_pendiente = None
                    st.success("✅ Gasto registrado correctamente")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"❌ Fallo al guardar: Código {res.status_code} - {res.text}")
                    st.session_state.sku_gasto_pendiente = None
            except Exception as e:
                st.error(f"❌ Excepción al guardar: {e}")
                st.session_state.sku_gasto_pendiente = None
    with col_cancel2:
        if st.button("❌ Cancelar", use_container_width=True, key="btn_cancel_sku_gasto"):
            st.session_state.sku_gasto_pendiente = None
            st.rerun()

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