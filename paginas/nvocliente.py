import streamlit as st
import requests

def app():
    st.title("📂 Alta de Clientes")
    st.markdown("Ingresa los datos del cliente para registrarlo en la base de datos de AWS.")
    
    # Importante: No uses 'localhost' aquí si la API está en la nube
    API_BASE_URL = "http://3.151.25.133:8090/zeutica/clientenuevo"

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
                    respuesta = requests.post(API_BASE_URL, json=datos_cliente)

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

    submit_button = st.button("Ver Clientes")
    url_enviar = "http://3.151.25.133:8090/zeutica/clientes"
    
    if submit_button:
        
        try:
            # Indicador de carga (Spinner)
            with st.spinner('Buscando en la base de datos...'):
                response = requests.get(url_enviar)
                
            # 3. Manejo de la respuesta
            if response.status_code == 200:
                data = response.json()                
                st.success("¡Lista de Clientes Encontrada!")
                
                # Mostramos los datos de forma estética
                st.write("### Detalles de los Clientes")
                #st.json(data)  O puedes usar st.table(data) si es una lista
                st.dataframe(data)                

            elif response.status_code == 404:
                st.warning("No se encontró ningún cliente")
            else:
                st.error(f"Error de la API: Código {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            st.error(f"Error de conexión: {e}")
    else:
        st.info("Por favor, consulta que tengas al cliente dado de alta.")
        pass