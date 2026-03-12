import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import date
import calendar
import logging
import time

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE_URL = st.session_state.ip

toks = {
            "Authorization": f"Bearer {st.session_state.token}"
        }

def obtener_ventas_mes():
    """
    Obtiene las ventas del mes actual desde el backend.
    Retorna un DataFrame con los datos o None si hay error.
    Sin caché para garantizar datos frescos.
    """
    try:
        # Obtener primer y último día del mes actual
        hoy = date.today()
        primer_dia = hoy.replace(day=1)
        
        # Último día del mes usando calendar
        ultimo_dia_num = calendar.monthrange(hoy.year, hoy.month)[1]
        ultimo_dia = hoy.replace(day=ultimo_dia_num)
        
        # Formatos de fecha para la API
        f1 = primer_dia.strftime("%Y-%m-%d")
        f2 = ultimo_dia.strftime("%Y-%m-%d")
        
        st.write(f"_Datos del {primer_dia.strftime('%d/%m/%Y')} al {ultimo_dia.strftime('%d/%m/%Y')}_")
        
        # Realizar solicitud al backend
        url = f"{API_BASE_URL}/zeutica/ventas/{f1}/{f2}"
        respuesta = requests.get(url, headers= toks ,timeout=10)
        
        if respuesta.status_code == 200:
            datos = respuesta.json()
            if datos:
                df = pd.DataFrame(datos)
                logger.info(f"✅ Se obtuvieron {len(df)} registros de ventas")
                return df
            else:
                st.warning("⚠️ No hay datos de ventas para este período")
                return None
        else:
            st.error(f"❌ Error del servidor: {respuesta.status_code}")
            logger.error(f"Error en API: {respuesta.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("❌ Tiempo de conexión agotado. Intenta más tarde.")
        logger.error("Timeout en conexión al API")
        return None
    except requests.exceptions.ConnectionError:
        st.error("❌ No se puede conectar al servidor. Verifica que el backend esté ejecutándose.")
        logger.error("Error de conexión al API")
        return None
    except Exception as e:
        st.error(f"❌ Error inesperado: {str(e)}")
        logger.error(f"Error general: {e}")
        return None

def calcular_metricas(df):
    """
    Calcula las métricas principales del dashboard.
    Retorna un diccionario con: total_ventas, utilidad, top_productos, plataforma_top
    """
    if df is None or df.empty:
        return None
    
    metricas = {}
    
    # 1. Total de ventas (suma de cantidades)
    metricas['total_ventas'] = df['cantidad'].sum()
    
    # 2. Utilidad (estimada como 25% - ajustable según tu modelo de negocio)
    # Si el backend trae una columna 'utilidad', usa eso en su lugar
    if 'utilidad' in df.columns:
        metricas['utilidad'] = df['utilidad'].sum()
        metricas['utilidad_pct'] = (metricas['utilidad'] / (df['cantidad'].sum() or 1)) * 100
    else:
        # Estimación por defecto (ajustable)
        metricas['utilidad'] = metricas['total_ventas'] * 0.25
        metricas['utilidad_pct'] = 25.0
    
    # 3. Top 5 productos más vendidos
    metricas['top_productos'] = df['producto'].value_counts().head(5)
    
    # 4. Plataforma que más vende
    metricas['plataforma_top'] = df['plataforma'].value_counts()
    metricas['plataforma_max'] = df['plataforma'].value_counts().idxmax() if 'plataforma' in df.columns else "N/A"
    
    return metricas

def mostrar_dashboard_gerencia():
    st.title("📊 Panel de Control de Gerencia")
    st.markdown("### Análisis de Ventas y Métricas Clave - Mes Actual")

    # Obtener datos del backend
    with st.spinner("Cargando datos del servidor..."):
        df_ventas = obtener_ventas_mes()
    
    if df_ventas is None or df_ventas.empty:
        st.info("📭 No hay datos disponibles para mostrar. Asegúrate de que el servidor esté ejecutándose.")
        return
    
    # Calcular métricas
    metricas = calcular_metricas(df_ventas)
    
    if metricas is None:
        st.error("No se pudieron procesar los datos.")
        return

    # ============ FILA 1: MÉTRICAS PRINCIPALES (KPIs) ============
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📦 Cantidad Vendida",
            f"{int(metricas['total_ventas']):,}",
            help="Total de unidades vendidas en el mes"
        )
    
    with col2:
        st.metric(
            "💰 Utilidad Estimada",
            f"{metricas['utilidad']:,.0f}",
            delta=f"{metricas['utilidad_pct']:.1f}%",
            help="Utilidad calculada del mes"
        )
    
    with col3:
        st.metric(
            "🌍 Principal Plataforma",
            metricas['plataforma_max'],
            f"{metricas['plataforma_top'].iloc[0]} ventas",
            help="Plataforma con más volumen de ventas"
        )
    
    with col4:
        num_transacciones = len(df_ventas)
        promedio = metricas['total_ventas'] / (num_transacciones or 1)
        st.metric(
            "📊 Ticket Promedio",
            f"{promedio:.0f} unidades",
            help="Promedio de cantidad por transacción"
        )

    st.divider()

    # ============ FILA 2: GRÁFICOS DE ANÁLISIS ============
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("🏆 Top 5 Productos Más Vendidos")
        df_top = pd.DataFrame({
            "Producto": metricas['top_productos'].index,
            "Cantidad": metricas['top_productos'].values
        })
        fig_bar = px.bar(
            df_top,
            x="Cantidad",
            y="Producto",
            orientation="h",
            color="Cantidad",
            color_continuous_scale="Blues",
            template="plotly_white"
        )
        fig_bar.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        st.subheader("🎯 Ventas por Plataforma")
        df_plataforma = pd.DataFrame({
            "Plataforma": metricas['plataforma_top'].index,
            "Ventas": metricas['plataforma_top'].values
        })
        fig_pie = px.pie(
            df_plataforma,
            values="Ventas",
            names="Plataforma",
            hole=0.4,
            template="plotly_white"
        )
        fig_pie.update_layout(height=350)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()

    # ============ TABLA DE DATOS DETALLADA ============
    with st.expander("📋 Ver datos detallados de ventas"):
        st.dataframe(df_ventas, use_container_width=True, hide_index=True)


# Creamos el contenedor vacío
placeholder = st.empty()

# Usamos el contenedor para mostrar algo temporal
with placeholder.container():
    st.success("🔓 Acceso verificado para: Gerencia")
    st.info("Cargando métricas confidenciales...")
    
    # Simulamos una carga de 3 segundos
    bar = st.progress(0)
    for i in range(100):
        time.sleep(0.02)
        bar.progress(i + 1)

# Borramos todo lo anterior para que no ocupe espacio
placeholder.empty()

mostrar_dashboard_gerencia()