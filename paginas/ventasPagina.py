import streamlit as st
import requests
from datetime import datetime
import random
import pandas as pd

API_BASE_URL = st.session_state.ip

toks = {
            "Authorization": f"Bearer {st.session_state.token}"
        }

# --- FUNCIONES DE DB ---
def obtener_clientes():
    try:
        res_clientes = requests.get(f"{API_BASE_URL}/zeutica/clientes", headers= toks)
        if res_clientes.status_code == 200:
            clientes = res_clientes.json()
            return {f"{item['id']} ({item['nombre']})": item for item in clientes}
    except:
        pass
    return {} # Retorno seguro si falla

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

def obtener_cotizaciones():
    """Obtiene las cotizaciones existentes del API"""
    try:
        res_cotizaciones = requests.get(f"{API_BASE_URL}/zeutica/consulta/cotizacion", headers= toks)
        if res_cotizaciones.status_code == 200:
            data = res_cotizaciones.json()
            
            # Extraer la lista de cotizaciones desde la clave "cotizaciones"
            cotizaciones = data.get('cotizaciones', [])
            
            if not isinstance(cotizaciones, list):
                st.error(f"Error: se esperaba una lista de cotizaciones")
                return {}
            
            # Mapeamos cotizaciones por ID y Cliente para el selectbox
            opciones = {}
            for item in cotizaciones:
                if isinstance(item, dict):
                    subtotal = float(item.get('subtotal', 0)) if item.get('subtotal') else 0.0
                    etiqueta = f"ID: {item.get('codigo_cotizacion')} - Cliente: {item.get('empresa', 'N/A')} (${subtotal:.2f})"
                    opciones[etiqueta] = item
            
            return opciones
    except Exception as e:
        st.error(f"Error al obtener cotizaciones: {str(e)}")
    return {}

def obtener_items_cotizacion(cotizacion_id):
    """Obtiene los items de una cotización específica"""
    try:
        res_items = requests.get(f"{API_BASE_URL}/zeutica/cotizacion/{cotizacion_id}", headers= toks)
        if res_items.status_code == 200:
            data = res_items.json()
            
            # Si devuelve un diccionario
            if isinstance(data, dict):
                # Caso A: Viene dentro de una clave 'items'
                if 'items' in data:
                    return data.get('items', [])
                # Caso B: El diccionario ES el item directamente (como en tu imagen)
                elif 'sku' in data:
                    return [data] # Lo metemos en una lista para iterarlo
                else:
                    st.error("Estructura de diccionario no reconocida por el sistema.")
                    return []
            
            # Si devuelve directamente una lista de diccionarios
            elif isinstance(data, list):
                return data
                
    except Exception as e:
        st.error(f"Error al obtener items de la cotización: {str(e)}")
    return []


