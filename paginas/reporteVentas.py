import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from streamlit_javascript import st_javascript

API_BASE_URL = st.session_state.ip

toks = {
            "Authorization": f"Bearer {st.session_state.token}"
        }

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
                response = requests.get(f"{API_BASE_URL}/zeutica/ventas/{fecha_inicio}/{fecha_fin}", headers= toks)
            
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
            res = requests.get(f"{API_BASE_URL}/zeutica/traspasos/reporte", headers= toks)
        if res.status_code == 200:
            data = res.json()

            st.dataframe(data, use_container_width=True, hide_index=True)                 
            
            st.metric(label="Total de traspasos", value=len(data))

        else:
                st.warning("Error: no encontrado")

    except Exception as e:
        st.error(f"Error de conexion {e}")

st.divider()

# --------- Seccion de Analisis Estadistico a Mostrar ----------
st.header("Analisis estadistico de ventas por SKU")
st.info("Predicción semanal de ventas por SKU generada por el modelo estadístico. Se actualiza automáticamente cada lunes a las 8:30 AM.")

def obtener_estadistica():
    """POST /zeutica/obtener-estadistica → DataFrame con predicción semanal por SKU."""
    hoy = datetime.now()
    # Retroceder 3 meses manejando rollover de año
    if hoy.month > 3:
        hace_3m = hoy.replace(month=hoy.month - 3)
    else:
        hace_3m = hoy.replace(year=hoy.year - 1, month=hoy.month + 9)

    try:
        res = requests.post(
            f"{API_BASE_URL}/zeutica/obtener-estadistica",
            headers=toks,
            json={
                "fecha":  hace_3m.strftime("%Y-%m-%d"),
                "fecha2": hoy.strftime("%Y-%m-%d"),
            },
            timeout=15,
        )
        if res.status_code == 200:
            data = res.json()
            return pd.DataFrame(data) if data else pd.DataFrame()
        st.error(f"Error al obtener predicción ({res.status_code})")
        return None
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# Detectamos día y hora del cliente vía JS para no depender del timezone del servidor
js_day  = st_javascript("new Date().getDay()")    # 0=Dom 1=Lun … 6=Sab
js_hour = st_javascript("new Date().getHours()")
js_min  = st_javascript("new Date().getMinutes()")

# Clave por fecha para que el auto-fetch solo ocurra una vez por lunes en la sesión
_hora_raw = st.session_state.get("cliente_hora", "")
fecha_key = str(_hora_raw)[:10] if isinstance(_hora_raw, str) else ""
lunes_key = f"pred_lunes_{fecha_key}"

es_lunes_830 = (
    isinstance(js_day,  (int, float)) and int(js_day)  == 1
    and isinstance(js_hour, (int, float)) and int(js_hour) == 8
    and isinstance(js_min,  (int, float)) and 25 <= int(js_min) <= 59
)

if es_lunes_830 and lunes_key not in st.session_state:
    st.session_state[lunes_key] = True
    st.session_state.pred_df = obtener_estadistica()

st.info("Predicción semanal de ventas por SKU generada por el modelo estadístico.")

if st.button("🔄 Obtener Predicción Semanal", use_container_width=False):
    st.session_state.pred_df = obtener_estadistica()

if "pred_df" in st.session_state and st.session_state.pred_df is not None:
    df_pred = st.session_state.pred_df
    if not df_pred.empty:
        # Expande JSON de columna predicciones → 3 cols limpias
        if "predicciones" in df_pred.columns:
            df_pred = pd.json_normalize(df_pred["predicciones"].apply(
                lambda x: x if isinstance(x, dict) else __import__("json").loads(x)
            ))[["sku", "cantidad", "prediccion_ventas"]]
        st.dataframe(
            df_pred,
            use_container_width=True,
            hide_index=True,
            column_config={
                "sku": st.column_config.TextColumn("SKU"),
                "cantidad": st.column_config.NumberColumn("Cantidad"),
                "prediccion_ventas": st.column_config.NumberColumn("Predicción Ventas", format="%.2f"),
            }
        )
        st.metric(label="SKUs en predicción", value=len(df_pred))
    else:
        st.info("Sin datos de predicción disponibles.")
else:
    st.caption("Presiona el botón o espera al lunes 8:30 AM para carga automática.")

