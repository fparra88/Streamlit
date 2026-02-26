import streamlit as st
import requests

API_BASE_URL = "http://10.0.9.227:8090"

st.header("Plataforma de registro de gastos Operativos")
st.info("Ingresa los gastos realizados para la operacion")

with st.form("Registro de Ventas"):
    col1, col2 = st.columns(2)

    with col1:
        descripcion = st.text_input("Ingresa la descripcion del gasto")
        costo = st.text_input("Ingresa el monto del gasto")

    with col2:
        cantidad = st.text_input("Ingresa la cantidad de piezas")

    envio_datos = st.form_submit_button("Registra el gasto")

if envio_datos:
    payload = {
        "descripcion": descripcion,
        "costo": costo,
        "cantidad": cantidad
    }
    try:
        with st.spinner("Enviando datos al servidor en AWS..."):
            res = requests.post(f"{API_BASE_URL}/zeutica/gastos", json=payload)
        if res.status_code == 200:
            st.success("Registro aceptado")

    except:
        st.error("Error de conexion")