if __name__ == "__main__":
    def cargar_cotizacion_al_carrito(cotizacion):
        """Carga los items de una cotización al carrito"""
        # Extraer el ID de la cotización (puede ser 'id' o 'codigo_cotizacion')
        cotizacion_id = cotizacion.get('id') or cotizacion.get('codigo_cotizacion')

        if not cotizacion_id:
            st.error("❌ No se pudo obtener el ID de la cotización")
            return False

        # Obtenemos los items del endpoint separado
        items = obtener_items_cotizacion(cotizacion_id)

        if not items:
            st.warning("⚠️ La cotización no tiene items asociados.")
            return False

        for item in items:
            cart_item = {
                "sku": item.get('sku', 'N/A'),
                # Se añade 'nombre_producto' basado en la respuesta de tu API
                "producto": item.get('nombre_producto', item.get('producto', 'Producto sin nombre')),
                "cantidad": int(item.get('cantidad', 0)),
                "precio_unitario": float(item.get('precio_unitario', 0)),
                "total_linea": float(item.get('total_linea', 0))
            }
            st.session_state.carrito_ventas.append(cart_item)

        return True

    # --- INICIALIZAR MEMORIA ---
    if 'carrito_ventas' not in st.session_state:
        st.session_state.carrito_ventas = []
    if 'descuento_venta' not in st.session_state:
        st.session_state.descuento_venta = 0.0

    # --- SECCIÓN: CARGAR COTIZACIONES EXISTENTES ---
    with st.expander("📋 Cargar Cotización Existente", expanded=False):
        st.markdown("#### Selecciona una cotización para cargar sus artículos al carrito:")

        cotizaciones_dict = obtener_cotizaciones()

        if cotizaciones_dict:
            cotizacion_seleccionada = st.selectbox(
                "Cotizaciones disponibles:",
                options=list(cotizaciones_dict.keys()),
                key="select_cotizacion"
            )

            col_cargar, col_recargar = st.columns(2)

            if col_cargar.button("Cargar Cotización al Carrito", type="primary", use_container_width=True):
                cotizacion_data = cotizaciones_dict[cotizacion_seleccionada]
                if cargar_cotizacion_al_carrito(cotizacion_data):
                    st.success(f"Cotización cargada con {len(cotizacion_data.get('items', []))} artículos.", icon="✅")
                    st.rerun()

            if col_recargar.button("🔄 Recargar Cotizaciones", use_container_width=True):
                st.rerun()
        else:
            st.info("📭 No hay cotizaciones disponibles.")

    with st.expander("📝 Registrar Nueva Venta Múltiple", expanded=True):
        col_prod, col_carrito = st.columns([1, 1])

        # --- 1. SECCIÓN DE AGREGAR PRODUCTOS ---
        with col_prod:
            st.markdown("### 1. Seleccionar Productos")
            opciones_inv = obtener_inventario()

            # 1. QUITAMOS el form para que la pantalla sea interactiva y reactiva
            seleccion = st.selectbox("Producto:", options=list(opciones_inv.keys()) if opciones_inv else [])

            if seleccion and opciones_inv:
                producto_data = opciones_inv[seleccion]

                stock_disp = int(producto_data.get('stock_bodega', 0))

                # 2. Extraemos los 3 precios de la base de datos
                precio = float(producto_data.get('precio') or 0.0)
                precio_2 = float(producto_data.get('precio_2') or 0.0)
                precio_3 = float(producto_data.get('precio_3') or 0.0)
                precio_amazon = float(producto_data.get('precio_amazon') or 0.0)

                # 3. Selector visual de Lista de Precios
                st.write("Selecciona Lista de Precios:")
                tipo_precio = st.radio(
                    "Oculto", # Etiqueta oculta
                    options=["Precio A", "Precio B", "Precio C", "Precio Amazon"],
                    horizontal=True,
                    label_visibility="collapsed"
                )

                # Asignamos el valor en tiempo real dependiendo del botón seleccionado
                if tipo_precio == "Precio A":
                    precio_sugerido = precio
                elif tipo_precio == "Precio B":
                    precio_sugerido = precio_2
                elif tipo_precio == "Precio C":
                    precio_sugerido = precio_3
                else:
                    precio_sugerido = precio_amazon

                c1, c2 = st.columns(2)

                # Límite de cantidad protegido por el stock real
                cantidad = c1.number_input(
                    "Cantidad:",
                    min_value=1,
                    max_value=max(1, stock_disp) if stock_disp > 0 else 1,
                    step=1
                )

                # 4. El input de precio ahora toma el valor sugerido automáticamente (pero permite editarlo manualmente si es necesario)
                precio = c2.number_input(
                    "Precio a aplicar:",
                    min_value=0.0,
                    value=float(precio_sugerido),
                    format="%.2f"
                )

                # 5. Botón normal (fuera de formulario)
                agregar = st.button("Añadir al Carrito 🛒", use_container_width=True, type="secondary")

                if agregar:
                    if stock_disp <= 0:
                        st.error("❌ Producto sin stock disponible.")
                    elif cantidad > stock_disp:
                        st.error("❌ La cantidad solicitada supera el inventario.")
                    else:
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
                # Mostrar Tabla con opciones de edición
                df_carrito = pd.DataFrame(st.session_state.carrito_ventas)
                st.dataframe(df_carrito[['sku', 'cantidad', 'precio_unitario', 'total_linea']], use_container_width=True, hide_index=True)

                # Opciones para editar/eliminar productos del carrito
                st.markdown("#### Gestionar productos del carrito:")
                idx_producto = st.number_input(
                    "Índice del producto (0 es el primer producto):",
                    min_value=0,
                    max_value=max(0, len(st.session_state.carrito_ventas) - 1),
                    step=1,
                    key="idx_carrito"
                )

                # Mostrar detalles del producto seleccionado
                if 0 <= idx_producto < len(st.session_state.carrito_ventas):
                    producto_actual = st.session_state.carrito_ventas[idx_producto]
                    st.info(f"🛒 **{producto_actual['sku']}** | Cantidad: {producto_actual['cantidad']} | Precio: ${producto_actual['precio_unitario']:.2f}")

                    # Input para nueva cantidad (SIEMPRE VISIBLE)
                    nueva_cantidad = st.number_input(
                        "Nueva cantidad:",
                        min_value=1,
                        value=producto_actual['cantidad'],
                        step=1,
                        key=f"qty_{idx_producto}"
                    )

                col_edit1, col_edit2, col_edit3 = st.columns(3)

                if col_edit1.button("❌ Eliminar Producto", use_container_width=True):
                    if 0 <= idx_producto < len(st.session_state.carrito_ventas):
                        st.session_state.carrito_ventas.pop(idx_producto)
                        st.rerun()

                if col_edit2.button("✏️ Guardar Cambios", use_container_width=True, type="primary"):
                    if 0 <= idx_producto < len(st.session_state.carrito_ventas):
                        st.session_state.carrito_ventas[idx_producto]['cantidad'] = nueva_cantidad
                        st.session_state.carrito_ventas[idx_producto]['total_linea'] = nueva_cantidad * st.session_state.carrito_ventas[idx_producto]['precio_unitario']
                        st.success("✅ Cantidad actualizada!")
                        st.rerun()

                if col_edit3.button("🔄 Recargar", use_container_width=True):
                    st.rerun()

                # Totales
                total_venta = sum(item['total_linea'] for item in st.session_state.carrito_ventas)

                # Sección de Descuento
                st.markdown("#### Aplicar Descuento:")
                descuento_pct = st.number_input(
                    "Porcentaje de Descuento (%):",
                    min_value=0.0,
                    max_value=100.0,
                    value=st.session_state.descuento_venta,
                    step=0.1,
                    key="descuento_input_venta"
                )
                st.session_state.descuento_venta = descuento_pct

                # Calcular total con descuento
                monto_descuento = total_venta * (descuento_pct / 100)
                iva = 1.16
                total_con_descuento = (total_venta - monto_descuento) * iva
                iva_solo = total_venta * 0.16

                # Mostrar desglose
                col_desc1, col_desc2, col_des3 = st.columns(3)
                col_desc1.metric("Subtotal:", f"${total_venta:,.2f}")
                col_desc2.metric(f"Descuento ({descuento_pct}%):", f"-${monto_descuento:,.2f}")
                col_des3.metric(f"Iva:", f"${float(iva_solo):,.2f}")
                st.markdown(f"## **TOTAL: ${total_con_descuento:,.2f}**")

                # Datos de Cierre
                diccionario_clientes = obtener_clientes()
                nom_cliente = st.selectbox("Cliente:", list(diccionario_clientes.keys()))
                medio = st.selectbox("Plataforma:", ["Mercado Libre", "Amazon", "Directo", "Local"])
                met_pago = st.text_input("Método de pago (Ej. Tarjeta, Efectivo):", value="CONTADO")

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
                            # Aplicar descuento al precio unitario
                            precio_con_descuento = item['precio_unitario'] * (1 - (descuento_pct / 100))

                            payload = {
                                "id_venta": id_venta_generado, # <--- El nuevo ID de 10 dígitos
                                "sku": item['sku'],
                                "stock_bodega": item['cantidad'],
                                "precio": round(precio_con_descuento, 2),
                                "producto": item['producto'],
                                "fecha": fecha_actual,
                                "nombreComprador": nom_cliente,
                                "otros": met_pago,
                                "plataforma": medio,
                                "usuario": st.session_state.usuario_nombre
                            }

                            # Enviamos uno por uno a la base de datos
                            res = requests.post(f"{API_BASE_URL}/zeutica/producto/venta", headers=toks, json=payload)
                            if res.status_code != 200:
                                errores += 1
                                st.error(f"Fallo al guardar: {item['sku']}")

                    if errores == 0:
                        st.balloons()
                        st.success(f"✅ Venta {id_venta_generado} registrada con éxito.", icon='🎉')

                        st.session_state.carrito_ventas = [] # Limpiamos memoria
                        import time
                        time.sleep(2)
                        st.rerun()