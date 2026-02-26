import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import requests

# --- CONFIGURACIÓN INICIAL ---
API_BASE_URL = "http://10.0.9.227:8090"

# // FUNCIONES PARA CONSULTAR DB //
def obtener_clientes():
    try:
        res_clientes = requests.get(f"{API_BASE_URL}/zeutica/clientes")
        if res_clientes.status_code == 200:
            clientes = res_clientes.json()
            return {c['nombre']: c for c in clientes}
    except:
        pass
    return {}

def obtener_inventario():
    try:
        res_inventario = requests.get(f"{API_BASE_URL}/zeutica/productos")
        if res_inventario.status_code == 200:
            inventario = res_inventario.json()
            return {f"{item['sku']} ({item['nombre']})": item for item in inventario}
    except:
        pass
    return {}

def obtener_siguiente_codigo():
    try:
        res = requests.get(f"{API_BASE_URL}/zeutica/cotizaciones/nuevo-codigo")
        return res.json().get("nuevo_codigo")
    except:
        return "ZTC-ERR"

# Inicializamos estados
if 'items_cotizacion' not in st.session_state: st.session_state.items_cotizacion = []
if 'mostrar_formCotizacion' not in st.session_state: st.session_state.mostrar_formCotizacion = False
if "mostrar_form" not in st.session_state: st.session_state.mostrar_form = False
if "codigo_actual" not in st.session_state: st.session_state.codigo_actual = "000"

# --- CLASE PDF PROFESIONAL (DISEÑO ZEUTICA) ---
class PDF(FPDF):
    def header(self):
        try:
            self.image('logo.png', 10, 8, 40) 
        except:
            pass
            
        self.set_font('Arial', '', 8)
        self.set_xy(10, 25)
        self.multi_cell(90, 4, 
            "Domicilio: Reporteros 44, Col. Los Periodistas, CP: 45078, Zapopan, Jalisco.\n"
            "Sitio Web: https://zeutica.com\n"
            "Teléfono: 33-1299-5688\n"
            "E-mail: ventas1@zeutica.com\n"
            "Asesor: Cecilia Parra", 0, 'L')

        self.set_xy(110, 10)
        self.set_font('Arial', 'B', 16)
        self.cell(90, 10, f'COTIZACION {st.session_state.codigo_actual}', 0, 1, 'R')
        
        self.set_font('Arial', 'B', 9)
        self.set_xy(140, 25)
        fecha_hoy = datetime.now().strftime('%d/%m/%Y')
        self.cell(30, 6, "Fecha:", 1, 0, 'L')
        self.cell(30, 6, fecha_hoy, 1, 1, 'R')
        self.set_x(140)
        self.cell(30, 6, "Válido Hasta:", 1, 0, 'L')
        self.cell(30, 6, "7 Días", 1, 1, 'R')

    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'B', 8)
        self.cell(0, 5, "Si tienes alguna pregunta por favor contáctanos", 0, 1, 'C')
        self.set_font('Arial', '', 8)
        self.cell(0, 5, "Telf: 33-1299-5688 / E-mail: ventas1@zeutica.com", 0, 1, 'C')
        self.cell(0, 5, f'Página {self.page_no()}', 0, 0, 'R')

