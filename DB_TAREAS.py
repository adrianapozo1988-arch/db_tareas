import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import zipfile

# Configuración de la página
st.set_page_config(page_title="Seguimiento de Tareas", layout="wide")

# --- BLOQUE DE SEGURIDAD (Login) ---
def check_password():
    """Retorna True si el usuario ingresó la clave correcta."""
    def password_entered():
        if st.session_state["password"] == "clave_2026": # <--- CAMBIA TU CLAVE AQUÍ
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
st.title("SEGUIMIENTO DE TAREAS & ONE YEAR PLAN")
st.markdown("---")

# --- 1. CARGA DE DATOS INTELIGENTE (AHORA LEE ZIP) ---
@st.cache_data
def load_data():
    archivos_en_carpeta = os.listdir('.')
    archivo_encontrado = None
    
    # 1. Buscamos primero si hay un ZIP (prioridad porque es más rápido)
    for archivo in archivos_en_carpeta:
        if "Tareas" in archivo and archivo.endswith(".zip"):
            archivo_encontrado = archivo
            break
            
    # 2. Si no hay ZIP, buscamos CSV o Excel normal
    if not archivo_encontrado:
        for archivo in archivos_en_carpeta:
            if "Tareas" in archivo and (archivo.endswith(".xlsx") or archivo.endswith(".csv")):
                archivo_encontrado = archivo
                break
    
    if archivo_encontrado:
        try:
            # Caso A: Es un ZIP
            if archivo_encontrado.endswith('.zip'):
                with zipfile.ZipFile(archivo_encontrado, 'r') as z:
                    # Buscamos el primer archivo dentro del zip que sea csv o excel
                    for nombre_interno in z.namelist():
                        if nombre_interno.endswith('.csv'):
                            return pd.read_csv(z.open(nombre_interno))
                        elif nombre_interno.endswith('.xlsx'):
                            return pd.read_excel(z.open(nombre_interno), engine='openpyxl')
                            
            # Caso B: Es CSV normal
            elif archivo_encontrado.endswith('.csv'):
                return pd.read_csv(archivo_encontrado)
                
            # Caso C: Es Excel normal
            else:
                return pd.read_excel(archivo_encontrado, engine='openpyxl')
        except Exception as e:
            st.error(f"Error leyendo el archivo: {e}")
            return None
    else:
        return None

df = load_data()

if df is None:
    st.error("❌ ERROR: No encuentro tu archivo de datos (Excel, CSV o ZIP).")
    st.stop()

# --- 2. BARRA LATERAL (FILTROS) ---
st.sidebar.header("🎯 Filtros")

# Filtro Mes
if 'Mes_Nombre' in df.columns:
    meses_ordenados = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                       'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    meses_disponibles = [m for m in meses_ordenados if m in df['Mes_Nombre'].unique()]
    mes_seleccionado = st.sidebar.multiselect("Selecciona Mes:", meses_disponibles, default=meses_disponibles)
else:
    st.error("Falta columna 'Mes_Nombre'")
    st.stop()

# Filtro Macrocanal
if 'Macrocanal' in df.columns:
    canales_disponibles = df['Macrocanal'].unique()
    canal_seleccionado = st.sidebar.multiselect("Selecciona Macrocanal:", canales_disponibles, default=canales_disponibles)
else:
    st.error("Falta columna 'Macrocanal'")
    st.stop()

# Aplicar filtros
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
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Visión General", "🏆 Fuerza de Ventas", "🛒 Clientes", "📦 Análisis de Portafolio", "📅 One Year Plan"])

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
    
    st.markdown("---")
    
    st.subheader("Mapa de Calor: Intensidad de Tareas")
    heatmap_data = df_filtered.pivot_table(index='Subcanal', columns='Mes_Nombre', values='Pregunta', aggfunc='count', fill_value=0)
    heatmap_data['Total'] = heatmap_data.sum(axis=1)
    heatmap_data = heatmap_data.sort_values('Total', ascending=False).drop(columns='Total').head(15)
    fig_heat = px.imshow(heatmap_data, text_auto=True, aspect="auto", color_continuous_scale='Viridis')
    st.plotly_chart(fig_heat, use_container_width=True)

