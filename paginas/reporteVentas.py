import streamlit as st
import requests
from datetime import datetime

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

# ====== SECCIÓN DE WEB SCRAPING ======
st.header("Scraping de Productos - ZVG")
st.info("Consulta productos desde https://zvg.es/productos/")

scrap_button = st.button("Obtener Productos ZVG")

if scrap_button:
    try:
        with st.spinner("Realizando scraping..."):
            # Importar BeautifulSoup
            from bs4 import BeautifulSoup
            import pandas as pd
            
            # URL a scraping
            url = "https://www.espn.com.mx/beisbol/mlb/estadisticas/jugador/_/tabla/batting/ordenar/atBats/dir/desc"
            
            # Headers para evitar bloqueos
            headers = {
                'User-Agent': '(windows NT 10.0; Win64; x64)',
                 "Accept-Language": "es-MX,es;q=0.9"
            }
            
            # Realizar petición web            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parsear HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraer productos (ajusta los selectores según la estructura del sitio)
            productos = []
            
            # Buscar elementos de producto (estos selectores pueden necesitar ajuste)
            product_elements = soup.find_all('div', class_='product')
            
            if not product_elements:
                # Alternativa: buscar por otra estructura común
                product_elements = soup.find_all('article', class_='product-item')
            
            if not product_elements:
                # Otra alternativa más genérica
                product_elements = soup.find_all('li', class_='product')
            
            for element in product_elements:
                try:
                    # Extraer nombre
                    nombre = element.find('h2', class_='product-name')
                    nombre = nombre.text.strip() if nombre else 'N/A'
                    
                    # Extraer precio
                    precio = element.find('span', class_='price')
                    precio = precio.text.strip() if precio else 'N/A'
                    
                    # Extraer descripción o categoría
                    descripcion = element.find('p', class_='description')
                    descripcion = descripcion.text.strip() if descripcion else 'N/A'
                    
                    # Extraer enlace
                    enlace = element.find('a', href=True)
                    enlace = enlace['href'] if enlace else 'N/A'
                    
                    productos.append({
                        'nombre': nombre,
                        'precio': precio,
                        'descripcion': descripcion,
                        'enlace': enlace
                    })
                
                except Exception as e:
                    st.warning(f"Error extrayendo elemento: {e}")
                    continue
            
            # Crear DataFrame
            if productos:
                df_productos = pd.DataFrame(productos)
                
                st.success(f"✅ Se extrajeron {len(df_productos)} productos")
                
                # Mostrar tabla
                st.dataframe(
                    df_productos,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "nombre": st.column_config.TextColumn("Producto", width=250),
                        "precio": st.column_config.TextColumn("Precio"),
                        "descripcion": st.column_config.TextColumn("Descripción", width=300),
                        "enlace": st.column_config.LinkColumn("Enlace", display_text="Ver producto")
                    }
                )
                
                # Descargar como CSV
                csv = df_productos.to_csv(index=False)
                st.download_button(
                    label="Descargar como CSV",
                    data=csv,
                    file_name="productos_zvg.csv",
                    mime="text/csv"
                )
            else:
                st.warning("⚠️ No se encontraron productos. Los selectores CSS pueden haber cambiado en el sitio.")
                st.info("Tip: Inspecciona el sitio web y proporciona los selectores CSS correctos.")
    
    except requests.exceptions.Timeout:
        st.error("❌ Timeout: El sitio tardó demasiado en responder.")
    except requests.exceptions.ConnectionError:
        st.error("❌ Error de conexión: No se pudo acceder al sitio.")
    except Exception as e:
        st.error(f"❌ Error durante el scraping: {e}")

