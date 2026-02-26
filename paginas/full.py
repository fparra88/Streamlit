import streamlit as st
import requests
import pandas as pd

# --- CONFIGURACIÓN DE URLs (Modifícalas después) ---
URL_GET_PRODUCTOS = "http://10.0.9.227:8090/zeutica/productos"
URL_POST_TRASPASO = "http://10.0.9.227:8090/traspaso"

def obtener_inventario():
    """Obtiene los productos y crea un diccionario para el selectbox"""
    try:
        res = requests.get(URL_GET_PRODUCTOS)
        if res.status_code == 200:
            productos = res.json()
            # Creamos la llave visual: "SKU - Descripción (Stock: X)"
            return {
                f"{p.get('sku', p.get('id'))} - {p.get('nombre', 'Sin nombre')}": p 
                for p in productos
            }
    except Exception as e:
        st.error(f"Error al conectar con la API: {e}")
    return {}

# --- INICIALIZAR MEMORIA ---
if 'lista_traspasos' not in st.session_state:
    st.session_state.lista_traspasos = []

def mostrar_traspasos():
    st.title("🔄 Traspaso Interno de Stock a FULL")
    st.markdown("Mueve cantidades de tu stock principal a FULL MELI.")

    col_prod, col_lista = st.columns([1, 1])

    # --- 1. COLUMNA: SELECCIÓN DE PRODUCTOS ---
    with col_prod:
        st.markdown("### 1. Seleccionar Producto")
        inventario = obtener_inventario()
        
        with st.form("form_traspaso"):
            opciones = list(inventario.keys())
            seleccion = st.selectbox("Buscar Producto:", options=opciones if opciones else ["Cargando..."])
            
            # Variables seguras
            stock_actual = 0
            sku_seleccionado = ""
            desc_seleccionada = ""
            
            if seleccion and inventario:
                producto_data = inventario[seleccion]
                stock_actual = int(producto_data.get('cantidad', 0))
                sku_seleccionado = producto_data.get('sku', producto_data.get('id', ''))
                desc_seleccionada = producto_data.get('nombre', '')
                
                st.info(f"📦 Stock disponible para traspaso: **{stock_actual}**")

            # Input de cantidad a mover
            cant_traspaso = st.number_input(
                "Cantidad a traspasar:", 
                min_value=1, 
                max_value=max(1, stock_actual), # Evita que traspase más de lo que hay
                step=1
            )
            
            agregar = st.form_submit_button("Añadir a la lista ➕")
            
            if agregar and inventario:
                if cant_traspaso > stock_actual:
                    st.error("❌ No puedes traspasar más stock del que tienes disponible.")
                else:
                    item = {
                        "sku": sku_seleccionado,
                        "descripcion": desc_seleccionada,
                        "cantidad": cant_traspaso
                    }
                    st.session_state.lista_traspasos.append(item)
                    st.rerun()

    # --- 2. COLUMNA: LISTA DE TRASPASOS Y EJECUCIÓN ---
    with col_lista:
        st.markdown("### 2. Resumen de Traspasos")
        
        if not st.session_state.lista_traspasos:
            st.info("Aún no hay productos seleccionados para traspaso.")
        else:
            # Mostrar la tabla visual
            df = pd.DataFrame(st.session_state.lista_traspasos)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Opciones de ejecución
            c1, c2 = st.columns(2)
            
            if c1.button("✅ Confirmar Traspaso", type="primary", use_container_width=True):
                # Preparamos el JSON para la API
                payload = {
                    "usuario": st.session_state.get("usuario_nombre", "Admin"),
                    "movimientos": st.session_state.lista_traspasos
                }
                
                try:
                    with st.spinner("Ejecutando traspaso en base de datos..."):
                        res = requests.post(URL_POST_TRASPASO, json=payload)
                    
                        if res.status_code == 200:
                            st.success("✅ Traspaso completado con éxito.")
                            st.session_state.lista_traspasos = [] # Limpiamos memoria
                            st.rerun()
                        else:
                            st.error(f"❌ Error en el servidor: {res.text}")
                except Exception as e:
                    st.error(f"⚠️ Falla de conexión: {e}")
            
            if c2.button("🗑️ Limpiar Lista", use_container_width=True):
                st.session_state.lista_traspasos = []
                st.rerun()

# Si llamas este archivo directamente o a través del exec()
mostrar_traspasos()