import streamlit as st
import requests
import pandas as pd

#API_BASE_URL = "http://10.0.9.227:8090" # url produccion
API_BASE_URL = "http://127.0.0.1:8000"

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
        "usuario_registro": st.session_state.get("usuario_nombre", "usuario"),
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

# Sección de consulta de gastos
st.divider()
st.subheader("Consulta de Gastos Registrados")

if st.button("Consultar Gastos", key="btn_consulta_gastos"):
    payload_consulta = {
        "usuario": st.session_state.get("usuario_nombre", "usuario")
    }
    try:
        with st.spinner("Consultando gastos..."):
            res = requests.get(f"{API_BASE_URL}/zeutica/consultagastos", params=payload_consulta)
        
        if res.status_code == 200:
            st.success("✅ Consulta realizada exitosamente")
            datos = res.json()  
               
             
            
            # Mostrar el DataFrame con columnas ordenadas
            st.dataframe(datos, use_container_width=True)
        else:
            st.error(f"❌ Error en la consulta: Código {res.status_code}")
            st.warning(res.text)
    
    except requests.exceptions.Timeout:
        st.error("❌ Tiempo de espera agotado. El servidor tardó demasiado en responder.")
    except requests.exceptions.ConnectionError:
        st.error("❌ Error de conexión. No se pudo conectar con el servidor.")
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error en la petición: {str(e)}")
    except Exception as e:
        st.error(f"❌ Error inesperado: {str(e)}")