with tab2:
    st.header("Análisis de Efectividad de Fuerza de Ventas")
    
    if 'Piramide Ventas.Vendedor' in df_filtered.columns:
        vend_data = df_filtered.groupby('Piramide Ventas.Vendedor').agg({
            'Pregunta': 'count', 'VALIDADA FINAL': 'sum', 'VALIDADA GEO': 'sum', 'VALIDADA VENTA': 'sum'
        }).reset_index()
        
        vend_data['Pct_Cumplimiento'] = (vend_data['VALIDADA FINAL'] / vend_data['Pregunta'] * 100).fillna(0)
        vend_data['Conversion_Rate'] = (vend_data['VALIDADA VENTA'] / vend_data['VALIDADA GEO'] * 100).fillna(0)
        
        def asignar_cuadrante(pct):
            if pct < 25: return '0-25% (Crítico)'
            elif pct < 50: return '25-50% (Bajo)'
            elif pct < 75: return '50-75% (Medio)'
            else: return '75-100% (Alto)'
            
        vend_data['Cuadrante'] = vend_data['Pct_Cumplimiento'].apply(asignar_cuadrante)
        
        cuadrante_counts = vend_data['Cuadrante'].value_counts().reindex(['0-25% (Crítico)', '25-50% (Bajo)', '50-75% (Medio)', '75-100% (Alto)']).fillna(0)
        
        col_v1, col_v2 = st.columns([1, 2])
        
        with col_v1:
            st.subheader("Distribución de Vendedores")
            fig_cuadrantes = px.bar(
                x=cuadrante_counts.index, y=cuadrante_counts.values, color=cuadrante_counts.index,
                title="Cantidad de Vendedores por Nivel de Cumplimiento",
                color_discrete_map={'0-25% (Crítico)':'red', '25-50% (Bajo)':'orange', '50-75% (Medio)':'yellow', '75-100% (Alto)':'green'}
            )
            st.plotly_chart(fig_cuadrantes, use_container_width=True)
            
        with col_v2:
            st.subheader("Matriz: Carga vs Efectividad")
            fig_scatter = px.scatter(
                vend_data, x='Pregunta', y='Pct_Cumplimiento', color='Cuadrante', size='VALIDADA GEO',
                hover_name='Piramide Ventas.Vendedor',
                title="Cada punto es un vendedor (Tamaño = Visitas)",
                color_discrete_map={'0-25% (Crítico)':'red', '25-50% (Bajo)':'orange', '50-75% (Medio)':'yellow', '75-100% (Alto)':'green'}
            )
            fig_scatter.add_hline(y=50, line_dash="dash", line_color="orange")
            fig_scatter.add_hline(y=75, line_dash="dash", line_color="green")
            st.plotly_chart(fig_scatter, use_container_width=True)

        st.markdown("### 📋 Detalle de Vendedores")
        st.dataframe(vend_data[['Piramide Ventas.Vendedor', 'Pregunta', 'VALIDADA FINAL', 'Pct_Cumplimiento', 'Cuadrante']].sort_values('Pct_Cumplimiento', ascending=False))

with tab3:
    st.subheader("Cumplimiento por Categoría de Cliente")
    if 'Categoria' in df_filtered.columns:
        cat_stats = df_filtered.groupby('Categoria').agg({'Pregunta': 'count', 'VALIDADA FINAL': 'sum'}).reset_index()
        cat_stats.rename(columns={'Pregunta': 'Asignadas', 'VALIDADA FINAL': 'Cumplidas'}, inplace=True)
        cat_stats['Pct_Cumplimiento'] = (cat_stats['Cumplidas'] / cat_stats['Asignadas'] * 100)
        cat_stats = cat_stats.sort_values('Pct_Cumplimiento', ascending=False)
        
        fig_combo = go.Figure()
        fig_combo.add_trace(go.Bar(x=cat_stats['Categoria'], y=cat_stats['Asignadas'], name='Tareas Asignadas', marker_color='lightgray'))
        fig_combo.add_trace(go.Bar(x=cat_stats['Categoria'], y=cat_stats['Cumplidas'], name='Tareas Cumplidas', marker_color='forestgreen'))
        fig_combo.add_trace(go.Scatter(
            x=cat_stats['Categoria'], y=cat_stats['Pct_Cumplimiento'], name='% Cumplimiento', yaxis='y2', 
            mode='lines+markers+text', text=[f"{v:.1f}%" for v in cat_stats['Pct_Cumplimiento']],
            line=dict(color='red', width=3), textposition="top center"
        ))
        fig_combo.update_layout(
            title="Asignación vs Ejecución por Categoría", yaxis=dict(title="Cantidad de Tareas"),
            yaxis2=dict(title="% Cumplimiento", overlaying='y', side='right', range=[0, 100]), barmode='group'
        )
        st.plotly_chart(fig_combo, use_container_width=True)

