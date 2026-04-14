import streamlit as st
import requests
import pandas as pd

# ============================================================================
# 1. SEGURIDAD Y ESTADO INICIAL
# ============================================================================
if "token" not in st.session_state or "ip" not in st.session_state:
    st.error("⚠️ No hay sesión activa. Por favor, inicia sesión.")
    st.stop()

API_BASE_URL = st.session_state.ip
toks = {"Authorization": f"Bearer {st.session_state.token}"}

# Estado del carrito y costos históricos del SKU activo
if "carrito" not in st.session_state:
    st.session_state.carrito = []
if "costos_bd" not in st.session_state:
    st.session_state.costos_bd = []


# ============================================================================
# 2. CALLBACKS
# ============================================================================
def actualizar_historial():
    """Carga el historial de costos cuando cambia el SKU seleccionado."""
    sku = st.session_state.mi_selector_sku
    try:
        res = requests.get(f"{API_BASE_URL}/zeutica/ultimos-costos/{sku}", headers=toks, timeout=5)
        st.session_state.costos_bd = res.json().get("costos", []) if res.status_code == 200 else []
    except Exception:
        st.session_state.costos_bd = []


def eliminar_item(idx: int):
    """Elimina el ítem en la posición idx del carrito."""
    st.session_state.carrito.pop(idx)


# ============================================================================
# 3. OBTENER PRODUCTOS (cacheado 5 min)
# ============================================================================
@st.cache_data(ttl=300)
def obtener_productos():
    try:
        resp = requests.get(f"{API_BASE_URL}/zeutica/productos", headers=toks, timeout=5)
        if resp.status_code == 200:
            productos = resp.json()
            prod_dict = {p["sku"]: p for p in productos}
            opciones = [(p["sku"], f"{p['sku']} - {p.get('nombre', 'Sin nombre')}") for p in productos]
            return prod_dict, opciones
        return {}, []
    except Exception:
        return {}, []


productos_dict, opciones_productos = obtener_productos()

if not opciones_productos:
    st.info("No hay productos disponibles o hay un problema de conexión.")
    st.stop()


# ============================================================================
# 4. ENCABEZADO DE LA FACTURA
# ============================================================================
st.title("📦 Registrar Factura de Compra")
st.divider()

st.subheader("📄 Datos de la Factura")
col_f1, col_f2, col_f3 = st.columns([1, 2, 1])

with col_f1:
    num_factura = st.text_input("# Factura", placeholder="Ej. FAC-2024-001", key="num_factura_input")

with col_f2:
    proveedor = st.text_input("🏭 Proveedor", placeholder="Nombre del proveedor", key="proveedor_input")

with col_f3:
    iva_pct = st.number_input(
        "IVA (%)",
        min_value=0.0, max_value=100.0,
        value=16.0, step=0.5, format="%.1f",
        help="Porcentaje de IVA aplicado al total de la factura"
    )

st.divider()


# ============================================================================
# 5. AGREGAR ÍTEMS AL CARRITO
# ============================================================================
st.subheader("➕ Agregar Ítem")

col1, col2 = st.columns([1, 2])
with col1:
    sku_sel = st.selectbox(
        "🔍 Producto (SKU)",
        options=[opt[0] for opt in opciones_productos],
        format_func=lambda x: next((opt[1] for opt in opciones_productos if opt[0] == x), x),
        key="mi_selector_sku",
        on_change=actualizar_historial,
    )

# Primera carga: asegurar historial del SKU activo
if "ultimo_sku" not in st.session_state:
    st.session_state.ultimo_sku = None
if sku_sel != st.session_state.ultimo_sku:
    actualizar_historial()
    st.session_state.ultimo_sku = sku_sel

nombre_prod = productos_dict.get(sku_sel, {}).get("nombre", "Sin nombre")
with col2:
    st.text_input("📝 Nombre", value=nombre_prod, disabled=True)

col3, col4, col5, col6 = st.columns(4)

with col3:
    qty = st.number_input("Cantidad", min_value=1, value=1, step=1)

with col4:
    costo_unit = st.number_input(
        "💲 Costo unitario",
        min_value=0.0, value=0.0, step=0.01, format="%.2f",
        help="Precio de compra por unidad"
    )

with col5:
    descuento_pct = st.number_input(
        "Descuento (%)",
        min_value=0.0, max_value=100.0,
        value=0.0, step=0.5, format="%.1f",
        help="Descuento sobre este ítem"
    )

