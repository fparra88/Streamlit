import streamlit as st
import requests

API_BASE_URL = st.session_state.ip

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

st.divider(width='stretch')

# --- SECCIÓN 2: Editar Productos (Solo Gerencia) ---
# Inicializar estado del editor
if "show_editor" not in st.session_state:
    st.session_state.show_editor = False
if "productos_data" not in st.session_state:
    st.session_state.productos_data = None
if "mensaje_exito" not in st.session_state:
    st.session_state.mensaje_exito = False

if st.session_state.usuario_nombre == "fparra":
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("### Gestión de Productos")
    
    with col2:
        if st.button('Editar Productos', use_container_width=True):
            st.session_state.show_editor = True
            try:
                # Obtener todos los productos
                with st.spinner('Cargando productos...'):
                    response = requests.get(f"{API_BASE_URL}/zeutica/productos")
                
                if response.status_code == 200:
                    st.session_state.productos_data = response.json()
                else:
                    st.error(f"Error al obtener productos: Código {response.status_code}")
            
            except requests.exceptions.RequestException as e:
                st.error(f"Error de conexión: {e}")
    
    # Mostrar mensaje de éxito si aplica
    if st.session_state.mensaje_exito:
        st.success("✅ Cambios guardados exitosamente")
        st.session_state.mensaje_exito = False
    
    # Mostrar editor SOLO si está activo
    if st.session_state.show_editor:
        if st.session_state.productos_data is not None:
            st.info("Edita los datos y haz clic en 'Guardar Cambios'")
            
            # Mostrar editor de datos
            st.write("#### Datos para Editar")
            datos_editados = st.data_editor(
                st.session_state.productos_data,
                use_container_width=True,
                hide_index=False,
                key="editor_productos"
            )
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Botón para guardar cambios
                if st.button("✅ Guardar Cambios", use_container_width=True):
                    try:
                        with st.spinner('Guardando cambios...'):
                            # Convertir los datos editados a diccionario
                            payload = {"productos": datos_editados}
                            
                            # Hacer POST al endpoint
                            save_response = requests.post(
                                f"{API_BASE_URL}/productos/editados",
                                json=payload
                            )
                        
                        if save_response.status_code == 200:
                            st.session_state.mensaje_exito = True
                            st.session_state.show_editor = False
                            st.session_state.productos_data = None
                            st.rerun()
                        else:
                            st.error(f"Error al guardar: Código {save_response.status_code}")
                            st.error(save_response.text)
                    
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error de conexión al guardar: {e}")
                    except Exception as e:
                        st.error(f"Error inesperado: {e}")
            
            with col2:
                # Botón para cancelar
                if st.button("❌ Cancelar", use_container_width=True):
                    st.session_state.show_editor = False
                    st.session_state.productos_data = None
                    st.rerun()
