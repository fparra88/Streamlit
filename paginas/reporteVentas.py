import streamlit as st
import requests
from datetime import datetime

API_BASE_URL = "http://3.151.25.133:8090"

st.header("Reporte de ventas plataformas por fecha")
st.info("Selecciona un inicio y final de fecha para generar reporte de Ventas")

with st.form("Consulta de Ventas"):
    col1, col2 = st.columns(2)

    with col1:
        fecha_inicio = st.date_input("Fecha de Inicio", value=datetime.now())

    with col2:
        fecha_fin = st.date_input("Fecha de Fin", value=datetime.now())

    submit_reporte = st.form_submit_button("Generar Reporte")

if submit_reporte:
    if fecha_inicio > fecha_fin:
        st.error("Error: La fecha inicio no puede ser antes de la fecha final")
    
    else:
        try:
            with st.spinner("Consultando servidor en AWS..."):
                response = requests.get(f"{API_BASE_URL}/zeutica/ventas/{fecha_inicio}/{fecha_fin}")
            
            if response.status_code == 200:                
                ventas = response.json()
                #st.table(ventas)
                st.dataframe(
                    ventas,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "id": None,           # Poner None OCULTA la columna automáticamente
                        "precio": st.column_config.NumberColumn("Precio (MXN)", format="$%.2f"),
                        "fecha_registro": st.column_config.DatetimeColumn("Fecha de Venta", format="DD/MM/YYYY")
                    }    
                )
                st.metric(label="Total de Productos", value=len(ventas))                
                          
            else:
                st.warning("Error: Valor no encontrado")

        except Exception as e:
            st.error(f"Error de conexion {e}")

st.info("Consulta reporte de traspasos a full.")
rep_traspasos = st.button("Consulta de Traspasos")
if rep_traspasos:
    try:
        with st.spinner("Consultando servidor AWS..."):
            res = requests.get(f"{API_BASE_URL}/zeutica/traspasos/reporte")
        if res.status_code == 200:
            data = res.json()

            st.dataframe(data, use_container_width=True, hide_index=True)                 
            
            st.metric(label="Total de traspasos", value=len(data))

        else:
                st.warning("Error: no encontrado")

    except Exception as e:
        st.error(f"Error de conexion {e}")