# Costo promedio proyectado (incluye el costo ingresado por el usuario)
historial = st.session_state.costos_bd
lista_prom = historial + [costo_unit] if costo_unit > 0 else historial
costo_prom = round(sum(lista_prom) / len(lista_prom), 2) if lista_prom else 0.0

# Subtotal usa el costo promedio proyectado, no el unitario directo
subtotal_item = qty * costo_prom * (1 - descuento_pct / 100)

with col6:
    # Mostramos el costo promedio proyectado y el delta respecto al costo ingresado
    delta_prom = round(costo_prom - costo_unit, 2) if costo_unit > 0 else 0.0
    st.metric("💲 Costo unit. promedio", f"${costo_prom:,.2f}", delta=f"{delta_prom:+.2f} vs ingresado")

if not historial:
    st.caption("⚠️ Sin compras previas — el promedio es el costo ingresado.")
else:
    st.caption(f"✅ Promedio de {len(lista_prom)} registros. Subtotal ítem: **${subtotal_item:,.2f}**")

if st.button("🛒 Agregar al carrito", use_container_width=True):
    errores_item = []
    if not sku_sel:
        errores_item.append("Selecciona un producto.")
    if qty <= 0:
        errores_item.append("La cantidad debe ser mayor a 0.")
    if costo_unit <= 0:
        errores_item.append("El costo unitario debe ser mayor a 0.")

    if errores_item:
        for e in errores_item:
            st.warning(f"⚠️ {e}")
    else:
        # Verificar si el SKU ya existe en el carrito para acumularlo
        existente = next((i for i, it in enumerate(st.session_state.carrito) if it["sku"] == sku_sel), None)
        if existente is not None:
            # Actualizamos la línea existente sumando cantidad
            it = st.session_state.carrito[existente]
            nueva_qty = it["qty"] + qty
            it["qty"] = nueva_qty
            it["costo_unit"] = costo_unit          # actualiza al último precio
            it["descuento_pct"] = descuento_pct
            it["subtotal"] = nueva_qty * costo_prom * (1 - descuento_pct / 100)
            it["costo_prom"] = costo_prom
        else:
            st.session_state.carrito.append({
                "sku": sku_sel,
                "nombre": nombre_prod,
                "qty": int(qty),
                "costo_unit": float(costo_unit),
                "descuento_pct": float(descuento_pct),
                "subtotal": float(subtotal_item),
                "costo_prom": float(costo_prom),
            })
        st.success(f"✅ '{nombre_prod}' agregado al carrito.")


# ============================================================================
# 6. CARRITO ACTUAL
# ============================================================================
st.divider()
st.subheader("🛒 Carrito de Compra")

if not st.session_state.carrito:
    st.info("El carrito está vacío. Agrega ítems arriba.")
