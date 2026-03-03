import streamlit as st
import requests
import pandas as pd
import math

#API_BASE_URL = "http://10.0.9.227:8090" # url produccion
API_BASE_URL = "http://127.0.0.1:8000"

def sanitize_row_data(row):
    """
    Limpia los datos de una fila antes de enviarlos a la API.
    Convierte NaN a None y rellena campos requeridos con strings vacíos.
    """
    # Campos que requieren string en lugar de null
    campos_string = ['contacto', 'telefono', 'empresa', 'direccion']
    
    sanitized = {}
    
    for key, value in row.items():
        # Manejo de NaN en valores numéricos
        if isinstance(value, float) and math.isnan(value):
            # Si es un campo que requiere string, usar string vacío
            if key in campos_string:
                sanitized[key] = ""
            else:
                sanitized[key] = None
        # Si es None
        elif value is None:
            # Si es un campo que requiere string, usar string vacío
            if key in campos_string:
                sanitized[key] = ""
            else:
                sanitized[key] = None
        # Mantener otros valores tal cual
        else:
            sanitized[key] = value
    
    return sanitized

def app():
    st.title("📂 Alta de Clientes")
    st.markdown("Ingresa los datos del cliente para registrarlo en la base de datos de AWS.")
    
    # Importante: No uses 'localhost' aquí si la API está en la nube
    

    # Usamos st.form para agrupar los inputs y enviarlos solo al presionar el botón
    with st.form("formulario_cliente", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            usoscfdi = ["G01 - Adquisición de mercancías",
            "G02 - Devoluciones, descuentos o bonificaciones",
            "G03 - Gastos en general",
            "I01 - Construcciones",
            "I02 - Mobiliario y equipo de oficina por inversiones",
            "I03 - Equipo de transporte",
            "I04 - Equipo de cómputo y accesorios",
            "I05 - Dados, troqueles, moldes, matrices y herramental",
            "I06 - Comunicaciones telefónicas",
            "I07 - Comunicaciones satelitales",
            "I08 - Otra maquinaria y equipo",
            "D01 - Honorarios médicos, dentales y gastos hospitalarios",
            "D02 - Gastos médicos por incapacidad o discapacidad",
            "D03 - Gastos funerales",
            "D04 - Donativos",
            "D05 - Intereses reales efectivamente pagados por créditos hipotecarios (casa habitación)",
            "D06 - Aportaciones voluntarias al SAR",
            "D07 - Primas por seguros de gastos médicos",
            "D08 - Gastos de transportación escolar obligatoria",
            "D09 - Depósitos en cuentas especiales para el ahorro, planes de pensiones",
            "D10 - Pagos por servicios educativos (colegiaturas)",
            "S01 - Sin efectos fiscales",
            "CP01 - Pagos",
            "CN01 - Nómina"]
            nombre = st.text_input("Nombre Completo *")
            rfc = st.text_input("Ingresa RFC (Obligatorio)")
            telefono = st.text_input("Teléfono")
            cp = st.text_input("Codigo Postal(obligatorio sat)")
            usocfdi = st.selectbox("Selecciona el uso de cfdi", usoscfdi)
            
        
        with col2:
            regimenes = ["601 - General de Ley Personas Morales",
            "603 - Personas Morales con Fines no Lucrativos",
            "605 - Sueldos y Salarios e Ingresos Asimilados a Salarios",
            "606 - Arrendamiento",
            "607 - Régimen de Enajenación de acciones en bolsa de valores",
            "608 - Enajenación de bienes",
            "609 - Consolidación",
            "610 - Residentes en el Extranjero sin Establecimiento Permanente en México",
            "611 - Ingresos por Dividendos (socios y accionistas)",
            "612 - Personas Físicas con Actividades Empresariales y Profesionales",
            "614 - Intereses",
            "615 - De los demás ingresos",
            "616 - Sin obligaciones fiscales",
            "620 - Sociedades Cooperativas de Producción que optan por diferir sus ingresos",
            "621 - Incorporación Fiscal",
            "622 - Actividades Agrícolas, Ganaderas, Silvícolas y Pesqueras",
            "623 - Opcional para Grupos de Sociedades",
            "624 - Coordinados",
            "625 - Régimen de las Actividades Empresariales con ingresos a través de Plataformas Tecnológicas",
            "626 - Régimen Simplificado de Confianza"]
            email = st.text_input("Correo Electrónico *")
            # Dejamos dirección como text_area por si es larga
            direccion = st.text_area("Dirección Física (Opcional)", height=100)            
            empresa = st.text_input("Empresa (opcional)")
            regimen = st.selectbox("Selecciona el regimen fiscal", regimenes)
            contacto = st.text_input("Agrega datos del contacto")

        # Botón de envío
        submitted = st.form_submit_button("💾 Guardar Cliente")

        if submitted:
            # 1. Validación básica en el Frontend
            if not nombre or not rfc:
                st.warning("⚠️ Por favor completa los campos obligatorios (Nombre y RFC), tambien asegurate de ingresar CP y uso de cfdi.")
                return # Detiene la ejecución si faltan datos

            # Preparar el JSON
            datos_cliente = {
                "nombre": nombre,
                "email": email,
                "empresa": empresa,
                "contacto": contacto,
                "telefono": telefono,
                "direccion": direccion if direccion else None, # Envía null si está vacío
                "rfc": rfc,
                "cp": cp,
                "regimen": regimen,
                "usocfdi": usocfdi
            }

            # 3. Enviar a FastAPI
            try:
                with st.spinner("Conectando con AWS..."):
                    respuesta = requests.post(f"{API_BASE_URL}/zeutica/clientenuevo", json=datos_cliente)

                # 4. Manejar la respuesta del servidor
                if respuesta.status_code == 200:
                    data_resp = respuesta.json()
                    st.success(f"✅ ¡Cliente registrado! ID asignado: {data_resp.get('id')}")
                    # Como usamos clear_on_submit=True, el formulario se limpiará solo
                else:
                    st.error(f"❌ Error del servidor: {respuesta.status_code} - {respuesta.text}")

            except requests.exceptions.ConnectionError:
                st.error("🔌 No se pudo conectar con la API. Verifica que el servidor en AWS esté activo.")
            except Exception as e:
                st.error(f"Ocurrió un error inesperado: {e}")

# Si ejecutas este archivo directo para probar:
if __name__ == "__main__":
    app()
    # --- ESTADOS INICIALES ---
    if "clientes_data" not in st.session_state:
        st.session_state.clientes_data = None
    if "mostrar_editor" not in st.session_state:
        st.session_state.mostrar_editor = False
    
    url_obtener = f"{API_BASE_URL}/zeutica/clientes"
    url_editar = f"{API_BASE_URL}/zeutica/editcliente"    
    
    # Botón para cargar clientes con callback
    def cargar_clientes_df():
    
        try:
            response = requests.get(f"{API_BASE_URL}/zeutica/clientes")
            if response.status_code == 200:
                # 1. Convertimos la lista de la API directamente a DataFrame plano
                raw_json = response.json()
                df = pd.json_normalize(raw_json) 
            
                # Guardamos el DataFrame en el estado de la sesión
                st.session_state.clientes_data = df
                st.session_state.mostrar_editor = True
                st.success("¡Lista de clientes cargada!")
            else:
                st.error(f"Error al obtener clientes: {response.status_code}")
        except Exception as e:
            st.error(f"Falla de conexión: {e}")

# --- INTERFAZ ---
st.divider()
st.subheader("📋 Gestión de Clientes Existentes")

# BOTÓN ÚNICO PARA MOSTRAR/CARGAR
if st.button("👁️ Ver Clientes", type="secondary", key="btn_ver_principal"):
    cargar_clientes_df()

# Solo mostramos el editor si se ha presionado el botón y hay datos
if st.session_state.mostrar_editor and st.session_state.clientes_data is not None:
    st.info("💡 Puedes editar las celdas directamente. Al terminar, presiona 'Enviar Cambios'.")
    
    # 2. El data_editor ahora recibe un DataFrame, por lo que devolverá un DataFrame
    edited_df = st.data_editor(
        st.session_state.clientes_data,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        key="editor_tabla_clientes"
    )

    st.divider()
    
    # 3. Botón para enviar SÓLO las modificaciones
    if st.button("✅ Guardar Cambios", type="primary"):
        
        # Extraemos el registro exacto de lo que el usuario editó
        estado_editor = st.session_state["editor_tabla_clientes"]
        filas_modificadas = estado_editor.get("edited_rows", {})
        
        if not filas_modificadas:
            st.warning("⚠️ No se detectaron modificaciones en los datos.")
        else:
            try:
                with st.spinner("Actualizando clientes..."):
                    exitosos = 0
                    errores = []
                    
                    # Iteramos SOLO sobre los índices de las filas que sufrieron cambios
                    for idx in filas_modificadas.keys():
                        # Extraemos la fila completa y actualizada usando su índice
                        fila_actualizada = edited_df.iloc[idx]
                        cliente_id = fila_actualizada.get('id')
                        
                        # Blindaje por si se intenta editar una fila sin ID válido
                        if pd.isna(cliente_id) or cliente_id == "":
                            continue
                        
                        # Convertimos a diccionario y limpiamos valores NaN para evitar errores JSON
                        payload = {k: (None if pd.isna(v) else v) for k, v in fila_actualizada.to_dict().items()}
                        
                        # Petición POST a tu endpoint de Zeutica
                        res = requests.post(url_editar, json=payload)
                        
                        if res.status_code == 200:
                            exitosos += 1
                        else:
                            errores.append(f"ID {cliente_id}: {res.status_code}")
                            
                    # --- MANEJO DE MENSAJES ---
                    if errores:
                        st.error("❌ Ocurrieron errores al guardar:")
                        for err in errores:
                            st.write(f"  - {err}")
                            
                    if exitosos > 0:
                        st.success(f"✅ {exitosos} cliente(s) actualizado(s) correctamente.")
                        # Sincronizamos los datos base para que el editor "limpie" el historial de cambios
                        st.session_state.clientes_data = edited_df
                        
            except Exception as e:
                st.error(f"Error crítico en la comunicación con el servidor: {e}")