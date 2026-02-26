import streamlit as st
import requests

API_BASE_URL = "http://3.151.25.133:8090"

def obtener_skus():
    try:
        response = requests.get(f"{API_BASE_URL}/zeutica/productos") 
        if response.status_code == 200:
            data = response.json() 

    except Exception as e:
        st.error(f"No se pudo conectar con el servidor: {e}")

    return {c['sku']: c for c in data}   

with st.form("consulta_sku"): # Formulario para consultar SKU en DATABASE
    sku_input = obtener_skus()
    seleccion = st.selectbox("Selecciona el sku",sku_input)    
    
    def buscar():
        
        try:
            # Indicador de carga (Spinner)
            with st.spinner('Buscando en la base de datos...'):
                response = requests.get(f"{API_BASE_URL}/zeutica/producto/sku/{seleccion}")
                
            # 3. Manejo de la respuesta
            if response.status_code == 200:
                data = response.json()                
                st.success("¡Producto encontrado!")
                
                # Mostramos los datos de forma estética
                st.write("### Detalles del Producto")
                #st.json(data)  O puedes usar st.table(data) si es una lista
                st.table(data)                

            elif response.status_code == 404:
                st.warning(f"No se encontró ningún producto con el SKU: {sku_input}")
            else:
                st.error(f"Error de la API: Código {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            st.error(f"Error de conexión: {e}")

        st.info("Por favor, introduce un SKU antes de presionar el botón.")
        pass
    st.form_submit_button("Buscar SKU", on_click=buscar())

# --- SECCIÓN 1: Visualizar Inventario ---
if st.button('Visualizar Inventario'):
    data = requests.get(f"{API_BASE_URL}/zeutica/productos")
    if data.status_code == 200:
        st.dataframe(
            data.json(),
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": None,# Poner None OCULTA la columna automáticamente
                }    
        ) 
             
        st.metric(label="Total de Productos", value=len(data.json()))

    else:
        st.error("Error al conectar con la API")
            
    