def generar_pdf_zeutica(datos_cliente, items, forma_pago, comentario_seleccionado, costo_envio):
    pdf = PDF()
    pdf.add_page()
    
    pdf.set_y(55)
    pdf.set_fill_color(0, 74, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 8, "   CLIENTE", 0, 1, 'L', 1)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 9)
    pdf.ln(2)
    
    def fila_cliente(etiqueta, valor):
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(25, 6, etiqueta, 0, 0)
        pdf.set_font('Arial', '', 9)
        pdf.cell(0, 6, valor, 0, 1)

    fila_cliente("NOMBRE CLIENTE:", datos_cliente.get('empresa', 'N/A'))
    fila_cliente("EMPRESA:", datos_cliente.get('empresa', 'N/A'))
    fila_cliente("ATENCION:", datos_cliente.get('atencion', 'N/A'))
    fila_cliente("EMAIL:", datos_cliente.get('email', 'N/A'))
    fila_cliente("DOMICILIO:", datos_cliente.get('domicilio', 'N/A'))
    fila_cliente("TELEFONO:", datos_cliente.get('telefono', 'N/A'))
    pdf.ln(5)

    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Arial', 'B', 9)
    header_w = [30, 80, 20, 30, 30] 
    headers = ["CÓDIGO / SKU", "DESCRIPCIÓN", "CANT", "PRECIO", "TOTAL"]
    
    for i, h in enumerate(headers):
        pdf.cell(header_w[i], 8, h, 1, 0, 'C', 1)
    pdf.ln()

    pdf.set_font('Arial', '', 8)
    subtotal_gral = 0
    
    for item in items:
        precio_u = item['precio']
        cantidad = item['cantidad']
        total_linea = precio_u * cantidad
        texto_completo = item['producto']
        try:
            sku = texto_completo.split(' (')[0]
            nombre = texto_completo.split(' (')[1].replace(')', '')
        except:
            sku = "N/A"
            nombre = texto_completo

        x_ini = pdf.get_x()
        y_ini = pdf.get_y()
        
        pdf.set_xy(x_ini + 30, y_ini)
        pdf.multi_cell(80, 6, nombre, 1, 'L')
        y_fin = pdf.get_y()
        alto_fila = y_fin - y_ini
        
        pdf.set_xy(x_ini, y_ini)
        pdf.cell(30, alto_fila, sku, 1, 0, 'C')
        pdf.set_xy(x_ini + 110, y_ini)
        pdf.cell(20, alto_fila, str(cantidad), 1, 0, 'C')
        pdf.cell(30, alto_fila, f"${precio_u:,.2f}", 1, 0, 'R')
        pdf.cell(30, alto_fila, f"${total_linea:,.2f}", 1, 1, 'R')
        
        subtotal_gral += total_linea

    iva = subtotal_gral * 0.16
    total_neto = subtotal_gral + costo_envio + iva
    
    pdf.ln(2)
    x_totales = 140
    pdf.set_x(x_totales)
    
    def fila_total(texto, valor, negrita=False):
        pdf.set_x(x_totales)
        pdf.set_font('Arial', 'B' if negrita else '', 9)
        pdf.cell(30, 6, texto, 1, 0, 'R', 1 if negrita else 0)
        pdf.cell(30, 6, f"${valor:,.2f}", 1, 1, 'R', 1 if negrita else 0)

    fila_total("Sub-Total:", subtotal_gral)
    fila_total("Costo del Envio:", costo_envio)
    fila_total("IVA (16%):", iva)
    fila_total("TOTAL:", total_neto, negrita=True)

    pdf.set_y(pdf.get_y() + 5)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, "TÉRMINOS Y CONDICIONES", 0, 1, 'L')
    
    pdf.set_font('Arial', '', 8)
    pdf.multi_cell(0, 5, 
        f"1. FORMA DE PAGO: {forma_pago.upper()}\n"
        "2. COTIZACIÓN EN: PESO MEXICANO (MXN)\n"        
        "3. PRECIOS SUJETOS A CAMBIO SIN PREVIO AVISO.", 0, 'L\n'
        f"4. COMENTARIOS: {comentario_seleccionado}")

    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- INTERFAZ STREAMLIT ---
def abrir_formulario(): st.session_state.mostrar_formCotizacion = True
def abrir_form(): st.session_state.mostrar_form = True
def cerrar_form(): st.session_state.mostrar_form = False

if st.session_state.mostrar_formCotizacion:
    if 'codigo_actual' not in st.session_state or st.session_state.codigo_actual == "000":
        st.session_state.codigo_actual = obtener_siguiente_codigo()

    with st.expander(f"📝 Generador de Cotizaciones - {st.session_state.codigo_actual}", expanded=True):
        st.info(f"📋 Folio de Cotización: **{st.session_state.codigo_actual}**")

st.button("Nueva Cotización ➕", on_click=abrir_formulario)

