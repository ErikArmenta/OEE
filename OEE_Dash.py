# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import altair as alt
from datetime import datetime, timedelta, date
import numpy as np
from modules.supabase_client import SupabaseManager

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Sistema OEE | EA Innovation",
    page_icon="eficiencia.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS PERSONALIZADOS (Dark Mode & Professional) ---
st.markdown("""
<style>
    /* Global Styles */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        border: 1px solid #334155;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: #0f172a;
        padding: 10px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        color: #94a3b8;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #38bdf8;
        background-color: #1e293b;
        border-radius: 5px;
    }
    /* Button Styles */
    div.stButton > button {
        background-color: #2563eb;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #1d4ed8;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZACIÓN SUPABASE ---
@st.cache_resource
def init_connection():
    try:
        if "supabase" in st.secrets:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
            return SupabaseManager(url, key)
        else:
            return None
    except Exception as e:
        return None

db = init_connection()

# --- FUNCIONES DE CÁLCULO (BACKEND LOGIC) ---
def calculate_metrics(tiempo_programado, rate_teorico, producido, rechazos,
                     setup, f_mec, f_elec, f_cham, ajuste, f_mat):

    # 1. Tiempo Muerto (Suma de fallas)
    tiempo_muerto = setup + f_mec + f_elec + f_cham + ajuste + f_mat

    # 2. Tiempo Funcionamiento
    tiempo_funcionamiento = max(0, tiempo_programado - tiempo_muerto)

    # 3. Disponibilidad: (Tiempo Programado - Tiempo Muerto) / Tiempo Programado
    disponibilidad = (tiempo_funcionamiento / tiempo_programado) if tiempo_programado > 0 else 0

    # 4. Rendimiento: Unidades Producidas / (Tiempo Funcionamiento * Rate Teórico)
    # Note: Rate Teórico is typically units/minute.
    capacidad_teorica = tiempo_funcionamiento * rate_teorico
    rendimiento = (producido / capacidad_teorica) if capacidad_teorica > 0 else 0

    # 5. Calidad: (Unidades Producidas - Rechazos) / Unidades Producidas
    calidad = ((producido - rechazos) / producido) if producido > 0 else 0

    # 6. OEE
    oee = disponibilidad * rendimiento * calidad

    return {
        "tiempo_muerto": tiempo_muerto,
        "tiempo_funcionamiento": tiempo_funcionamiento,
        "disponibilidad": disponibilidad * 100, # Convertir a porcentaje
        "rendimiento": rendimiento * 100,
        "calidad": calidad * 100,
        "oee": oee * 100
    }

# --- SIDEBAR ---
with st.sidebar:
    try:
        st.image("EA_2.png", width=200)
    except:
        st.title("EA System")

    st.markdown("### ⚙️ Configuración Global")

    # Meta OEE Slider
    meta_oee = st.number_input("🎯 Meta OEE (%)", min_value=0.0, max_value=100.0, value=85.0, step=1.0)

    # Filtros Globales (Afectan Dashboard y Reportes)
    filter_date_range = st.date_input("📅 Rango de Fechas",
                                    [date.today() - timedelta(days=30), date.today()])

    # Líneas disponibles (SL001 - SL033)
    lineas_opts = [f"SL{str(i).zfill(3)}" for i in range(1, 34)]
    filter_line = st.multiselect("🏭 Líneas", lineas_opts, default=lineas_opts[:5])

    filter_turn = st.multiselect("⏰ Turno", ["Mañana", "Tarde", "Noche"], default=["Mañana", "Tarde", "Noche"])

    st.markdown("---")
    st.markdown("**Master Engineer Erik Armenta**")

# --- MAIN APP ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard OEE", "✍️ Captura de Datos", "📄 Reportes y Descargas"])

# -----------------------------------------------------------------------------
# TAB 1: DASHBOARD
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# TAB 1: DASHBOARD
# -----------------------------------------------------------------------------
def make_donut(input_response, input_text, input_color):
    if input_color == 'blue':
        chart_color = ['#29b5e8', '#155F7A']
    if input_color == 'green':
        chart_color = ['#27AE60', '#12783D']
    if input_color == 'orange':
        chart_color = ['#F39C12', '#875A12']
    if input_color == 'red':
        chart_color = ['#E74C3C', '#78281F']

    source = pd.DataFrame({
        "Topic": ['', input_text],
        "% value": [100-input_response, input_response]
    })
    source_bg = pd.DataFrame({
        "Topic": ['', input_text],
        "% value": [100, 0]
    })

    plot = alt.Chart(source).mark_arc(innerRadius=60, cornerRadius=25).encode(
        theta="% value",
        color= alt.Color("Topic:N",
                        scale=alt.Scale(
                            domain=[input_text, ''],
                            range=chart_color),
                        legend=None),
    ).properties(width=180, height=180)

    text = plot.mark_text(align='center', color="#29b5e8", font="Lato", fontSize=28, fontWeight=700, fontStyle="italic").encode(text=alt.value(f'{input_response:.2f}%'))
    plot_bg = alt.Chart(source_bg).mark_arc(innerRadius=60, cornerRadius=20).encode(
        theta="% value",
        color= alt.Color("Topic:N",
                        scale=alt.Scale(
                            domain=[input_text, ''],
                            range=chart_color),
                        legend=None),
    ).properties(width=180, height=180)
    return plot_bg + plot + text

with tab1:
    st.title("📊 Dashboard OEE en Tiempo Real")

    if not db:
        st.error("⚠️ Error de conexión: No se encontraron credenciales de Supabase en 'secrets.toml'.")
        st.info("Por favor configura [supabase] url y key.")
    else:
        # Fetch Data based on filters
        if len(filter_date_range) == 2:
            start_d, end_d = filter_date_range
            raw_df = db.fetch_records(start_d, end_d)

            if not raw_df.empty:
                # Apply Filters
                df = raw_df[
                    (raw_df['linea'].isin(filter_line)) &
                    (raw_df['turno'].isin(filter_turn))
                ]

                if not df.empty:
                    # --- NUEVA LÓGICA CORRECTA PARA KPI GLOBALES (CÁLCULO HORIZONTAL) ---
                    total_tiempo_prog = df['tiempo_programado_min'].sum()
                    total_tiempo_muerto = df['tiempo_muerto'].sum()
                    total_producido = df['producido'].sum()

                    # Para el esperado, sumamos la capacidad teórica de cada registro individualmente
                    total_esperado = (df['tiempo_funcionamiento'] * df['rate_teorico']).sum()
                    total_rechazos = df['rechazos_fugas'].sum()

                    # Calculamos componentes globales
                    disp_g = ((total_tiempo_prog - total_tiempo_muerto) / total_tiempo_prog) if total_tiempo_prog > 0 else 0
                    perf_g = (total_producido / total_esperado) if total_esperado > 0 else 0
                    qual_g = ((total_producido - total_rechazos) / total_producido) if total_producido > 0 else 0

                    # Asignación a variables para las donas y métricas
                    kpi_oee = (disp_g * perf_g * qual_g) * 100
                    kpi_disp = disp_g * 100
                    kpi_perf = perf_g * 100
                    kpi_qual = qual_g * 100

                    st.markdown("### Indicadores Clave de Rendimiento (KPIs)")
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.altair_chart(make_donut(kpi_oee, 'OEE', 'blue'), use_container_width=True)
                        st.metric("OEE Global", f"{kpi_oee:.2f}%", delta=f"{kpi_oee-meta_oee:.2f}% vs Meta")
                    with col2:
                        st.altair_chart(make_donut(kpi_disp, 'Disponibilidad', 'green'), use_container_width=True)
                        st.metric("Disponibilidad", f"{kpi_disp:.2f}%")
                    with col3:
                        st.altair_chart(make_donut(kpi_perf, 'Rendimiento', 'orange'), use_container_width=True)
                        st.metric("Eficiencia / Rendimiento", f"{kpi_perf:.2f}%")
                    with col4:
                        st.altair_chart(make_donut(kpi_qual, 'Calidad', 'red'), use_container_width=True)
                        st.metric("Calidad (FTT)", f"{kpi_qual:.2f}%")

                    st.markdown("---")

                    # --- FUNCIÓN INTERNA PARA CÁLCULO HORIZONTAL EN GRÁFICAS ---
                    def calc_h_metrics(x):
                        tp = x['tiempo_programado_min'].sum()
                        tm = x['tiempo_muerto'].sum()
                        prod = x['producido'].sum()
                        esp = (x['tiempo_funcionamiento'] * x['rate_teorico']).sum()
                        rech = x['rechazos_fugas'].sum()
                        d = (tp - tm) / tp if tp > 0 else 0
                        p = prod / esp if esp > 0 else 0
                        q = (prod - rech) / prod if prod > 0 else 0
                        return pd.Series({'oee': (d*p*q)*100, 'disp': d*100, 'perf': p*100, 'qual': q*100})

                    # Gráficos de Tendencia
                    c1, c2 = st.columns(2)

                    with c1:
                        # Tendencia Diaria (Agrupada horizontalmente)
                        df_daily = df.groupby('fecha').apply(calc_h_metrics, include_groups=False).reset_index()
                        fig_trend = px.line(df_daily, x='fecha', y='oee', markers=True,
                                          title="Tendencia OEE Diaria (Cálculo Real)", template="plotly_dark")
                        fig_trend.add_hline(y=meta_oee, line_dash="dash", line_color="green", annotation_text=f"Meta {meta_oee}%")
                        st.plotly_chart(fig_trend, use_container_width=True)

                    with c2:
                        # Tendencia Mensual (Agrupada horizontalmente)
                        df['mes'] = pd.to_datetime(df['fecha']).dt.strftime('%Y-%m')
                        df_monthly = df.groupby('mes').apply(calc_h_metrics, include_groups=False).reset_index()
                        fig_month = px.bar(df_monthly, x='mes', y='oee',
                                         title="Tendencia OEE Mensual (Cálculo Real)", template="plotly_dark",
                                         color='oee', color_continuous_scale='Blues')
                        fig_month.add_hline(y=meta_oee, line_dash="dash", line_color="green", annotation_text=f"Meta {meta_oee}%")
                        st.plotly_chart(fig_month, use_container_width=True)

                    # Pareto y Desglose
                    c3, c4 = st.columns(2)

                    with c3:
                        failure_cols = ['setup_excesivo', 'falla_mecanica', 'falla_electrica',
                                      'falla_chamber', 'ajuste_no_programado', 'falta_material']
                        failures = df[failure_cols].sum().sort_values(ascending=False).reset_index()
                        failures.columns = ['Falla', 'Minutos']
                        failures['Acumulado'] = failures['Minutos'].cumsum() / failures['Minutos'].sum() * 100
                        fig_pareto = make_subplots(specs=[[{"secondary_y": True}]])
                        fig_pareto.add_trace(go.Bar(x=failures['Falla'], y=failures['Minutos'], name="Minutos", marker_color="#ef4444"), secondary_y=False)
                        fig_pareto.add_trace(go.Scatter(x=failures['Falla'], y=failures['Acumulado'], name="% Acumulado", marker_color="#3b82f6"), secondary_y=True)
                        fig_pareto.update_layout(title="Pareto de Tiempo Muerto (Minutos)", template="plotly_dark")
                        st.plotly_chart(fig_pareto, use_container_width=True)

                    with c4:
                        # Desglose OEE por Línea (Agrupado horizontalmente)
                        df_line = df.groupby('linea').apply(calc_h_metrics, include_groups=False).reset_index()
                        fig_bar = px.bar(df_line, x='linea', y=['disp', 'perf', 'qual'],
                                    title="Desglose OEE por Línea (Cálculo Real)", barmode='group',
                                    template="plotly_dark", labels={'value': 'Porcentaje (%)', 'variable': 'KPI'})
                        st.plotly_chart(fig_bar, use_container_width=True)

                else:
                    st.warning("No hay datos para los filtros seleccionados.")
            else:
                st.info("No se encontraron registros en el rango de fechas seleccionado.")
        else:
            st.info("Seleccione un rango de fechas válido.")
# -----------------------------------------------------------------------------
# TAB 2: CAPTURA DE DATOS
# -----------------------------------------------------------------------------
with tab2:
    st.header("📝 Nuevo Registro OEE")
    st.markdown("Celdas naranjas del formato Excel original.")

    if not db:
        st.warning("⚠️ Base de datos no conectada. No se podran guardar registros.")

    with st.form("oee_form", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            f_fecha = st.date_input("Fecha", date.today())
            f_linea = st.selectbox("Línea", lineas_opts)

        with col2:
            f_turno = st.selectbox("Turno", ["Mañana", "Tarde", "Noche"])
            f_modelo = st.text_input("Modelo/Parte")

        with col3:
            f_tiempo_prog = st.number_input("Tiempo Programado (min)", min_value=0, value=480, help="Tiempo Total del Turno")
            f_rate = st.number_input("Rate Teórico/Eficiencia (u/min)", min_value=0.0, value=1.0, format="%.2f")

        with col4:
            f_producido = st.number_input("Total Producido", min_value=0)
            f_rechazos = st.number_input("Scrap / Rechazos (Cantidad)", min_value=0, help="Cantidad de piezas SCRAP")

        st.markdown("#### 🛑 Tiempos Muertos (Minutos)")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1: f_setup = st.number_input("Setup Excesivo", min_value=0)
        with c2: f_mec = st.number_input("Falla Mecánica", min_value=0)
        with c3: f_elec = st.number_input("Falla Eléctrica", min_value=0)
        with c4: f_cham = st.number_input("Falla Chamber", min_value=0)
        with c5: f_ajuste = st.number_input("Ajuste No Prog.", min_value=0)
        with c6: f_mat = st.number_input("Falta Material", min_value=0)

        submitted = st.form_submit_button("💾 Guardar Registro", type="primary")

        if submitted:
            # Calcular Métricas
            metrics = calculate_metrics(f_tiempo_prog, f_rate, f_producido, f_rechazos,
                                     f_setup, f_mec, f_elec, f_cham, f_ajuste, f_mat)

            # Preparar Payload
            payload = {
                "fecha": f_fecha.isoformat(),
                "linea": f_linea,
                "turno": f_turno,
                "modelo": f_modelo,
                "tiempo_programado_min": f_tiempo_prog,
                "rate_teorico": f_rate,
                "producido": f_producido,
                "rechazos_fugas": f_rechazos,
                "setup_excesivo": f_setup,
                "falla_mecanica": f_mec,
                "falla_electrica": f_elec,
                "falla_chamber": f_cham,
                "ajuste_no_programado": f_ajuste,
                "falta_material": f_mat,
                "tiempo_muerto": metrics["tiempo_muerto"],
                "tiempo_funcionamiento": metrics["tiempo_funcionamiento"],
                "disponibilidad": metrics["disponibilidad"],
                "rendimiento": metrics["rendimiento"],
                "calidad": metrics["calidad"],
                "oee": metrics["oee"]
            }

            if db:
                res = db.insert_record(payload)
                if res:
                    st.success(f"✅ Registro guardado para {f_linea}")
                    st.info(f"OEE: {metrics['oee']:.1f}% | Rendimiento: {metrics['rendimiento']:.1f}% | FTT (Calidad): {metrics['calidad']:.1f}%")
                else:
                    st.error("❌ Error al guardar en base de datos.")
            else:
                st.error("No hay conexión a BD. Datos no guardados.")


# -----------------------------------------------------------------------------
# TAB 3: REPORTES
# -----------------------------------------------------------------------------
# --- FUNCIONALIDAD DE SEMÁFORO (ESTILO CONDICIONAL) ---
def aplicar_semaforo(val):
    """Aplica colores RGB basados en el rendimiento OEE/Rendimiento"""
    if val < 70:
        color = '#ef4444' # Rojo
    elif val < 85:
        color = '#f59e0b' # Amarillo
    else:
        color = '#10b981' # Verde
    return f'background-color: {color}; color: white; font-weight: bold'

import base64

def get_image_base64(path):
    try:
        with open(path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        return encoded_string
    except Exception as e:
        return ""

with tab3:
    st.markdown("<h2 style='text-align: center;'>📄 Generador de Reportes Interactivos</h2>", unsafe_allow_html=True)

    if db and len(filter_date_range) == 2:
        start_d, end_d = filter_date_range
        raw_df_rep = db.fetch_records(start_d, end_d)

        if not raw_df_rep.empty:
            df_rep = raw_df_rep[
                (raw_df_rep['linea'].isin(filter_line)) &
                (raw_df_rep['turno'].isin(filter_turn))
            ]

            if not df_rep.empty:
                # --- FUNCIÓN DE APOYO PARA CÁLCULO HORIZONTAL ---
                def calc_report_metrics(x):
                    tp = x['tiempo_programado_min'].sum()
                    tm = x['tiempo_muerto'].sum()
                    prod = x['producido'].sum()
                    esp = (x['tiempo_funcionamiento'] * x['rate_teorico']).sum()
                    rech = x['rechazos_fugas'].sum()
                    d = (tp - tm) / tp if tp > 0 else 0
                    p = prod / esp if esp > 0 else 0
                    q = (prod - rech) / prod if prod > 0 else 0
                    return pd.Series({
                        'oee': round((d*p*q)*100, 2),
                        'disponibilidad': round(d*100, 2),
                        'rendimiento': round(p*100, 2),
                        'calidad': round(q*100, 2)
                    })

                # 1. Crear Tabla de Resumen (Cálculo Horizontal en lugar de pivot_table mean)
                pivot = df_rep.groupby('linea').apply(calc_report_metrics, include_groups=False)

                # Aplicar Estilo de Semáforo
                st.subheader("Vista Previa de Rendimiento (Totales Reales)")
                try:
                    styled_pivot = pivot.style.map(aplicar_semaforo, subset=['oee', 'rendimiento'])
                except:
                    styled_pivot = pivot.style.applymap(aplicar_semaforo, subset=['oee', 'rendimiento'])

                st.dataframe(styled_pivot, use_container_width=True)

                # 2. GENERACIÓN DE GRÁFICOS PARA EL REPORTE
                # Grafico 1: Barras OEE por Línea (Basado en el cálculo horizontal anterior)
                fig_html_bar = px.bar(pivot.reset_index(), x='linea', y='oee',
                                     color='oee', color_continuous_scale='RdYlGn',
                                     title="Análisis Comparativo Real por Línea", template="plotly_dark")

                # Grafico 2: Tendencia Diaria para el Reporte (Cálculo Horizontal)
                df_daily_rep = df_rep.groupby('fecha').apply(calc_report_metrics, include_groups=False).reset_index()
                fig_html_trend = px.line(df_daily_rep, x='fecha', y='oee', markers=True,
                                      title="Tendencia OEE Diaria (Totales)", template="plotly_dark")
                fig_html_trend.add_hline(y=85, line_dash="dash", line_color="green", annotation_text="Target 85%")

                # Grafico 3: Pareto (Este se mantiene igual porque ya usa .sum())
                failure_cols = ['setup_excesivo', 'falla_mecanica', 'falla_electrica',
                              'falla_chamber', 'ajuste_no_programado', 'falta_material']
                failures_rep = df_rep[failure_cols].sum().sort_values(ascending=False).reset_index()
                failures_rep.columns = ['Falla', 'Minutos']
                failures_rep['Acumulado'] = failures_rep['Minutos'].cumsum() / failures_rep['Minutos'].sum() * 100

                fig_html_pareto = make_subplots(specs=[[{"secondary_y": True}]])
                fig_html_pareto.add_trace(go.Bar(x=failures_rep['Falla'], y=failures_rep['Minutos'], name="Minutos", marker_color="#ef4444"), secondary_y=False)
                fig_html_pareto.add_trace(go.Scatter(x=failures_rep['Falla'], y=failures_rep['Acumulado'], name="% Acumulado", marker_color="#3b82f6"), secondary_y=True)
                fig_html_pareto.update_layout(title="Pareto de Tiempo Muerto (Minutos)", template="plotly_dark")

                # --- El resto del código del HTML y Botones de descarga se mantiene igual ---
                logo_b64 = get_image_base64("EA_2.png")
                logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width:120px; position:absolute; top:20px; left:20px;">' if logo_b64 else ""
                html_table = styled_pivot.to_html()

                reporte_completo = f"""
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>Reporte EA Innovation - OEE</title>
                    <style>
                        body {{ background-color: #0f172a; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; padding: 40px; }}
                        .page {{ max-width: 1200px; margin: auto; background: #1e293b; padding: 30px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); margin-bottom: 50px; position: relative; }}
                        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; color: white; }}
                        th, td {{ padding: 12px; border: 1px solid #334155; text-align: center; }}
                        th {{ background-color: #334155; }}
                        h1 {{ color: #38bdf8; margin-top: 40px; }}
                        .page-break {{ page-break-before: always; }}
                    </style>
                </head>
                <body>
                    <div class="page">
                        {logo_html}
                        <h1>EA Innovation Suite: Reporte OEE</h1>
                        <p><strong>Resumen Operativo (Cálculo Horizontal)</strong> | Rango: {start_d} al {end_d}</p>
                        <hr style="border: 0.5px solid #334155;">
                        <h3>Tabla de Rendimiento General</h3>
                        {html_table}
                        <br>
                        <h3>Comparativo de Eficiencia</h3>
                        {fig_html_bar.to_html(full_html=False, include_plotlyjs='cdn')}
                        <br>
                        <p style="font-size: 0.8em; color: #94a3b8;">Hoja 1 de 2 | Generado por Master Engineer Erik Armenta</p>
                    </div>
                    <div class="page-break"></div>
                    <div class="page">
                        {logo_html}
                        <h1>Análisis Detallado</h1>
                        <p><strong>Tendencias y Fallas</strong></p>
                        <hr style="border: 0.5px solid #334155;">
                        <h3>Tendencia de OEE en el Tiempo</h3>
                        {fig_html_trend.to_html(full_html=False, include_plotlyjs=False)}
                        <br><br>
                        <h3>Análisis de Pareto (Tiempos Muertos)</h3>
                        {fig_html_pareto.to_html(full_html=False, include_plotlyjs=False)}
                        <br>
                        <p style="font-size: 0.8em; color: #94a3b8;">Hoja 2 de 2 | Generado por Master Engineer Erik Armenta</p>
                    </div>
                </body>
                </html>
                """

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.download_button("📊 Descargar Reporte", reporte_completo, f"Reporte_OEE_{start_d}.html", "text/html", use_container_width=True)
                with col_btn2:
                    st.download_button("📊 Descargar Datos Crudos", df_rep.to_csv().encode('utf-8'), "datos_oee.csv", "text/csv", use_container_width=True)
            else:
                st.info("No hay datos para reportar.")

