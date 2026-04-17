import streamlit as st
import pandas as pd
from datetime import date
import requests

API_BASE_URL = st.session_state.ip

toks = {
            "Authorization": f"Bearer {st.session_state.token}"
        }

st.title("💰 Gestión Financiera - Zeutica")

# 1. MÉTRICAS RESUMEN
col1, col2, col3 = st.columns(3)
# Supongamos que traes estos datos de tu API
col1.metric("Por Cobrar (CxC)", "$45,200.00", "+5%")
col2.metric("Por Pagar (CxP)", "$12,800.00", "-2%", delta_color="inverse")
col3.metric("Flujo Neto Proyectado", "$32,400.00")

st.divider()

# 2. TABS PARA CXC Y CXP
tab_cxc, tab_cxp = st.tabs(["📥 Cuentas por Cobrar", "📤 Cuentas por Pagar"])

with tab_cxc:
    st.subheader("Pendientes de Clientes")
    # Traer datos de la API
    res = requests.get(f"{API_BASE_URL}/zeutica/finanzas/cxc", headers=toks)
    if res.status_code == 200:
        df_cxc = pd.DataFrame(res.json())

        # Resaltar vencidos en rojo usando Pandas Styling
        def resaltar_vencidos(s):
            return ['background-color: #ffcccc' if v < 0 else '' for v in s]

        if not df_cxc.empty:
            # Solo aplicamos configuración si hay datos
            st.data_editor(df_cxc.style.apply(resaltar_vencidos, subset=['dias_restantes']))
        else:
            st.info("🙌 No hay cuentas por cobrar pendientes hoy.")               
                
        st.dataframe(
            df_cxc.style.apply(resaltar_vencidos, subset=['dias_restantes']),
            column_config={
                "saldo_pendiente": st.column_config.NumberColumn("Saldo $", format="$%.2f"),
                "dias_restantes": st.column_config.NumberColumn("Días para vencer", help="Negativo significa vencido")
            },
            hide_index=True
        )

with tab_cxp:
    st.subheader("Obligaciones con Proveedores")
    # Botón para registrar un nuevo pago (CxP)
    if st.button("➕ Registrar Nueva Cuenta por Pagar"):
        # Abrir formulario de registro
        pass