if st.session_state.mostrar_formCotizacion:
    with st.expander("📝 Generador de Cotizaciones", expanded=True):
        
        st.markdown("### 1. Datos del Cliente")
        c1, c2 = st.columns(2)

        with c1:
            diccionario_clientes = obtener_clientes()
            opciones = list(diccionario_clientes.keys())
            seleccion_nombre = st.selectbox("Selecciona Cliente/Empresa", opciones)
            datos_cliente = diccionario_clientes.get(seleccion_nombre, {})

            empresa_nombre = st.text_input("Empresa", value=datos_cliente.get('empresa', ''), disabled=True)
            atencion = st.text_input("Atención", value=datos_cliente.get('atencion', ''), disabled=False)            
            

        with c2:
            telefono = st.text_input("Teléfono", value=datos_cliente.get('telefono', ''), disabled=True)
            domicilio = st.text_area("Domicilio", value=datos_cliente.get('direccion', ''), height=108, disabled=True)
            email = st.text_input("email", value=datos_cliente.get('email', ''), disabled=True)

        st.markdown("### 2. Productos y Precios")
        inventario = obtener_inventario()   
            
        col_prod, col_lista = st.columns([1, 1])
        
        with col_prod:
            # Seleccionamos producto y lista de precios de manera dinámica (sin st.form)
            sel_prod = st.selectbox("Producto:", list(inventario.keys()) if inventario else [])
            
            # --- NUEVA LÓGICA DE LISTA DE PRECIOS ---
            tipo_precio = st.radio(
                "Selecciona Lista de Precios:", 
                ["Precio A", "Precio B", "Precio C"], 
                horizontal=True
            )
            
            cc1, cc2 = st.columns(2)
            cant = cc1.number_input("Cantidad", 1, 1000, 1)
            
            # Asignamos el precio base dependiendo de la selección en el radio button
            p_base = 0.0
            if sel_prod: 
                prod_data = inventario[sel_prod]
                if tipo_precio == "Precio A":
                    p_base = float(prod_data.get('precio', 0.0))
                elif tipo_precio == "Precio B":
                    p_base = float(prod_data.get('precio_2', 0.0))
                elif tipo_precio == "Precio C":
                    p_base = float(prod_data.get('precio_3', 0.0))
                    
            precio = cc2.number_input("Precio a aplicar", value=p_base, format="%.2f")
                
            if st.button("Agregar Producto 🛒", type="primary"):
                st.session_state.items_cotizacion.append({
                    "producto": sel_prod, "cantidad": cant, "precio": precio, "total": cant * precio
                })
                st.rerun()

        with col_lista:
            # Cálculos de totales
            subtotal = sum(item.get('total', 0) for item in st.session_state.items_cotizacion)
            iva = subtotal * 0.16
            total_general = subtotal + iva
            limite_envio = 7000 * 1.16 
            costo_envio = 0.0

            if total_general > limite_envio:
                sku_envio = "ENV-GRATIS-ZEU"
                costo_envio = 0.0
            else:
                sku_envio = "ENV-ESTANDAR-01"
                costo_envio = 300.00

            if st.session_state.items_cotizacion:
                df = pd.DataFrame(st.session_state.items_cotizacion)
                st.dataframe(df, use_container_width=True, hide_index=True)
        
                st.markdown("---")
                t1, t2 = st.columns([2, 1])
        
                with t2:
                    st.write(f"**Subtotal:** ${subtotal:,.2f}")
                    st.write(f"**IVA (16%):** ${iva:,.2f}")
            
                    if costo_envio == 0:
                        st.success(f"✅ Envío Gratis ({sku_envio})")
                    else:
                        st.warning(f"🚚 Envío: ${costo_envio:,.2f} ({sku_envio})")
            
                    total_final = total_general + costo_envio
                    st.subheader(f"TOTAL: ${total_final:,.2f}")

                if st.button("Limpiar Lista 🗑️"):
                    st.session_state.items_cotizacion = []
                    st.rerun()
           
        st.markdown("### 3. Condiciones Finales")
        f1, f2 = st.columns(2)
            
        opciones_comentarios = [
            "ENVIO GRATIS EN COMPRAS MAYORES A $7000.00 MAS IVA, TIEMPO DE ENTREGA DE 4-7 DIAS HABILES..",                      
            "EL ENVIO SE REALIZARA POR PAQUETERIA PAQUETE EXPRESS EN CASO DE REQUERIR UNA PAQUETERIA EN PARTICULAR ESTA SE COTIZARA DE MANERA ADICIONAL.",
            "OTROS..."            
        ]
            
        forma_pago = f1.text_input("Forma de Pago", value="CONTADO")        
        comentario = f2.selectbox("Comentarios / Envío", opciones_comentarios)

        if comentario == "OTROS...":
            comentario_final = st.text_area("Escribe el comentario personalizado:")
        else:
            comentario_final = comentario

        if st.session_state.items_cotizacion and empresa_nombre:
            datos_cliente = {
                "empresa": empresa_nombre, "atencion": atencion, "email": email, 
                "domicilio": domicilio, "telefono": telefono
            }
                
            pdf_bytes = generar_pdf_zeutica(datos_cliente, st.session_state.items_cotizacion, forma_pago, comentario_final, costo_envio)
                
            if st.download_button(
                    "📄 Descargar y Registrar Cotización",
                    data=pdf_bytes,
                    file_name=f"Cotizacion_{st.session_state.codigo_actual}_{seleccion_nombre}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                ):
                    payload = {
                        "codigo": st.session_state.codigo_actual,
                        "empresa": empresa_nombre,                        
                        "atencion": atencion,
                        "email": email,
                        "domicilio": domicilio,
                        "telefono": telefono,
                        "subtotal": subtotal,
                        "iva": iva,
                        "total": total_final,
                        "forma_pago": forma_pago,
                        "comentarios": comentario_final,
                        "items": [
                            {
                            "sku": i['producto'].split(' (')[0],
                            "nombre_producto": i['producto'].split(' (')[1].replace(')', ''),
                            "cantidad": i['cantidad'],
                            "precio_unitario": i['precio'],
                            "total_linea": i['total']
                            } for i in st.session_state.items_cotizacion
                        ]
                    }
        
                    res = requests.post(f"{API_BASE_URL}/zeutica/cotizaciones/guardar", json=payload)
                    if res.status_code == 200:
                        st.success(f"✅ Cotización {st.session_state.codigo_actual} guardada.")
                        st.session_state.items_cotizacion = []
                        st.session_state.codigo_actual = "000"
                    else:
                        st.error("❌ Error al guardar en la base de datos.")

        elif not empresa_nombre:
            st.warning("⚠️ Debes ingresar al menos el nombre de la Empresa.")

import pandas as pd

# --- SECCIÓN DE CONSULTA ---
st.button("Consulta Cotización ➕", on_click=abrir_form, key="btn_consulta_coti_principal")

if st.session_state.mostrar_form:
    with st.expander("📝 Consultor de Cotizaciones", expanded=True):
        st.info("📋 Consulta de cotizaciones activas en el sistema. Agrega el código de factura y presiona Guardar.")
        try:
            coti = requests.get(f"{API_BASE_URL}/zeutica/consulta/cotizacion")
            if coti.status_code == 200:
                datos = coti.json().get("cotizaciones", [])
                if datos:
                    # 1. Convertimos los datos a un DataFrame de Pandas
                    df = pd.DataFrame(datos)
                    
                    # 2. Si la columna 'relacion_factura' no viene de la DB, la creamos vacía
                    if "relacion_factura" not in df.columns:
                        df["relacion_factura"] = ""
                        
                    # 3. Identificamos todas las columnas originales para bloquearlas
                    columnas_bloqueadas = [col for col in df.columns if col != "relacion_factura"]
                    
                    # 4. Mostramos el editor de datos interactivo
                    df_editado = st.data_editor(
                        df, 
                        use_container_width=True, 
                        hide_index=True,
                        disabled=columnas_bloqueadas, # Esto hace que SOLO relacion_factura sea editable
                        key="editor_cotizaciones"
                    )
                    
                    # 5. Botón para enviar los datos a la base de datos
                    if st.button("Guardar Relación de Facturas 💾", type="primary"):
                        # Filtramos el dataframe para obtener solo las filas donde escribieron algo
                        modificados = df_editado[df_editado["relacion_factura"].str.strip() != ""]
                        
                        if not modificados.empty:
                            # Convertimos a diccionario solo las columnas necesarias
                            # NOTA: Cambia "codigo" por el nombre exacto de la columna que identifica tu cotización (ej. "id", "folio")
                            payload = modificados[["codigo_cotizacion", "relacion_factura"]].to_dict(orient="records")
                            
                            res_update = requests.post(f"{API_BASE_URL}/zeutica/relacionFactura", json=payload)
                            
                            if res_update.status_code == 200:
                                st.success("✅ ¡Facturas vinculadas correctamente en la base de datos!")
                                st.rerun() # Recarga para limpiar la vista
                            else:
                                st.error("❌ Error al guardar en el servidor.")
                        else:
                            st.warning("⚠️ No has ingresado ninguna factura nueva para guardar.")

                else:
                    st.warning("No se encontraron registros en la base de datos.")
            else:
                st.error(f"Error del servidor: {coti.status_code}")
        except Exception as e:
            st.error(f"⚠️ Error de comunicación con la API: {e}")
        
        st.button("Cerrar Consultor", on_click=cerrar_form, key="btn_cerrar_coti")