else:
    # Mostramos tabla del carrito
    df_carrito = pd.DataFrame(st.session_state.carrito)[
        ["sku", "nombre", "qty", "costo_unit", "descuento_pct", "subtotal"]
    ].rename(columns={
        "sku": "SKU",
        "nombre": "Nombre",
        "qty": "Cantidad",
        "costo_unit": "Costo Unit.",
        "descuento_pct": "Desc. (%)",
        "subtotal": "Subtotal",
    })

    st.dataframe(
        df_carrito.style.format({
            "Costo Unit.": "${:,.2f}",
            "Desc. (%)": "{:.1f}%",
            "Subtotal": "${:,.2f}",
        }),
        use_container_width=True,
        hide_index=True,
    )

    # Botones para eliminar ítems individuales
    cols_del = st.columns(len(st.session_state.carrito))
    for idx, item in enumerate(st.session_state.carrito):
        with cols_del[idx]:
            if st.button(f"🗑️ {item['sku']}", key=f"del_{idx}", help=f"Eliminar {item['nombre']}"):
                eliminar_item(idx)
                st.rerun()

    # ========================================================================
    # 7. TOTALES DE LA FACTURA
    # ========================================================================
    st.divider()
    subtotal_bruto = sum(it["qty"] * it["costo_unit"] for it in st.session_state.carrito)
    desc_total = sum(it["qty"] * it["costo_unit"] * (it["descuento_pct"] / 100) for it in st.session_state.carrito)
    base_grav = subtotal_bruto - desc_total
    iva_monto = base_grav * (iva_pct / 100)
    total_final = base_grav + iva_monto

    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    col_t1.metric("Subtotal bruto", f"${subtotal_bruto:,.2f}")
    col_t2.metric(f"Descuento total", f"-${desc_total:,.2f}")
    col_t3.metric(f"IVA ({iva_pct:.1f}%)", f"${iva_monto:,.2f}")
    col_t4.metric("**Total Factura**", f"${total_final:,.2f}")

    st.divider()

    # ========================================================================
    # 8. REGISTRAR FACTURA COMPLETA
    # ========================================================================
    if st.button("✅ Registrar Factura", use_container_width=True, type="primary"):
        errores_fac = []
        if not num_factura.strip():
            errores_fac.append("Ingresa el número de factura.")
        if not proveedor.strip():
            errores_fac.append("Ingresa el nombre del proveedor.")

        if errores_fac:
            for e in errores_fac:
                st.error(f"❌ {e}")
        else:
            usuario = st.session_state.get("usuario_nombre", "usuario")
            errores_api = []

            # La API espera una lista; construimos todos los ítems de una vez
            payload_compras = [
                {
                    "sku": item["sku"],
                    "nombre": item["nombre"],
                    "stock_bodega": item["qty"],
                    "costo_total": item["costo_unit"],
                    "num_factura": num_factura.strip(),
                    "proveedor": proveedor.strip(),
                    "descuento_pct": item["descuento_pct"],
                    "iva_pct": iva_pct,
                    "subtotal": item["subtotal"],
                    "usuario": usuario,
                }
                for item in st.session_state.carrito
            ]

            try:
                with st.spinner("Registrando factura..."):
                    resp = requests.post(
                        f"{API_BASE_URL}/zeutica/compras",
                        headers=toks, json=payload_compras, timeout=10
                    )
                if resp.status_code not in [200, 201]:
                    errores_api.append(f"{resp.status_code} - {resp.text}")
            except Exception as e:
                errores_api.append(str(e))

            # Actualizar costo promedio por ítem (independiente del resultado principal)
            for item in st.session_state.carrito:
                try:
                    requests.post(
                        f"{API_BASE_URL}/zeutica/costoPromedio",
                        json={"sku": item["sku"], "costo_prom": item["costo_prom"]},
                        headers=toks, timeout=5
                    )
                except Exception:
                    pass  # No bloqueamos si falla el promedio

            if errores_api:
                for e in errores_api:
                    st.error(f"❌ Error al registrar factura: {e}")
            else:
                st.balloons()
                st.success(f"🎉 Factura **{num_factura}** registrada exitosamente — {len(st.session_state.carrito)} ítems, total ${total_final:,.2f}")
                # Limpiar carrito tras registro exitoso
                st.session_state.carrito = []
                import time
                time.sleep(2)
                st.rerun()


# ============================================================================
# 9. HISTORIAL DE COMPRAS
# ============================================================================
st.divider()
st.subheader("📋 Historial de Compras")

if st.button("🔍 Consultar compras registradas", use_container_width=True):
    try:
        with st.spinner("Cargando historial..."):
            resp_hist = requests.get(
                f"{API_BASE_URL}/zeutica/registro-compras",
                headers=toks, timeout=10
            )
        if resp_hist.status_code == 200:
            data = resp_hist.json()
            # Soporta respuesta como lista directa o dentro de una llave
            if isinstance(data, dict):
                data = data.get("compras", data.get("data", []))
            if data:
                df_hist = pd.DataFrame(data)
                st.dataframe(df_hist, use_container_width=True, hide_index=True)
            else:
                st.info("No hay compras registradas.")
        else:
            st.error(f"❌ Error al obtener historial: {resp_hist.status_code} - {resp_hist.text}")
    except Exception as e:
        st.error(f"❌ No se pudo conectar con el servidor: {e}")


# ============================================================================
# 10. PANEL LATERAL
# ============================================================================
with st.sidebar:
    st.info(
        "📋 **Guía de uso:**\n"
        "1. Completa los datos de la factura (número y proveedor)\n"
        "2. Selecciona un producto y ajusta cantidad, costo y descuento\n"
        "3. Haz clic en **Agregar al carrito**\n"
        "4. Repite para cada ítem de la factura\n"
        "5. Verifica los totales (descuento e IVA se calculan automáticamente)\n"
        "6. Haz clic en **Registrar Factura**"
    )
    if st.session_state.carrito:
        st.metric("Ítems en carrito", len(st.session_state.carrito))
    if st.button("🗑️ Vaciar carrito", use_container_width=True):
        st.session_state.carrito = []
        st.rerun()
