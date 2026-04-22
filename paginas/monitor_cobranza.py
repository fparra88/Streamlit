import streamlit as st
import requests
import pandas as pd
from typing import Optional
import math

API_BASE_URL = st.session_state.ip

toks = {
    "Authorization": f"Bearer {st.session_state.token}"
}


# ─── HELPERS DE DATOS ────────────────────────────────────────────────────────

def fetchCreditSales() -> Optional[pd.DataFrame]:
    try:
        res = requests.get(f"{API_BASE_URL}/zeutica/ventas-credito", headers=toks, timeout=10)
        if res.status_code != 200:
            st.error(f"❌ Error en la API: {res.status_code}")
            return None
        data = res.json()
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        if not data:
            return pd.DataFrame()
        return pd.DataFrame(data)
    except requests.exceptions.Timeout:
        st.error("⏱️ Timeout: La API tardó demasiado en responder.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("🔌 Error de conexión: No se puede alcanzar la API.")
        return None
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")
        return None


def normalizeColumnNames(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.replace("(?<!^)(?=[A-Z])", "_", regex=True).str.lower()
    return df


def _col(df: pd.DataFrame, *candidates: str) -> Optional[str]:
    """Retorna el primer nombre de columna que exista en el DataFrame."""
    for name in candidates:
        if name in df.columns:
            return name
    return None


def _safe_float(val, default: float = 0.0) -> float:
    try:
        f = float(val)
        return 0.0 if math.isnan(f) else f
    except (TypeError, ValueError):
        return default


def _init_state():
    if "creditos_df" not in st.session_state:
        st.session_state.creditos_df = None
    if "abono_ok" not in st.session_state:
        st.session_state.abono_ok = False


# ─── FRAGMENTO: RESUMEN Y TABLA ───────────────────────────────────────────────

@st.fragment
def renderResumenCredito():
    df = st.session_state.creditos_df

    if df is None or df.empty:
        st.info("📭 No hay ventas a crédito registradas actualmente.")
        return

    col_saldo = _col(df, "saldo_pendiente", "saldo", "pendiente")
    col_nombre = _col(df, "nombre", "nombre_cliente", "cliente")
    col_id = _col(df, "id_ventas", "id_venta", "id")

    # --- KPI CARDS ---
    st.markdown("### 📊 Resumen de Cartera")
    k1, k2, k3 = st.columns(3)

    clientes_unicos = df[col_nombre].nunique() if col_nombre else len(df)
    with k1:
        st.metric("👥 Clientes con crédito", clientes_unicos)

    total_pendiente = 0.0
    if col_saldo:
        total_pendiente = pd.to_numeric(df[col_saldo], errors="coerce").fillna(0).sum()
    with k2:
        st.metric("💰 Saldo total pendiente", f"${total_pendiente:,.2f}")

    with k3:
        promedio = total_pendiente / clientes_unicos if clientes_unicos else 0
        st.metric("📈 Promedio por cliente", f"${promedio:,.2f}")

    st.divider()

    # --- TABLA CON ORDENAMIENTO ---
    st.markdown("#### 🗂️ Detalle de ventas a crédito")

    col_ctrl1, col_ctrl2 = st.columns([3, 1])
    with col_ctrl1:
        sort_col = st.selectbox(
            "Ordenar por:",
            options=df.columns.tolist(),
            index=df.columns.tolist().index(col_saldo) if col_saldo and col_saldo in df.columns else 0,
            key="sort_col_credito",
        )
    with col_ctrl2:
        sort_dir = st.radio(
            "Orden:", ["↓ Desc", "↑ Asc"], horizontal=True, key="sort_dir_credito"
        )

    df_sorted = df.sort_values(
        by=sort_col, ascending=("Asc" in sort_dir)
    ).reset_index(drop=True)

    st.dataframe(df_sorted, use_container_width=True, hide_index=True)


# ─── FRAGMENTO: PANEL DE ABONOS ───────────────────────────────────────────────

@st.fragment
def renderPanelAbono():
    df = st.session_state.creditos_df

    if df is None or df.empty:
        return

    col_id = _col(df, "id_ventas", "id_venta", "id")
    col_nombre = _col(df, "nombre", "nombre_cliente", "cliente")
    col_saldo = _col(df, "saldo_pendiente", "saldo", "pendiente")

    if not col_id:
        st.warning("⚠️ La respuesta de la API no contiene un campo de ID de venta reconocible.")
        return

    st.markdown("### 💳 Registrar Abono")

    # Construir etiquetas legibles para el selectbox
    def _label(row):
        nombre = row[col_nombre] if col_nombre else "—"
        saldo = _safe_float(row[col_saldo]) if col_saldo else 0.0
        return f"{nombre}  |  Venta #{row[col_id]}  |  Saldo: ${saldo:,.2f}"

    df_con_saldo = df.copy()
    if col_saldo:
        df_con_saldo["_saldo_num"] = pd.to_numeric(df_con_saldo[col_saldo], errors="coerce").fillna(0)
        # Solo mostrar ventas con saldo pendiente > 0
        df_activas = df_con_saldo[df_con_saldo["_saldo_num"] > 0].reset_index(drop=True)
    else:
        df_activas = df_con_saldo.reset_index(drop=True)

    if df_activas.empty:
        st.success("✅ No hay saldos pendientes. ¡Cartera al día!")
        return

    opciones_idx = df_activas.index.tolist()
    labels = [_label(df_activas.loc[i]) for i in opciones_idx]

    with st.form("form_abono", clear_on_submit=True):
        sel_idx = st.selectbox(
            "Selecciona la venta a abonar:",
            options=opciones_idx,
            format_func=lambda i: labels[i],
            key="sel_venta_abono",
        )

        fila = df_activas.loc[sel_idx]
        saldo_max = _safe_float(fila["_saldo_num"]) if "_saldo_num" in fila.index else 0.0

        col_monto, col_info = st.columns([2, 1])
        with col_monto:
            saldo_abonado = st.number_input(
                "Monto del abono ($)",
                min_value=1.0,
                max_value=saldo_max if saldo_max > 0 else 999_999.0,
                value=min(saldo_max, saldo_max) if saldo_max > 0 else 1.0,
                step=1.0,
                format="%.2f",
            )
        with col_info:
            st.metric("Saldo pendiente", f"${saldo_max:,.2f}" if saldo_max else "—")

        submitted = st.form_submit_button(
            "💳 Registrar Abono", type="primary", use_container_width=True
        )

        if submitted:
            id_ventas = fila[col_id]
            if isinstance(id_ventas, float):
                id_ventas = int(id_ventas)

            payload = {
                "id_ventas": id_ventas,
                "saldo_abonado": float(saldo_abonado),
            }

            try:
                with st.spinner("Registrando abono..."):
                    res = requests.post(
                        f"{API_BASE_URL}/zeutica/abonos",
                        headers=toks,
                        json=payload,
                        timeout=10,
                    )

                if res.status_code == 200:
                    nombre_cliente = fila[col_nombre] if col_nombre else f"Venta #{id_ventas}"
                    st.success(
                        f"✅ Abono de **${saldo_abonado:,.2f}** registrado para **{nombre_cliente}**."
                    )
                    st.balloons()
                    # Fuerza recarga de datos para reflejar el nuevo saldo
                    st.session_state.creditos_df = None
                    st.rerun()
                else:
                    st.error(f"❌ Error {res.status_code}: {res.text}")

            except requests.exceptions.ConnectionError:
                st.error("🔌 No se pudo conectar con la API.")
            except Exception as e:
                st.error(f"Error inesperado: {e}")


# ─── LAYOUT PRINCIPAL ─────────────────────────────────────────────────────────

_init_state()

st.title("💳 Monitor de Cobranza")
st.markdown("Consulta el estado de la cartera de clientes con crédito y registra abonos.")

col_btn, col_estado = st.columns([1, 4])
with col_btn:
    if st.button("🔄 Cargar / Actualizar", type="secondary", key="btn_cargar_creditos"):
        with st.spinner("Conectando con el servidor..."):
            df_raw = fetchCreditSales()
        if df_raw is not None:
            st.session_state.creditos_df = (
                normalizeColumnNames(df_raw) if not df_raw.empty else df_raw
            )

with col_estado:
    if st.session_state.creditos_df is not None:
        st.caption(f"✅ {len(st.session_state.creditos_df)} registros cargados.")

st.divider()

if st.session_state.creditos_df is not None:
    renderResumenCredito()
    st.divider()
    renderPanelAbono()
else:
    st.info("⬆️ Presiona **Cargar / Actualizar** para consultar la cartera de crédito.")
