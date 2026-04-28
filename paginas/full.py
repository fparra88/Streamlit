import streamlit as st
import requests
import pandas as pd

API_BASE_URL = st.session_state.ip

toks = {
            "Authorization": f"Bearer {st.session_state.token}"
        }

# --- CONFIGURACIÓN DE URLs (Modifícalas después) ---
URL_GET_PRODUCTOS = f"{API_BASE_URL}/zeutica/productos"
URL_POST_TRASPASO = f"{API_BASE_URL}/zeutica/traspaso"
URL_POST_CLEAN = f"{API_BASE_URL}/zeutica/traspaso/clean"

def obtener_inventario():
    """Obtiene los productos y crea un diccionario para el selectbox"""
    try:
        res = requests.get(URL_GET_PRODUCTOS, headers= toks)
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

URL_DESTINO = {
    "FULL":  URL_POST_TRASPASO,
    "CLEAN": URL_POST_CLEAN,
}

def mostrar_traspasos():
    st.title("🔄 Traspaso Interno de Stock")
    st.markdown("Mueve cantidades de tu stock principal al almacén destino.")

    # Selector de almacén destino — determina el endpoint a usar
    destino = st.radio(
        "Almacén destino:",
        options=["FULL", "CLEAN"],
        horizontal=True,
        key="destino_almacen",
    )

    col_prod, col_lista = st.columns([1, 1])

    # --- 1. COLUMNA: SELECCIÓN DE PRODUCTOS ---
    with col_prod:
        st.markdown("### 1. Seleccionar Producto")
        inventario = obtener_inventario()
        
        # 1. QUITAMOS EL 'with st.form()'
        opciones = list(inventario.keys())
        seleccion = st.selectbox("Buscar Producto:", options=opciones if opciones else ["Cargando..."])
        
        # Variables seguras
        stock_actual = 0
        sku_seleccionado = ""
        desc_seleccionada = ""
        
        if seleccion and inventario:
            producto_data = inventario[seleccion]
            stock_actual = int(producto_data.get('stock_bodega', 0))
            sku_seleccionado = producto_data.get('sku', producto_data.get('id', ''))
            desc_seleccionada = producto_data.get('nombre', '')
            
            st.info(f"📦 Stock disponible para traspaso: **{stock_actual}**")

        # Input de cantidad a mover
        cant_traspaso = st.number_input(
            "Cantidad a traspasar:", 
            min_value=1, 
            # 2. Protección extra por si el stock es 0
            max_value=max(1, stock_actual) if stock_actual > 0 else 1, 
            step=1
        )
        
        # 3. CAMBIAMOS A UN BOTÓN NORMAL
        agregar = st.button("Añadir a la lista ➕", use_container_width=True, type="secondary")
        
        if agregar and inventario:
            if stock_actual <= 0:
                st.error("❌ No hay stock disponible para este producto.")
            elif cant_traspaso > stock_actual:
                st.error("❌ No puedes traspasar más stock del que tienes disponible.")
            else:
                item = {
                    "sku": sku_seleccionado,
                    "descripcion": desc_seleccionada,
                    "stock_bodega": cant_traspaso
                    
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

            if c2.button("🗑️ Limpiar Lista", use_container_width=True):
                st.session_state.lista_traspasos = []
                st.session_state.confirm_traspaso = False
                st.rerun()

            if not st.session_state.get("confirm_traspaso"):
                if c1.button("✅ Confirmar Traspaso", type="primary", use_container_width=True):
                    total_uds = sum(int(i["stock_bodega"]) for i in st.session_state.lista_traspasos)
                    st.session_state.confirm_traspaso = {
                        "destino": destino,
                        "n_items": len(st.session_state.lista_traspasos),
                        "total_uds": total_uds,
                    }
                    st.rerun()
            else:
                ct = st.session_state.confirm_traspaso
                st.warning(
                    f"⚠️ ¿Confirmas traspasar **{ct['n_items']} producto(s)** "
                    f"({ct['total_uds']} uds. en total) al almacén **{ct['destino']}**?"
                )
                col_ok, col_cancel = st.columns(2)
                with col_ok:
                    if st.button("✅ Sí, traspasar", type="primary", use_container_width=True):
                        movimientos = [
                            {**item, "stock_clean": int(item["stock_bodega"])}
                            if ct["destino"] == "CLEAN" else item
                            for item in st.session_state.lista_traspasos
                        ]
                        payload = {
                            "usuario": st.session_state.get("usuario_nombre", "Error"),
                            "movimientos": movimientos,
                            "almacen": ct['destino']
                        }
                        try:
                            with st.spinner("Ejecutando traspaso en base de datos..."):
                                res = requests.post(URL_DESTINO[ct["destino"]], headers=toks, json=payload)
                            if res.status_code == 200:
                                st.session_state.confirm_traspaso = False
                                st.balloons()
                                st.success(f"✅ Traspaso a **{ct['destino']}** completado con éxito.{res.text}")
                                st.session_state.lista_traspasos = []
                                import time
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(f"❌ Error en el servidor: {res.text}")
                                st.session_state.confirm_traspaso = False
                        except Exception as e:
                            st.error(f"⚠️ Falla de conexión: {e}")
                            st.session_state.confirm_traspaso = False
                with col_cancel:
                    if st.button("❌ Cancelar", use_container_width=True):
                        st.session_state.confirm_traspaso = False
                        st.rerun()

# Si llamas este archivo directamente o a través del exec()
mostrar_traspasos()