with tab4:
    st.header("📦 Análisis de Portafolio (Items)")
    st.subheader("Top 10 Tareas/Items más Vendidos (Global)")
    top_items = df_filtered[df_filtered['VALIDADA FINAL'] == 1]['Pregunta'].value_counts().head(10).reset_index()
    top_items.columns = ['Item', 'Ventas']
    fig_items = px.bar(top_items, x='Ventas', y='Item', orientation='h', title="Ranking de Ventas por Item", color='Ventas', color_continuous_scale='Blues')
    fig_items.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_items, use_container_width=True)
    
    st.markdown("---")
    st.subheader("🔍 ¿Qué items funcionan mejor en cada Categoría de Cliente?")
    cats_disponibles = sorted(df_filtered['Categoria'].dropna().unique())
    cat_seleccionada_item = st.selectbox("Selecciona Categoría de Cliente para analizar:", cats_disponibles)
    
    df_cat_item = df_filtered[df_filtered['Categoria'] == cat_seleccionada_item]
    item_perf = df_cat_item.groupby('Pregunta').agg({'Pregunta': 'count', 'VALIDADA FINAL': 'sum'}).rename(columns={'Pregunta': 'Ofrecido', 'VALIDADA FINAL': 'Vendido'}).reset_index()
    item_perf['Efectividad'] = (item_perf['Vendido'] / item_perf['Ofrecido'] * 100).fillna(0)
    item_perf = item_perf[item_perf['Ofrecido'] > 10].sort_values('Efectividad', ascending=False).head(10)
    
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        st.dataframe(item_perf[['Pregunta', 'Ofrecido', 'Vendido', 'Efectividad']].style.format({'Efectividad': '{:.1f}%'}))
    with col_i2:
        fig_cat_items = px.bar(
            item_perf, x='Efectividad', y='Pregunta', orientation='h', 
            title=f"Top Items por % de Cierre en {cat_seleccionada_item}", color='Efectividad', color_continuous_scale='Greens'
        )
        fig_cat_items.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_cat_items, use_container_width=True)

with tab5:
    st.header("📅 One Year Plan Avanzado")
    st.info("Simula escenarios modificando las visitas por subcanal específico.")
    subcanales_oyp = df_filtered['Subcanal'].unique()
    subcanal_sim = st.selectbox("🎯 Selecciona el Subcanal a Potenciar:", subcanales_oyp)
    
    col_sim1, col_sim2, col_sim3 = st.columns(3)
    df_sub = df_filtered[df_filtered['Subcanal'] == subcanal_sim]
    visitas_act_sub = df_sub['VALIDADA GEO'].sum()
    ventas_act_sub = df_sub['VALIDADA VENTA'].sum()
    conv_act_sub = (ventas_act_sub / visitas_act_sub * 100) if visitas_act_sub > 0 else 0
    
    with col_sim1:
        st.markdown(f"**KPIs Actuales: {subcanal_sim}**")
        st.write(f"Visitas: {visitas_act_sub:,.0f}")
        st.write(f"Conversión: {conv_act_sub:.1f}%")
    with col_sim2:
        st.subheader("🛠️ Ajustes")
        delta_visitas = st.slider(f"Cambio en Visitas ({subcanal_sim})", -50, 100, 0, format="%d%%")
        nueva_conv = st.slider(f"Nueva Conversión ({subcanal_sim})", 0.0, 100.0, float(conv_act_sub), format="%.1f%%")
        
    visitas_new_sub = visitas_act_sub * (1 + delta_visitas/100)
    ventas_new_sub = visitas_new_sub * (nueva_conv/100)
    delta_ventas_sub = ventas_new_sub - ventas_act_sub
    total_ventas_actual = total_ventas
    total_ventas_proy = total_ventas_actual + delta_ventas_sub
    lift_global = ((total_ventas_proy - total_ventas_actual) / total_ventas_actual * 100) if total_ventas_actual > 0 else 0
    
    with col_sim3:
        st.subheader("🚀 Impacto Global")
        st.metric("Ventas Totales Proyectadas", f"{total_ventas_proy:,.0f}", delta=f"{lift_global:.2f}% Global")
        st.write(f"Venta extra aportada por {subcanal_sim}: **+{delta_ventas_sub:,.0f}**")
    
    st.markdown("---")
    fig_waterfall = go.Figure(go.Waterfall(
        name = "20", orientation = "v", measure = ["relative", "relative", "total"],
        x = ["Ventas Actuales", f"Impacto {subcanal_sim}", "Ventas Proyectadas"],
        textposition = "outside", text = [f"{total_ventas_actual/1000:.0f}k", f"{delta_ventas_sub/1000:+.0f}k", f"{total_ventas_proy/1000:.0f}k"],
        y = [total_ventas_actual, delta_ventas_sub, total_ventas_proy], connector = {"line":{"color":"rgb(63, 63, 63)"}},
    ))
    fig_waterfall.update_layout(title = "Puente de Ventas: Impacto de la Simulación", showlegend = False)
    st.plotly_chart(fig_waterfall, use_container_width=True)