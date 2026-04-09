import streamlit as st
import requests
from datetime import datetime
import random

API_BASE_URL = st.session_state.ip

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

def obtener_pedidos():
    try:
        res = requests.get(f"{API_BASE_URL}/zeutica/cleanest", headers=toks)
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return []

def actualizar_pedido(pedido_id, payload):
    try:
        res = requests.patch(f"{API_BASE_URL}/zeutica/cleanest/{pedido_id}", headers=toks, json=payload)
        return res.status_code == 200
    except:
        return False

def mostrar_firma(norden_v, uid):
    """Muestra un botón toggle; solo consulta y renderiza la firma si el usuario lo activa.
    uid debe ser el id único del pedido en DB para evitar colisión de keys cuando hay
    múltiples órdenes con el mismo numero_orden."""
    import base64
    from PIL import Image
    import io

    # Usamos uid (id de DB) como discriminador de clave, no norden_v, que puede repetirse
    key_toggle = f"ver_firma_{uid}"
    if key_toggle not in st.session_state:
        st.session_state[key_toggle] = False

    label = "🔒 Ocultar Firma" if st.session_state[key_toggle] else "🖊️ Ver Firma Registrada"
    if st.button(label, key=f"btn_ver_firma_{uid}", use_container_width=True):
        st.session_state[key_toggle] = not st.session_state[key_toggle]

    if st.session_state[key_toggle]:
        try:
            res = requests.get(
                f"{API_BASE_URL}/zeutica/obtener-firma",
                headers=toks,
                params={"numero_orden": norden_v},  # norden_v se usa solo para la API, no como key
                timeout=5,
            )
            if res.status_code == 200:
                data = res.json()
                img_b64 = data.get("firma_base64") or data.get("firma_digital")
                fecha = data.get("fecha_firma")
                if img_b64:
                    img_bytes = base64.b64decode(img_b64)
                    img = Image.open(io.BytesIO(img_bytes))
                    st.image(img, caption=f"Firma — Orden {norden_v} con fecha {fecha}", use_container_width=False, width=350)
                else:
                    st.caption("Sin firma registrada aún.")
            elif res.status_code == 404:
                st.caption("Sin firma registrada aún.")
            else:
                st.caption(f"No se pudo obtener la firma ({res.status_code}).")
        except Exception as e:
            st.caption(f"Error al cargar firma: {e}")


@st.dialog("✍️ Firma Digital")
def _modal_firma(pid, norden_v):
    """Canvas dentro de modal; convierte a base64 y envía a /zeutica/efirma"""
    from streamlit_drawable_canvas import st_canvas
    import base64
    import io
    from PIL import Image
    from datetime import datetime

    st.caption(f"Orden: **{norden_v}** — Dibuja la firma en el recuadro:")

    canvas_result = st_canvas(
        fill_color="rgba(255,255,255,0)",
        stroke_width=2,
        stroke_color="#000000",
        background_color="#FFFFFF",
        height=150,
        width=500,
        drawing_mode="freedraw",
        display_toolbar=True,
        key=f"canvas_{pid}",
    )

    if st.button("📤 Enviar Firma", type="primary", use_container_width=True):
        if canvas_result.image_data is None:
            st.warning("El lienzo está vacío. Dibuja la firma antes de enviar.")
            return

        # Convertir numpy array → PNG → base64
        img = Image.fromarray(canvas_result.image_data.astype("uint8"), mode="RGBA")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        payload = {
            "numero_orden": norden_v,
            "firma_base64": img_b64,
            "usuario": st.session_state.get("usuario_nombre", "sistema"),
            "fecha_firma": datetime.now().isoformat(),
        }

        try:
            res = requests.post(f"{API_BASE_URL}/zeutica/efirma", headers=toks, json=payload)
            if res.status_code in (200, 201):
                st.success("✅ Firma enviada correctamente.")
                st.rerun()
            else:
                st.error(f"Error al enviar firma: {res.status_code} — {res.text}")
        except Exception as e:
            st.error(f"Error de conexión: {e}")


def firma_digital(pid, norden_v):
    """Botón que abre el modal de firma digital."""
    st.markdown("---")
    if st.button("✍️ Firma Digital", key=f"btn_firma_{pid}", use_container_width=True):
        _modal_firma(pid, norden_v)

