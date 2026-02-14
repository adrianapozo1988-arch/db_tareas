import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import zipfile

# Configuración de la página
st.set_page_config(page_title="War Room Táctico", layout="wide")

# --- BLOQUE DE SEGURIDAD (Login) ---
def check_password():
    """Retorna True si el usuario ingresó la clave correcta."""
    def password_entered():
        if st.session_state["password"] == "clave_2026": 
            st.session_state["password_correct"] = True
            del st.session_state["password"]  
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("🔐 Ingresa la contraseña de acceso:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("🔐 Ingresa la contraseña de acceso:", type="password", on_change=password_entered, key="password")
        st.error("❌ Contraseña incorrecta")
        return False
    else:
        return True

if not check_password():
    st.stop()

# Título Principal
st.title("WAR ROOM TÁCTICO: RECUPERACIÓN & EJECUCIÓN")
st.markdown("---")

# --- 1. CARGA DE DATOS INTELIGENTE ---
@st.cache_data
def load_data():
    archivos_en_carpeta = os.listdir('.')
    archivo_encontrado = None
    
    # Prioridad ZIP
    for archivo in archivos_en_carpeta:
        if "Tareas" in archivo and archivo.endswith(".zip"):
            archivo_encontrado = archivo
            break
            
    if not archivo_encontrado:
        for archivo in archivos_en_carpeta:
            if "Tareas" in archivo and (archivo.endswith(".xlsx") or archivo.endswith(".csv")):
                archivo_encontrado = archivo
                break
    
    if archivo_encontrado:
        try:
            if archivo_encontrado.endswith('.zip'):
                with zipfile.ZipFile(archivo_encontrado, 'r') as z:
                    for nombre_interno in z.namelist():
                        if nombre_interno.endswith('.csv'):
                            return pd.read_csv(z.open(nombre_interno))
                        elif nombre_interno.endswith('.xlsx'):
                            return pd.read_excel(z.open(nombre_interno), engine='openpyxl')
            elif archivo_encontrado.endswith('.csv'):
                return pd.read_csv(archivo_encontrado)
            else:
                return pd.read_excel(archivo_encontrado, engine='openpyxl')
        except Exception as e:
            st.error(f"Error leyendo archivo: {e}")
            return None
    else:
        return None

df = load_data()

if df is None:
    st.error("❌ ERROR: No encuentro tu archivo de datos.")
    st.stop()

# --- 2. BARRA LATERAL (FILTROS) ---
st.sidebar.header("🎯 Filtros Operativos")

if 'Mes_Nombre' in df.columns:
    meses_ordenados = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                       'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    meses_disponibles = [m for m in meses_ordenados if m in df['Mes_Nombre'].unique()]
    mes_seleccionado = st.sidebar.multiselect("Selecciona Mes:", meses_disponibles, default=meses_disponibles)
else:
    st.error("Falta columna 'Mes_Nombre'")
    st.stop()

if 'Macrocanal' in df.columns:
    canales_disponibles = df['Macrocanal'].unique()
    canal_seleccionado = st.sidebar.multiselect("Selecciona Macrocanal:", canales_disponibles, default=canales_disponibles)
else:
    st.error("Falta columna 'Macrocanal'")
    st.stop()

df_filtered = df[
    (df['Mes_Nombre'].isin(mes_seleccionado)) & 
    (df['Macrocanal'].isin(canal_seleccionado))
]

# --- 3. KPIs PRINCIPALES ---
col1, col2, col3, col4 = st.columns(4)

total_visitas = df_filtered['VALIDADA GEO'].sum() if 'VALIDADA GEO' in df_filtered.columns else 0
total_ventas = df_filtered['VALIDADA VENTA'].sum() if 'VALIDADA VENTA' in df_filtered.columns else 0
tasa_conversion = (total_ventas / total_visitas * 100) if total_visitas > 0 else 0
total_tareas_cumplidas = df_filtered['VALIDADA FINAL'].sum() if 'VALIDADA FINAL' in df_filtered.columns else 0

col1.metric("📍 Visitas (Esfuerzo)", f"{total_visitas:,.0f}")
col2.metric("💰 Ventas (Éxito)", f"{total_ventas:,.0f}")
col3.metric("📈 Tasa Conversión", f"{tasa_conversion:.1f}%")
col4.metric("✅ Tareas Cumplidas", f"{total_tareas_cumplidas:,.0f}")

st.markdown("---")

# --- 4. PESTAÑAS DE ANÁLISIS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Visión General", "🏆 Fuerza de Ventas", "🛒 Clientes (Base)", "📦 Portafolio", "⚡ Recuperación (Mes Caído)"])

with tab1:
    st.subheader("Rendimiento por Macrocanal")
    macro_data = df_filtered.groupby('Macrocanal')[['VALIDADA GEO', 'VALIDADA VENTA']].sum().reset_index()
    
    fig_macro = go.Figure()
    fig_macro.add_trace(go.Bar(x=macro_data['Macrocanal'], y=macro_data['VALIDADA GEO'], name='Visitas', marker_color='skyblue'))
    fig_macro.add_trace(go.Bar(x=macro_data['Macrocanal'], y=macro_data['VALIDADA VENTA'], name='Ventas', marker_color='salmon'))
    fig_macro.update_layout(barmode='group', height=400)
    st.plotly_chart(fig_macro, use_container_width=True)
    
    st.markdown("---")
    
    st.subheader("🔥 Top 10 Subcanales (Por Volumen de Visita)")
    if 'Subcanal' in df_filtered.columns:
        sub_perf = df_filtered.groupby('Subcanal')[['VALIDADA GEO', 'VALIDADA VENTA']].sum().reset_index()
        sub_perf['Conversion_Rate'] = (sub_perf['VALIDADA VENTA'] / sub_perf['VALIDADA GEO']).fillna(0) * 100
        sub_perf_top10 = sub_perf.sort_values('VALIDADA GEO', ascending=False).head(10)
        
        fig_sub = px.bar(
            sub_perf_top10, x='Subcanal', y='Conversion_Rate', color='Conversion_Rate',
            title="Efectividad en los 10 Subcanales más visitados",
            text_auto='.1f', color_continuous_scale='Magma'
        )
        st.plotly_chart(fig_sub, use_container_width=True)

with tab2:
    st.header("Matriz de Desempeño: Carga vs Efectividad")
    st.markdown("*Solo se muestra el gráfico de dispersión para identificar oportunidades.*")
    
    if 'Piramide Ventas.Vendedor' in df_filtered.columns:
        vend_data = df_filtered.groupby('Piramide Ventas.Vendedor').agg({
            'Pregunta': 'count', 'VALIDADA FINAL': 'sum', 'VALIDADA GEO': 'sum', 'VALIDADA VENTA': 'sum'
        }).reset_index()
        
        vend_data['Pct_Cumplimiento'] = (vend_data['VALIDADA FINAL'] / vend_data['Pregunta'] * 100).fillna(0)
        
        def asignar_cuadrante(pct):
            if pct < 25: return 'Crítico (<25%)'
            elif pct < 50: return 'Bajo (25-50%)'
            elif pct < 75: return 'Medio (50-75%)'
            else: return 'Alto (>75%)'
            
        vend_data['Cuadrante'] = vend_data['Pct_Cumplimiento'].apply(asignar_cuadrante)
        
        # ÚNICA GRÁFICA: SCATTER PLOT
        fig_scatter = px.scatter(
            vend_data, x='Pregunta', y='Pct_Cumplimiento', color='Cuadrante', size='VALIDADA GEO',
            hover_name='Piramide Ventas.Vendedor',
            title="Matriz de Vendedores: Eje X = Carga (Tareas) | Eje Y = Cumplimiento %",
            color_discrete_map={'0-25% (Crítico)':'red', '25-50% (Bajo)':'orange', '50-75% (Medio)':'yellow', '75-100% (Alto)':'green'},
            height=600
        )
        # Líneas de referencia estratégicas
        fig_scatter.add_hline(y=50, line_dash="dash", line_color="black", annotation_text="Meta Mínima 50%")
        fig_scatter.add_vline(x=vend_data['Pregunta'].mean(), line_dash="dash", line_color="gray", annotation_text="Carga Promedio")
        
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        with st.expander("Ver detalle en tabla"):
            st.dataframe(vend_data.sort_values('Pct_Cumplimiento', ascending=False))

with tab3:
    st.subheader("Análisis de Base de Clientes y Cumplimiento")
    
    if 'Categoria' in df_filtered.columns and 'Local' in df_filtered.columns:
        # 1. Calcular Número de Clientes Únicos por Categoría
        clientes_unicos = df_filtered.groupby('Categoria')['Local'].nunique().reset_index()
        clientes_unicos.rename(columns={'Local': 'Num_Clientes'}, inplace=True)
        
        # 2. Calcular Cumplimiento de Tareas
        cat_stats = df_filtered.groupby('Categoria').agg({'Pregunta': 'count', 'VALIDADA FINAL': 'sum'}).reset_index()
        cat_stats.rename(columns={'Pregunta': 'Asignadas', 'VALIDADA FINAL': 'Cumplidas'}, inplace=True)
        cat_stats['Pct_Cumplimiento'] = (cat_stats['Cumplidas'] / cat_stats['Asignadas'] * 100)
        
        # Fusionar ambas tablas
        final_cat_stats = pd.merge(clientes_unicos, cat_stats, on='Categoria')
        
        col_kpi1, col_kpi2 = st.columns([1, 2])
        
        with col_kpi1:
            st.markdown("### 👥 Clientes Únicos")
            st.write("Número de puntos de venta visitados en este periodo por categoría:")
            st.dataframe(final_cat_stats[['Categoria', 'Num_Clientes']].style.background_gradient(cmap='Blues'))
            
            # Gráfico simple de torta o barras para clientes
            fig_pie = px.pie(final_cat_stats, values='Num_Clientes', names='Categoria', title="Mix de Clientes", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_kpi2:
            st.markdown("### 📊 Efectividad en esos Clientes")
            fig_combo = go.Figure()
            # Eje Y1: Volumen de Clientes (Barras)
            fig_combo.add_trace(go.Bar(
                x=final_cat_stats['Categoria'], 
                y=final_cat_stats['Num_Clientes'], 
                name='Nº Clientes', 
                marker_color='royalblue',
                text=final_cat_stats['Num_Clientes'],
                textposition='auto'
            ))
            
            # Eje Y2: % Cumplimiento (Línea)
            fig_combo.add_trace(go.Scatter(
                x=final_cat_stats['Categoria'], 
                y=final_cat_stats['Pct_Cumplimiento'], 
                name='% Cumplimiento', 
                yaxis='y2', 
                mode='lines+markers+text', 
                text=[f"{v:.1f}%" for v in final_cat_stats['Pct_Cumplimiento']],
                line=dict(color='red', width=3), 
                textposition="top center"
            ))
            
            fig_combo.update_layout(
                title="Relación: Tamaño de Base vs Efectividad de Tareas",
                yaxis=dict(title="Número de Clientes Únicos"),
                yaxis2=dict(title="% Cumplimiento Tareas", overlaying='y', side='right', range=[0, 100]),
                legend=dict(x=0.01, y=0.99)
            )
            st.plotly_chart(fig_combo, use_container_width=True)

with tab4:
    st.header("📦 Análisis de Portafolio")
    st.subheader("Top Items más Vendidos")
    top_items = df_filtered[df_filtered['VALIDADA FINAL'] == 1]['Pregunta'].value_counts().head(10).reset_index()
    top_items.columns = ['Item', 'Ventas']
    fig_items = px.bar(top_items, x='Ventas', y='Item', orientation='h', title="Ranking de Ventas", color='Ventas', color_continuous_scale='Blues')
    fig_items.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_items, use_container_width=True)

with tab5:
    st.header("⚡ Plan de Recuperación Táctico (Mes Caído)")
    st.markdown("""
    **Objetivo:** Calcular qué necesitamos hacer el *próximo mes* para cerrar la brecha de ventas.
    """)
    
    # 1. Definir la BASE (Lo que hicimos en el periodo seleccionado)
    base_ventas = total_ventas # Viene de los KPIs principales
    base_visitas = total_visitas
    base_conversion = tasa_conversion
    
    col_input1, col_input2, col_input3 = st.columns(3)
    
    with col_input1:
        st.info(f"📊 **Cierre Actual (Base)**\nVentas: {base_ventas:,.0f}\nConv: {base_conversion:.1f}%")
        
    with col_input2:
        # Input: La Meta del próximo mes
        meta_ventas = st.number_input("🎯 Meta de Ventas Próximo Mes:", value=int(base_ventas * 1.10), step=1000)
        gap = meta_ventas - base_ventas
        st.write(f"📉 **Brecha a recuperar (Gap):** {gap:,.0f}")

    with col_input3:
        st.write("🛠️ **Simulador de Acciones**")
        # Sliders Tácticos
        sim_visitas = st.slider("Incrementar Visitas (%)", 0, 50, 5)
        sim_conv = st.slider("Mejorar Efectividad (%)", 0.0, 100.0, float(base_conversion), format="%.1f%%")

    st.markdown("---")
    
    # Cálculos Tácticos
    # 1. Impacto por Visitas (Fuerza Bruta)
    nuevas_visitas = base_visitas * (1 + sim_visitas/100)
    ventas_por_volumen = nuevas_visitas * (base_conversion/100) # Ventas si solo subimos visitas manteniendo efec. actual
    aporte_volumen = ventas_por_volumen - base_ventas
    
    # 2. Impacto por Efectividad (Calidad)
    # Sobre las NUEVAS visitas, aplicamos la NUEVA conversión
    ventas_finales_sim = nuevas_visitas * (sim_conv/100)
    aporte_efectividad = ventas_finales_sim - ventas_por_volumen # La diferencia es gracias a la mejor conversión
    
    # Resultado
    cumplimiento_sim = (ventas_finales_sim / meta_ventas) * 100
    color_resultado = "green" if cumplimiento_sim >= 100 else "red"
    
    # Visualización de Cascada (Bridge)
    st.subheader("Puente de Recuperación")
    
    fig_bridge = go.Figure(go.Waterfall(
        name = "Recuperación", orientation = "v",
        measure = ["relative", "relative", "relative", "total", "total"],
        x = ["Cierre Actual", "Aporte x +Visitas", "Aporte x +Efectividad", "Proyección Final", "Meta"],
        textposition = "outside",
        text = [f"{base_ventas/1000:.0f}k", f"+{aporte_volumen/1000:.1f}k", f"+{aporte_efectividad/1000:.1f}k", f"{ventas_finales_sim/1000:.0f}k", f"{meta_ventas/1000:.0f}k"],
        y = [base_ventas, aporte_volumen, aporte_efectividad, ventas_finales_sim, 0], # La meta es una barra comparativa aparte o línea, aquí usamos total para la proyección
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
    ))
    
    # Añadimos la Meta como una línea horizontal
    fig_bridge.add_hline(y=meta_ventas, line_dash="dot", line_color="black", annotation_text="Meta Objetivo")
    
    fig_bridge.update_layout(title = "Cómo cerramos el Gap el próximo mes", showlegend = False)
    st.plotly_chart(fig_bridge, use_container_width=True)
    
    # Veredicto
    st.markdown(f"""
    ### 📝 Veredicto del Simulador
    Con un aumento del **{sim_visitas}% en visitas** y una efectividad del **{sim_conv:.1f}%**, 
    proyectamos vender **{ventas_finales_sim:,.0f}**.
    
    Esto representa un **:{color_resultado}[{cumplimiento_sim:.1f}%]** de la meta propuesta.
    """)