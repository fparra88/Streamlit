import streamlit as st
import requests
from paginas.ventasPagina import obtener_inventario

API_BASE_URL = st.session_state.ip

toks = {
    "Authorization": f"Bearer {st.session_state.get('token')}"
}

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

def firma_digital(pid, norden_v):
    """Muestra canvas de firma, convierte a base64 y envía a /zeutica/efirma"""
    from streamlit_drawable_canvas import st_canvas
    import base64
    import io
    from PIL import Image
    from datetime import datetime

    key_show = f"show_firma_{pid}"
    if key_show not in st.session_state:
        st.session_state[key_show] = False

    st.markdown("---")

    if st.button("✍️ Firma Digital", key=f"btn_firma_{pid}", use_container_width=True):
        st.session_state[key_show] = not st.session_state[key_show]

    if st.session_state[key_show]:
        st.markdown("**Dibuja la firma en el recuadro:**")

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

        if st.button("📤 Enviar Firma", key=f"enviar_firma_{pid}", type="primary"):
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
                "fecha": datetime.now().isoformat(),
            }

            try:
                res = requests.post(f"{API_BASE_URL}/zeutica/efirma", headers=toks, json=payload)
                if res.status_code in (200, 201):
                    st.success("✅ Firma enviada correctamente.")
                    st.session_state[key_show] = False
                else:
                    st.error(f"Error al enviar firma: {res.status_code} — {res.text}")
            except Exception as e:
                st.error(f"Error de conexión: {e}")

def cleanest():
    st.title("CLEANEST CHOICE")

    tab_nueva, tab_tracking = st.tabs(["Nueva Orden de Pedido", "Tracking de Pedidos"])

    # ─────────────────────────────────────────
    # TAB 1: NUEVA ORDEN
    # ─────────────────────────────────────────
    with tab_nueva:
        st.markdown("### Ingresa los datos de la Orden de Pedido")

        with st.form("formulario_cleanest", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                norden = st.text_input("Número de Orden", value="OC")
                sku_input = obtener_inventario()
                opciones_validas = list(sku_input.keys()) if sku_input else []
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

        if not pedidos:
            st.info("No hay órdenes registradas.")
        else:
            STATUS_ICON = {
                "Entregado":  "🟢",
                "En Tránsito": "🟡",
                "Pendiente":  "🔴",
            }

            for pedido in pedidos:
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

                    # Firma digital por orden
                    firma_digital(pid, norden_v)

cleanest()
