import streamlit as st
import requests

API_BASE_URL = st.session_state.ip

toks = {
            "Authorization": f"Bearer {st.session_state.token}"
        }

def obtener_skus():
    try:        
        response = requests.get(f"{API_BASE_URL}/zeutica/productos",headers= toks) 
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
                response = requests.get(f"{API_BASE_URL}/zeutica/producto/sku/{seleccion}",headers= toks)
                
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
    data = requests.get(f"{API_BASE_URL}/zeutica/productos", headers= toks)
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
st.warning("Seccion Exclusiva de GERENCIA!!")

# --- SECCIÓN 2: Editar Productos (Solo Gerencia) ---
# Inicializar estado del editor
if "show_editor" not in st.session_state:
    st.session_state.show_editor = False
if "productos_data" not in st.session_state:
    st.session_state.productos_data = None
if "mensaje_exito" not in st.session_state:
    st.session_state.mensaje_exito = False

if st.session_state.usuario_nombre == "gerencia" or "fparra":
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("### Administrador de productos.")
    
    with col2:
        if st.button('Editar Productos', use_container_width=True):
            st.session_state.show_editor = True
            try:
                # Obtener todos los productos
                with st.spinner('Cargando productos...'):
                    response = requests.get(f"{API_BASE_URL}/zeutica/productos", headers= toks)
                
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
                                f"{API_BASE_URL}/zeutica/productos/editados", headers= toks,
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

st.divider(width='stretch')

# --- SECCIÓN 3: Crear Nuevo Producto (Solo Gerencia) ---
# Inicializar estado del formulario de nuevo producto
if "show_form_nuevo" not in st.session_state:
    st.session_state.show_form_nuevo = False
if "mensaje_nuevo_exito" not in st.session_state:
    st.session_state.mensaje_nuevo_exito = False

if st.session_state.usuario_nombre == "gerencia" or "fparra":
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("### Crear Nuevo Producto.")
    
    with col2:
        if st.button('➕ Nuevo Producto', use_container_width=True):
            st.session_state.show_form_nuevo = True
    
    # Mostrar mensaje de éxito si aplica
    if st.session_state.mensaje_nuevo_exito:
        st.success("✅ Producto creado exitosamente")
        st.session_state.mensaje_nuevo_exito = False
    
    # Mostrar formulario SOLO si está activo
    if st.session_state.show_form_nuevo:
        st.info("Completa los datos del nuevo producto")
        
        # Crear columnas para mejor presentación
        col1, col2 = st.columns(2)
        
        with col1:
            sku = st.text_input("SKU", placeholder="Ej: COFPLI-001")
            nombre = st.text_input("Nombre", placeholder="Ej: Producto XYZ")
            categoria = st.text_input("Categoría", placeholder="Ej: COFIA")
            medida = st.text_input("Medida", placeholder="Ej: UNIDAD, PZA")
            ubicacion = st.text_input("Ubicación", placeholder="Ej: CEDIS - Estante 5")
        
        with col2:
            stock_minimo = st.number_input("Stock Mínimo", min_value=50, value=300, format="%d")
            numero_referencia = st.number_input("Número de Referencia", min_value=0, value=0, format="%d")
            costo_total = st.number_input("Costo Total", min_value=0.0, value=0.0, format="%.2f")
            precio = st.number_input("Precio", min_value=0.0, value=0.0, format="%.2f")
            precio_2 = st.number_input("Precio_2", min_value=0.0, value=0.0, format="%.2f")
            precio_3 = st.number_input("Precio_3", min_value=0.0, value=0.0, format="%.2f")
        
        # Botones de acción
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            if st.button("✅ Crear Producto", use_container_width=True):
                # Validar que al menos los campos básicos estén llenos
                if not sku or not nombre or not categoria:
                    st.error("❌ Por favor completa SKU, Nombre y Categoría")
                else:
                    try:
                        with st.spinner('Creando producto...'):
                            payload = {
                                "sku": sku,
                                "nombre": nombre,
                                "categoria": categoria,
                                "medida": medida,
                                "ubicacion": ubicacion,
                                "stock_minimo": stock_minimo,
                                "numero_referencia": numero_referencia,
                                "costo_total": costo_total,
                                "precio": precio,
                                "precio_2": precio_2,
                                "precio_3": precio_3
                            }
                            
                            # Hacer POST al endpoint
                            response = requests.post(
                                f"{API_BASE_URL}/zeutica/producto/nuevo", headers= toks,
                                json=payload
                            )
                        
                        if response.status_code == 200 or response.status_code == 201:
                            st.session_state.mensaje_nuevo_exito = True
                            st.session_state.show_form_nuevo = False
                            st.rerun()
                        else:
                            st.error(f"Error al crear producto: Código {response.status_code}")
                            st.error(response.text)
                    
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error de conexión: {e}")
                    except Exception as e:
                        st.error(f"Error inesperado: {e}")
        
        with col_btn2:
            if st.button("❌ Cancelar", use_container_width=True):
                st.session_state.show_form_nuevo = False
                st.rerun()