def cleanest():
    st.title("CLEANEST CHOICE")

    tab_nueva, tab_tracking, tab_historial = st.tabs(["Nueva Orden de Pedido", "Tracking de Pedidos", "Historial"])

    # ─────────────────────────────────────────
    # TAB 1: NUEVA ORDEN
    # ─────────────────────────────────────────
    with tab_nueva:
        st.markdown("### Ingresa los datos de la Orden de Pedido")

        with st.form("formulario_cleanest", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                norden = st.text_input("Número de Orden", value="OC")
                skus_permitidos = ["ESPFARBLA", "CUBBCADLD", "TAPCUABLA24","UNIAZLCH", "UNIAZLXL", "UNIAZLMED", "UNIAZLGDE", "UNIAZL2XL", "UNIAZLXXL"]
                sku_input = obtener_inventario()
                # Las claves del dict tienen formato "SKU (nombre)", por eso comparamos contra item['sku']
                opciones_validas = [key for key, item in sku_input.items() if item.get("sku") in skus_permitidos] if sku_input else []
                seleccion = st.selectbox("SKU / Producto", options=opciones_validas)

            with col2:
                cantidad = st.number_input("Cantidad", min_value=1, step=1)
                fecha_promesa = st.date_input("Fecha Promesa", format="YYYY-MM-DD")

            submitted = st.form_submit_button("Registrar Orden", type="primary", use_container_width=True)

            if submitted:
                if not norden or not seleccion:
                    st.error("Completa todos los campos.")
                else:
                    producto_data = sku_input.get(seleccion, {})
                    sku_val = producto_data.get("sku", seleccion)

                    payload = {
                        "numero_orden": norden,
                        "sku": sku_val,
                        "cantidad": int(cantidad),
                        "fecha_promesa": fecha_promesa.isoformat(),
                        "status": "Pendiente",
                        "envio1": 0,
                        "envio2": 0,
                        "envio3": 0
                    }

                    try:
                        res = requests.post(f"{API_BASE_URL}/zeutica/ordenes", headers=toks, json=payload)
                        if res.status_code in (200, 201):
                            st.success(f"✅ Orden **{norden}** registrada correctamente.")
                            requests.post("https://n8n-n8n.i4mjht.easypanel.host/webhook/5a5caa1a-3ad5-44ff-9f47-d791f937f2d0",json=payload)
                            st.balloons()
                        else:
                            st.error(f"Error al registrar: {res.status_code} — {res.text}")
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")

    # ─────────────────────────────────────────
    # TAB 2: TRACKING
    # ─────────────────────────────────────────
    with tab_tracking:
        st.markdown("### Seguimiento de Órdenes de Pedido")

        _, col_btn = st.columns([5, 1])
        with col_btn:
            if st.button("🔄 Recargar", use_container_width=True):
                st.rerun()

        pedidos = obtener_pedidos()

        STATUS_ICON = {
            "Entregado":  "🟢",
            "En Tránsito": "🟡",
            "Pendiente":  "🔴",
        }

        def calcular_status(pedido):
            cantidad_v = int(pedido.get("cantidad", 0))
            total = int(pedido.get("envio1", 0)) + int(pedido.get("envio2", 0)) + int(pedido.get("envio3", 0))
            if total >= cantidad_v:
                return "Entregado"
            elif total > 0:
                return "En Tránsito"
            return pedido.get("status", "Pendiente")

        # Tracking solo muestra órdenes que NO están en verde
        pedidos_activos = [p for p in pedidos if calcular_status(p) != "Entregado"]

        if not pedidos_activos:
            st.info("No hay órdenes activas en seguimiento.")
        else:
            for pedido in pedidos_activos:
                pid          = pedido.get("id") or pedido.get("numero_orden")
                norden_v     = pedido.get("numero_orden", "—")
                sku_v        = pedido.get("sku", "—")
                cantidad_v   = int(pedido.get("cantidad", 0))
                fecha_p      = pedido.get("fecha_promesa", "—")
                status_v     = pedido.get("status", "Pendiente")
                envio1_v     = int(pedido.get("envio1", 0))
                envio2_v     = int(pedido.get("envio2", 0))
                envio3_v     = int(pedido.get("envio3", 0))

                # Calcular status actual para el encabezado del expander
                total_actual = envio1_v + envio2_v + envio3_v
                if total_actual >= cantidad_v:
                    status_display = "Entregado"
                elif total_actual > 0:
                    status_display = "En Tránsito"
                else:
                    status_display = status_v

                icono = STATUS_ICON.get(status_display, "⚪")

                with st.expander(
                    f"{icono}  {norden_v}  |  SKU: {sku_v}  |  Pedido: {cantidad_v} pzs  |  Promesa: {fecha_p}  |  **{status_display}**",
                    expanded=(status_display != "Entregado")
                ):
                    # Fila de datos
                    c_qty, c_e1, c_e2, c_e3, c_st = st.columns([1, 1, 1, 1, 2])

                    c_qty.metric("Cantidad Pedida", cantidad_v)

                    new_e1 = c_e1.number_input("Envío 1", min_value=0, value=envio1_v, step=1, key=f"e1_{pid}")
                    new_e2 = c_e2.number_input("Envío 2", min_value=0, value=envio2_v, step=1, key=f"e2_{pid}")
                    new_e3 = c_e3.number_input("Envío 3", min_value=0, value=envio3_v, step=1, key=f"e3_{pid}")

                    total_nuevo = new_e1 + new_e2 + new_e3

                    # Status sugerido según los envíos actuales en pantalla
                    if total_nuevo >= cantidad_v:
                        status_sugerido = "Entregado"
                    elif total_nuevo > 0:
                        status_sugerido = "En Tránsito"
                    else:
                        status_sugerido = status_v

                    opciones_status = ["Pendiente", "En Tránsito", "Entregado"]
                    idx_default = opciones_status.index(status_sugerido) if status_sugerido in opciones_status else 0

                    with c_st:
                        nuevo_status = st.selectbox(
                            "Status",
                            options=opciones_status,
                            index=idx_default,
                            key=f"st_{pid}"
                        )

                    # Barra de progreso
                    if cantidad_v > 0:
                        progreso = min(total_nuevo / cantidad_v, 1.0)
                        st.progress(progreso, text=f"Enviado: {total_nuevo} / {cantidad_v} pzs ({progreso*100:.0f}%)")

                    # Guardar
                    if st.button("💾 Guardar cambios", key=f"save_{pid}", type="primary"):
                        # Si los envíos completan la cantidad, forzar Entregado sin importar el selectbox
                        final_status = "Entregado" if total_nuevo >= cantidad_v else nuevo_status

                        update_payload = {
                            "envio1": new_e1,
                            "envio2": new_e2,
                            "envio3": new_e3,
                            "status": final_status
                        }
                        if actualizar_pedido(pid, update_payload):
                            st.success(f"✅ Orden {norden_v} actualizada — Status: **{final_status}**")
                            st.rerun()
                        else:
                            st.error("Error al actualizar. Verifica la conexión con el servidor.")

                    # Visualización de la firma ya registrada
                    mostrar_firma(norden_v, uid=pid)

                    # Canvas para capturar o actualizar la firma
                    firma_digital(pid, norden_v)

    # ─────────────────────────────────────────
    # TAB 3: HISTORIAL
    # ─────────────────────────────────────────
    with tab_historial:
        st.markdown("### Historial de Ordenes Completadas 🟢")

        _, col_btn_h = st.columns([5, 1])
        with col_btn_h:
            if st.button("🔄 Recargar", key="recargar_historial", use_container_width=True):
                st.rerun()

        # Reutilizamos pedidos ya cargados; si el tab se renderiza primero, los obtenemos
        pedidos_hist = obtener_pedidos()
        completados = [p for p in pedidos_hist if calcular_status(p) == "Entregado"]

        if not completados:
            st.info("Aún no hay órdenes completadas.")
        else:
            # Registro en sesión de órdenes ya enviadas como venta, para no duplicar
            if "ventas_enviadas" not in st.session_state:
                st.session_state.ventas_enviadas = set()

            # Cargamos inventario una sola vez para todo el loop
            inv = obtener_inventario()

            for pedido in completados:
                pid_hist   = pedido.get("id") or pedido.get("numero_orden")  # id único para keys
                norden_v   = pedido.get("numero_orden", "—")
                sku_v      = pedido.get("sku", "—")
                cantidad_v = int(pedido.get("cantidad", 0))
                fecha_p    = pedido.get("fecha_promesa", "—")
                envio1_v   = int(pedido.get("envio1", 0))
                envio2_v   = int(pedido.get("envio2", 0))
                envio3_v   = int(pedido.get("envio3", 0))
                total_env  = envio1_v + envio2_v + envio3_v

                with st.expander(
                    f"🟢  {norden_v}  |  SKU: {sku_v}  |  Pedido: {cantidad_v} pzs  |  Promesa: {fecha_p}  |  **Entregado**",
                    expanded=False
                ):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Cantidad Pedida", cantidad_v)
                    c2.metric("Envío 1", envio1_v)
                    c3.metric("Envío 2", envio2_v)
                    c4.metric("Envío 3", envio3_v)
                    st.progress(1.0, text=f"Enviado: {total_env} / {cantidad_v} pzs (100%)")
                    # Visualización de la firma registrada (solo lectura)
                    mostrar_firma(norden_v, uid=pid_hist)

                # Enviar venta solo la primera vez que esta orden aparece como Entregado 
                norden_v = norden_v[2:] 
                res_check = requests.get(f"{API_BASE_URL}/zeutica/verifica-venta/{norden_v}", headers=toks)
                ya_existe = res_check.json().get("registrada", False)    
                if ya_existe:          
                    item_data   = next((v for v in inv.values() if v.get("sku") == sku_v), {})
                    nombre_prod = item_data.get("nombre", sku_v)
                    precio_clean = float(item_data.get("precio_clean") or 0.0)

                    payload = {
                        "id_venta": norden_v,
                        "sku": sku_v,
                        "stock_bodega": cantidad_v,
                        "precio": precio_clean,
                        "producto": nombre_prod,
                        "fecha": datetime.now().isoformat(),
                        "nombreComprador": "CLEANEST CHOICE",
                        "otros": "FARMACEUTICA",
                        "plataforma": "SISTEMA ZEUTICA",
                        "usuario": st.session_state.usuario_nombre
                    }

                    res = requests.post(f"{API_BASE_URL}/zeutica/producto/venta", headers=toks, json=payload)
                    if res.status_code == 200:
                                                
                        st.success(f"✅ Venta de orden {norden_v} ingresada correctamente")
                        st.balloons()
                    else:
                        st.error(f"❌ Error al enviar venta {norden_v}: {res.text}")    
                  
cleanest()
