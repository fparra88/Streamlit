import streamlit as st
import requests
from datetime import datetime
import random
import pandas as pd

API_BASE_URL = "http://10.0.9.227:8090"

# --- FUNCIONES DE DB ---
def obtener_clientes():
    try:
        res_clientes = requests.get(f"{API_BASE_URL}/zeutica/clientes")
        if res_clientes.status_code == 200:
            clientes = res_clientes.json()
            return {f"{item['id']} ({item['nombre']})": item for item in clientes}
    except:
        pass
    return {} # Retorno seguro si falla

def obtener_inventario():
    res_inventario = requests.get(f"{API_BASE_URL}/zeutica/productos")
    inventario = res_inventario.json()
    # Mapeamos los productos por nombre y SKU
    opciones = {f"{item['sku']} ({item['nombre']})": item for item in inventario}
    return opciones

# --- INICIALIZAR MEMORIA ---
if 'carrito_ventas' not in st.session_state:
    st.session_state.carrito_ventas = []
if 'mostrar_formulario_venta' not in st.session_state:
    st.session_state.mostrar_formulario_venta = False

def abrir_formulario():
    st.session_state.mostrar_formulario_venta = True

st.button("Nueva Venta ➕", on_click=abrir_formulario)

if st.session_state.mostrar_formulario_venta:
    with st.expander("📝 Registrar Nueva Venta Múltiple", expanded=True):
        col_prod, col_carrito = st.columns([1, 1])

        # --- 1. SECCIÓN DE AGREGAR PRODUCTOS ---
        with col_prod:
            st.markdown("### 1. Seleccionar Productos")
            opciones_inv = obtener_inventario()
            
            # Usamos un form pequeño SOLO para agregar a la lista
            with st.form("form_agregar_item"):
                seleccion = st.selectbox("Producto:", options=list(opciones_inv.keys()) if opciones_inv else [])
                
                c1, c2 = st.columns(2)
                stock_disp = int(opciones_inv[seleccion].get('cantidad', 0)) if seleccion else 0
                cantidad = c1.number_input("Cantidad:", min_value=1, max_value=max(1, stock_disp), step=1)
                precio = c2.number_input("Precio Venta:", min_value=0.0, format="%.2f")
                
                agregar = st.form_submit_button("Añadir al Carrito 🛒")
                
                if agregar and seleccion:
                    producto_data = opciones_inv[seleccion]
                    item = {
                        "sku": producto_data['sku'],
                        "producto": seleccion,
                        "cantidad": cantidad,
                        "precio_unitario": precio,
                        "total_linea": cantidad * precio
                    }
                    st.session_state.carrito_ventas.append(item)
                    st.rerun()

        # --- 2. SECCIÓN DEL CARRITO Y COBRO ---
        with col_carrito:
            st.markdown("### 2. Registro de venta")
            
            if not st.session_state.carrito_ventas:
                st.info("El carrito está vacío.")
            else:
                # Mostrar Tabla
                df_carrito = pd.DataFrame(st.session_state.carrito_ventas)
                st.dataframe(df_carrito[['sku', 'cantidad', 'precio_unitario', 'total_linea']], use_container_width=True, hide_index=True)
                
                # Totales
                total_venta = sum(item['total_linea'] for item in st.session_state.carrito_ventas)
                st.markdown(f"## **TOTAL: ${total_venta:,.2f}**")
                
                # Datos de Cierre
                diccionario_clientes = obtener_clientes()
                nom_cliente = st.selectbox("Cliente:", list(diccionario_clientes.keys()))
                medio = st.selectbox("Plataforma:", ["Mercado Libre", "Amazon", "Directo", "Local"])
                met_pago = st.text_input("Método de pago (Ej. Tarjeta, Efectivo):")
                
                col_btn1, col_btn2 = st.columns(2)
                confirmar = col_btn1.button("✅ Procesar Venta", type="primary")
                limpiar = col_btn2.button("🗑️ Vaciar Carrito")
                
                if limpiar:
                    st.session_state.carrito_ventas = []
                    st.rerun()

                # --- 3. LÓGICA DE GUARDADO MÚLTIPLE ---
                if confirmar:
                    # Generar ID único de 10 dígitos al azar
                    id_venta_generado = str(random.randint(1000000000, 9999999999))
                    fecha_actual = datetime.now().isoformat()
                    
                    errores = 0
                    with st.spinner("Registrando artículos en AWS..."):
                        # Iteramos sobre cada producto en el carrito
                        for item in st.session_state.carrito_ventas:
                            payload = {
                                "id_venta": id_venta_generado, # <--- El nuevo ID de 10 dígitos
                                "sku": item['sku'],
                                "cantidad": item['cantidad'],
                                "producto": item['producto'],
                                "fecha": fecha_actual,
                                "nombreComprador": nom_cliente,
                                "otros": met_pago,
                                "plataforma": medio
                            }
                            
                            # Enviamos uno por uno a la base de datos
                            res = requests.post(f"{API_BASE_URL}/zeutica/producto/venta", json=payload)
                            if res.status_code != 200:
                                errores += 1
                                st.error(f"Fallo al guardar: {item['sku']}")

                    if errores == 0:
                        st.success(f"✅ Venta {id_venta_generado} registrada con éxito.")
                        st.balloons()
                        st.session_state.carrito_ventas = [] # Limpiamos memoria
                        st.session_state.mostrar_formulario_venta = False
                        st.rerun()