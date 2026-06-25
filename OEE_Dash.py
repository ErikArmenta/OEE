# -*- coding: utf-8 -*-
"""
Created on Wed Jun 24 13:00:15 2026

@author: acer
"""

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
    page_title="Sistema OEE Rotarys | EA Innovation",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CATÁLOGO DE MÁQUINAS Y RATES ---
MAQUINAS_RATES = {
    "CS0525": 115, "CS0524": 115, "CS0516": 180, "CS0523": 100,
    "CS0522": 100, "CS0537": 200, "CS0514": 180, "CS0515": 180,
    "CS0505": 200, "CS0544": 200, "CS0575": 120, "CS0595": 120
}

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        border: 1px solid #334155;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; background-color: #0f172a; padding: 10px; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; color: #94a3b8; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #38bdf8; background-color: #1e293b; border-radius: 5px; }
    div.stButton > button { background-color: #2563eb; color: white; border-radius: 8px; border: none; padding: 0.5rem 1rem; transition: all 0.3s ease; }
    div.stButton > button:hover { background-color: #1d4ed8; transform: translateY(-2px); }
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
            st.error("⚠️ No se encontró la sección [supabase] en secrets.toml")
            return None
    except Exception as e:
        st.error(f"⚠️ Error al inicializar Supabase: {e}")
        return None

db = init_connection()

# --- FUNCIONES DE CÁLCULO (CORREGIDAS según Excel) ---
def calculate_metrics(tiempo_programado, rate_teorico, producido, scrap,
                      ajuste, f_mec, f_elec, f_personal, f_mat, c_modelo):

    tiempo_muerto = ajuste + f_mec + f_elec + f_personal + f_mat + c_modelo
    tiempo_funcionamiento = max(0, tiempo_programado - tiempo_muerto)

    # Disponibilidad = tiempo_funcionamiento / tiempo_programado
    disponibilidad = (tiempo_funcionamiento / tiempo_programado) if tiempo_programado > 0 else 0

    # CAPACIDAD TEÓRICA = tiempo_programado * (rate_teorico / 60)  --> como en Excel
    capacidad_teorica = tiempo_programado * (rate_teorico / 60)
    rendimiento = (producido / capacidad_teorica) if capacidad_teorica > 0 else 0

    # Scrap % = scrap / producido
    scrap_pct = (scrap / producido) if producido > 0 else 0
    # FTT y Calidad = producido / (producido + scrap)
    ftt = (producido / (producido + scrap)) if (producido + scrap) > 0 else 0
    calidad = ftt

    oee = disponibilidad * rendimiento * calidad

    return {
        "tiempo_muerto": tiempo_muerto,
        "tiempo_funcionamiento": tiempo_funcionamiento,
        "disponibilidad": disponibilidad * 100,
        "rendimiento": rendimiento * 100,
        "calidad": calidad * 100,
        "oee": oee * 100,
        "scrap_pct": scrap_pct * 100,
        "ftt": ftt * 100
    }

# --- SIDEBAR ---
with st.sidebar:
    try: st.image("EA_2.png", width=200)
    except: st.title("EA System")

    st.markdown("### ⚙️ Configuración Global")
    meta_oee = st.number_input("🎯 Meta OEE (%)", min_value=0.0, max_value=100.0, value=85.0, step=1.0)
    filter_date_range = st.date_input("📅 Rango de Fechas", [date.today() - timedelta(days=30), date.today()])

    maquinas_opts = list(MAQUINAS_RATES.keys())
    if db and len(filter_date_range) == 2:
        df_lines = db.fetch_records(filter_date_range[0], filter_date_range[1])
        if not df_lines.empty and 'maquina' in df_lines.columns:
            maquinas_opts = sorted(list(set(maquinas_opts + df_lines['maquina'].unique().tolist())))

    filter_maquina = st.multiselect("🏭 Máquinas", maquinas_opts, default=maquinas_opts)
    filter_turn = st.multiselect("⏰ Turno", [1, 2, 3], default=[1, 2, 3])

    st.markdown("---")
    st.markdown("**Master Engineer Erik Armenta**")

# --- MAIN APP ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard OEE", "✍️ Captura de Datos", "📄 Reportes y Descargas"])

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

    text = plot.mark_text(align='center', color=chart_color[0], font="Lato", fontSize=28, fontWeight=700, fontStyle="italic").encode(text=alt.value(f'{input_response:.2f}%'))
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
    st.title("📊 Dashboard Rotarys en Tiempo Real")

    if not db:
        st.error("⚠️ Error de conexión: No se encontraron credenciales de Supabase en 'secrets.toml'.")
        st.info("Por favor configura [supabase] url y key.")
    else:
        if len(filter_date_range) == 2:
            start_d, end_d = filter_date_range
            raw_df = db.fetch_records(start_d, end_d)

            if not raw_df.empty:
                df = raw_df[
                    (raw_df['maquina'].isin(filter_maquina)) &
                    (raw_df['turno'].isin(filter_turn))
                ]

                if not df.empty:
                    # --- KPIs GLOBALES (PROMEDIO DE LOS VALORES INDIVIDUALES) ---
                    kpi_oee = df['oee'].mean()
                    kpi_disp = df['disponibilidad'].mean()
                    kpi_perf = df['rendimiento'].mean()
                    kpi_ftt = df['ftt'].mean()
                    kpi_scrap = df['scrap_pct'].mean()

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
                        st.altair_chart(make_donut(kpi_ftt, 'FTT', 'red'), use_container_width=True)
                        st.metric("FTT (Calidad)", f"{kpi_ftt:.2f}%")
                        st.markdown(f"<h4 style='text-align: center; color: #ef4444;'>🚨 Scrap Global: {kpi_scrap:.2f}%</h4>", unsafe_allow_html=True)

                    st.markdown("---")

                    # --- FUNCIÓN PARA AGRUPAR PROMEDIOS (sin recalcular) ---
                    def avg_metrics(x):
                        return pd.Series({
                            'oee': x['oee'].mean(),
                            'disp': x['disponibilidad'].mean(),
                            'perf': x['rendimiento'].mean(),
                            'ftt': x['ftt'].mean(),
                            'scrap_pct': x['scrap_pct'].mean()
                        })

                    # Gráficos de Tendencia
                    c1, c2 = st.columns(2)

                    with c1:
                        df_daily = df.groupby('fecha').apply(avg_metrics, include_groups=False).reset_index()
                        fig_trend = px.line(df_daily, x='fecha', y='oee', markers=True,
                                          hover_data={'oee': ':.2f}%', 'ftt': ':.2f}%', 'scrap_pct': ':.2f}%'},
                                          title="Tendencia OEE Diaria (Promedio)", template="plotly_dark")
                        fig_trend.add_hline(y=meta_oee, line_dash="dash", line_color="green", annotation_text=f"Meta {meta_oee}%")
                        fig_trend.update_traces(line=dict(color="#38bdf8", width=3), marker=dict(size=8))
                        st.plotly_chart(fig_trend, use_container_width=True)

                    with c2:
                        df['mes'] = pd.to_datetime(df['fecha']).dt.strftime('%Y-%m')
                        df_monthly = df.groupby('mes').apply(avg_metrics, include_groups=False).reset_index()
                        fig_month = px.bar(df_monthly, x='mes', y='oee',
                                         hover_data={'oee': ':.2f}%', 'ftt': ':.2f}%', 'scrap_pct': ':.2f}%'},
                                         title="Tendencia OEE Mensual (Promedio)", template="plotly_dark",
                                         color='oee', color_continuous_scale='Blues')
                        fig_month.add_hline(y=meta_oee, line_dash="dash", line_color="green", annotation_text=f"Meta {meta_oee}%")
                        st.plotly_chart(fig_month, use_container_width=True)

                    # Pareto y Desglose
                    c3, c4 = st.columns(2)

                    with c3:
                        failure_cols = ['ajuste', 'falla_mecanica', 'falla_electrica', 'falta_personal', 'falta_material', 'cambio_modelo']
                        failures = df[failure_cols].sum().sort_values(ascending=False).reset_index()
                        failures.columns = ['Falla', 'Minutos']
                        failures['Acumulado'] = (failures['Minutos'].cumsum() / failures['Minutos'].sum() * 100).fillna(0)

                        fig_pareto = make_subplots(specs=[[{"secondary_y": True}]])
                        fig_pareto.add_trace(go.Bar(x=failures['Falla'], y=failures['Minutos'], name="Minutos", marker_color="#ef4444"), secondary_y=False)
                        fig_pareto.add_trace(go.Scatter(x=failures['Falla'], y=failures['Acumulado'], name="% Acumulado", marker_color="#3b82f6"), secondary_y=True)
                        fig_pareto.update_layout(title="Pareto de Tiempo Muerto (Minutos)", template="plotly_dark")
                        st.plotly_chart(fig_pareto, use_container_width=True)

                    with c4:
                        df_mach = df.groupby('maquina').apply(avg_metrics, include_groups=False).reset_index()
                        df_mach_melt = df_mach.rename(columns={'disp': 'Disponibilidad', 'perf': 'Rendimiento', 'ftt': 'FTT'})
                        fig_bar = px.bar(df_mach_melt, x='maquina', y=['Disponibilidad', 'Rendimiento', 'FTT'],
                                    title="Desglose de KPIs por Máquina (Promedio)", barmode='group',
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
    st.header("📝 Nuevo Registro Rotarys")

    col_dyn1, col_dyn2 = st.columns(2)
    with col_dyn1:
        f_maquina = st.selectbox("🏭 Seleccionar Máquina", list(MAQUINAS_RATES.keys()))
    with col_dyn2:
        f_rate = MAQUINAS_RATES[f_maquina]
        st.info(f"⚙️ **Rate Teórico Automático:** `{f_rate} u/h`")

    with st.form("oee_form", clear_on_submit=True):
        st.markdown(f"***Capturando datos para: {f_maquina}***")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            f_fecha = st.date_input("Fecha", date.today())
            f_hora = st.number_input("Hora (0-23)", min_value=0, max_value=23, value=datetime.now().hour)

        with col2:
            f_turno = st.selectbox("Turno", [1, 2, 3])
            f_tiempo_prog = st.number_input("Tiempo Programado (min)", min_value=0, value=60)

        with col3:
            f_producido = st.number_input("Total Producido", min_value=0)

        with col4:
            f_scrap = st.number_input("Scrap (Cantidad)", min_value=0)

        st.markdown("#### 🛑 Tiempos Muertos (Minutos)")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1: f_ajuste = st.number_input("Ajuste", min_value=0)
        with c2: f_mec = st.number_input("Falla Mecánica", min_value=0)
        with c3: f_elec = st.number_input("Falla Eléctrica", min_value=0)
        with c4: f_per = st.number_input("Falta Personal", min_value=0)
        with c5: f_mat = st.number_input("Falta Material", min_value=0)
        with c6: f_mod = st.number_input("Cambio Modelo", min_value=0)

        submitted = st.form_submit_button("💾 Guardar Registro", type="primary")

        if submitted:
            metrics = calculate_metrics(f_tiempo_prog, f_rate, f_producido, f_scrap,
                                     f_ajuste, f_mec, f_elec, f_per, f_mat, f_mod)

            payload = {
                "fecha": f_fecha.isoformat(),
                "hora": f_hora,
                "turno": f_turno,
                "maquina": f_maquina,
                "tiempo_programado_min": f_tiempo_prog,
                "rate_teorico": f_rate,
                "producido": f_producido,
                "scrap": f_scrap,
                "ajuste": f_ajuste,
                "falla_mecanica": f_mec,
                "falla_electrica": f_elec,
                "falta_personal": f_per,
                "falta_material": f_mat,
                "cambio_modelo": f_mod,
                "tiempo_muerto": metrics["tiempo_muerto"],
                "tiempo_funcionamiento": metrics["tiempo_funcionamiento"],
                "disponibilidad": metrics["disponibilidad"],
                "rendimiento": metrics["rendimiento"],
                "calidad": metrics["calidad"],
                "oee": metrics["oee"],
                "scrap_pct": metrics["scrap_pct"],
                "ftt": metrics["ftt"]
            }

            if db:
                if db.insert_record(payload):
                    st.success(f"✅ Guardado {f_maquina} - FTT: {metrics['ftt']:.2f}% | Scrap: {metrics['scrap_pct']:.2f}%")
                else:
                    st.error("❌ Error en BD.")

# -----------------------------------------------------------------------------
# TAB 3: REPORTES
# -----------------------------------------------------------------------------
def aplicar_semaforo(val):
    if val < 70:
        color = '#ef4444'
    elif val < 85:
        color = '#f59e0b'
    else:
        color = '#10b981'
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

    if not db:
        st.error("⚠️ Sin conexión a la base de datos.")
    elif len(filter_date_range) == 2:
        start_d, end_d = filter_date_range
        raw_df_rep = db.fetch_records(start_d, end_d)

        if not raw_df_rep.empty:
            st.markdown("### 🔍 Refinar Reporte")
            c_f1 = st.columns(1)[0]
            with c_f1:
                turnos_disponibles = [1, 2, 3]
                rep_filter_turn = st.multiselect("Filtrar por Turno", turnos_disponibles, default=[1, 2, 3])

            df_rep = raw_df_rep[
                (raw_df_rep['maquina'].isin(filter_maquina)) &
                (raw_df_rep['turno'].isin(rep_filter_turn))
            ].copy()

            if not df_rep.empty:
                # --- MÉTRICAS GLOBALES (PROMEDIOS) ---
                ftt_global_rep = df_rep['ftt'].mean()
                scrap_global_rep = df_rep['scrap_pct'].mean()
                total_prod_rep = df_rep['producido'].sum()

                # --- PREPARACIÓN DE LA TABLA (usando columnas ya existentes) ---
                df_rep['tiempo_prog_hrs'] = (df_rep['tiempo_programado_min'] / 60).round(2)

                vista_tabla = df_rep[['fecha', 'hora', 'turno', 'maquina', 'tiempo_prog_hrs',
                                      'producido', 'scrap', 'scrap_pct', 'ftt',
                                      'disponibilidad', 'rendimiento', 'oee']].copy()
                cols_kpi = ['scrap_pct', 'ftt', 'disponibilidad', 'rendimiento', 'oee']
                vista_tabla[cols_kpi] = vista_tabla[cols_kpi].round(2)

                st.markdown("### 🌎 Resumen Global del Período")
                c_g1, c_g2, c_g3 = st.columns(3)
                c_g1.metric("Total Producido", f"{total_prod_rep:,} pzas")
                c_g2.metric("FTT Global (Promedio)", f"{ftt_global_rep:.2f}%")
                c_g3.metric("Scrap Global (Promedio)", f"{scrap_global_rep:.2f}%", delta_color="inverse")
                st.markdown("---")

                st.subheader("Detalle de Operaciones Individuales")
                try:
                    styled_pivot = vista_tabla.style.map(aplicar_semaforo, subset=['oee', 'rendimiento', 'ftt'])
                except:
                    styled_pivot = vista_tabla.style.applymap(aplicar_semaforo, subset=['oee', 'rendimiento', 'ftt'])
                st.dataframe(styled_pivot, use_container_width=True)

                # --- GRÁFICAS (con promedios) ---
                def avg_metrics_report(x):
                    return pd.Series({
                        'oee': x['oee'].mean(),
                        'disponibilidad': x['disponibilidad'].mean(),
                        'rendimiento': x['rendimiento'].mean(),
                        'ftt': x['ftt'].mean(),
                        'scrap_pct': x['scrap_pct'].mean()
                    })

                df_mach_rep = df_rep.groupby('maquina').apply(avg_metrics_report, include_groups=False).reset_index()
                df_daily_rep = df_rep.groupby('fecha').apply(avg_metrics_report, include_groups=False).reset_index()

                c1, c2 = st.columns(2)
                with c1:
                    fig_bar = px.bar(df_mach_rep, x='maquina', y='oee', color='oee',
                                    color_continuous_scale='RdYlGn', title="OEE por Máquina (Promedio)",
                                    hover_data={'oee': ':.2f}%', 'ftt': ':.2f}%', 'scrap_pct': ':.2f}%'})
                    st.plotly_chart(fig_bar, use_container_width=True)
                with c2:
                    fig_trend = px.line(df_daily_rep, x='fecha', y='oee', markers=True,
                                        title="Tendencia Diaria (Promedio)",
                                        hover_data={'oee': ':.2f}%', 'ftt': ':.2f}%', 'scrap_pct': ':.2f}%'})
                    st.plotly_chart(fig_trend, use_container_width=True)

                # Pareto de Fallas
                st.subheader("Análisis de Tiempos Muertos")
                failure_cols = ['ajuste', 'falla_mecanica', 'falla_electrica', 'falta_personal', 'falta_material', 'cambio_modelo']
                failures_rep = df_rep[failure_cols].sum().sort_values(ascending=False).reset_index()
                failures_rep.columns = ['Falla', 'Minutos']
                failures_rep['Acumulado'] = (failures_rep['Minutos'].cumsum() / failures_rep['Minutos'].sum() * 100).fillna(0)

                fig_pareto = make_subplots(specs=[[{"secondary_y": True}]])
                fig_pareto.add_trace(go.Bar(x=failures_rep['Falla'], y=failures_rep['Minutos'], name="Minutos", marker_color="#ef4444"), secondary_y=False)
                fig_pareto.add_trace(go.Scatter(x=failures_rep['Falla'], y=failures_rep['Acumulado'], name="% Acumulado", marker_color="#3b82f6"), secondary_y=True)
                fig_pareto.update_layout(title="Pareto Global de Fallas", template="plotly_dark")
                st.plotly_chart(fig_pareto, use_container_width=True)

                # --- REPORTE HTML ---
                logo_b64 = get_image_base64("EA_2.png")
                logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width:120px; position:absolute; top:30px; left:30px;">' if logo_b64 else ""

                html_table = styled_pivot.to_html()

                html_kpis_globales = f"""
                <div style="display: flex; justify-content: space-around; background-color: #1e293b; padding: 20px; border-radius: 10px; border: 1px solid #334155; margin-bottom: 30px;">
                    <div>
                        <h2 style="color: #38bdf8; margin: 0; font-size: 2em;">{total_prod_rep:,}</h2>
                        <p style="margin: 0; color: #94a3b8; font-weight: bold; text-transform: uppercase;">Total Producido</p>
                    </div>
                    <div>
                        <h2 style="color: #10b981; margin: 0; font-size: 2em;">{ftt_global_rep:.2f}%</h2>
                        <p style="margin: 0; color: #94a3b8; font-weight: bold; text-transform: uppercase;">FTT Global (Promedio)</p>
                    </div>
                    <div>
                        <h2 style="color: #ef4444; margin: 0; font-size: 2em;">{scrap_global_rep:.2f}%</h2>
                        <p style="margin: 0; color: #94a3b8; font-weight: bold; text-transform: uppercase;">Scrap Global (Promedio)</p>
                    </div>
                </div>
                """

                dark_layout = dict(
                    template="plotly_dark",
                    paper_bgcolor="#0f172a",
                    plot_bgcolor="#0f172a",
                    font=dict(color="#f8fafc"),
                )

                fig_bar.update_layout(**dark_layout)
                fig_trend.update_layout(**dark_layout)
                fig_pareto.update_layout(**dark_layout)

                fig_trend.update_traces(
                    line=dict(color="#38bdf8", width=3),
                    marker=dict(size=6, color="#38bdf8"),
                    mode="lines+markers"
                )

                reporte_completo = f"""
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>Reporte Ejecutivo OEE Rotarys | EA Innovation</title>
                    <style>
                        body {{
                            background-color: #0f172a;
                            color: #f8fafc;
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            margin: 0;
                            padding: 40px;
                            text-align: center;
                        }}
                        .page {{
                            max-width: 1100px;
                            margin: 0 auto 50px auto;
                            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                            padding: 60px 50px 50px 50px;
                            border-radius: 15px;
                            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
                            border: 1px solid #334155;
                            min-height: 1000px;
                            position: relative;
                        }}
                        h1 {{ color: #38bdf8; font-size: 2.5em; margin-bottom: 10px; }}
                        h3 {{ color: #94a3b8; border-bottom: 1px solid #334155; padding-bottom: 10px; margin-top: 40px; }}
                        p {{ color: #94a3b8; font-size: 1.2em; margin: 5px 0; }}
                        table {{
                            width: 100%;
                            border-collapse: collapse;
                            margin: 30px auto;
                            background-color: rgba(15, 23, 42, 0.6);
                            border-radius: 10px;
                            overflow: hidden;
                            font-size: 0.9em;
                        }}
                        th {{
                            background-color: #334155;
                            color: #38bdf8;
                            padding: 15px;
                            text-align: center;
                            text-transform: uppercase;
                        }}
                        td {{
                            padding: 12px;
                            border-bottom: 1px solid #334155;
                            text-align: center;
                        }}
                        .chart-container {{
                            background-color: #0f172a;
                            border: 1px solid #334155;
                            border-radius: 12px;
                            padding: 10px;
                            margin: 20px auto;
                            max-width: 100%;
                        }}
                        .page-break {{ page-break-before: always; }}
                        .footer {{
                            margin-top: 60px;
                            font-size: 0.9em;
                            color: #64748b;
                            border-top: 1px solid #334155;
                            padding-top: 20px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="page">
                        {logo_html}
                        <h1>EA Innovation Suite</h1>
                        <p>Reporte de Desempeño OEE - Área de Rotarys</p>
                        <p style="font-size: 1em; opacity: 0.8; margin-bottom: 30px;">Período: {start_d} al {end_d}</p>

                        {html_kpis_globales}

                        <h3>Listado Detallado de Operaciones (Rotarys)</h3>
                        <div style="overflow-x: auto;">
                            {html_table}
                        </div>

                        <h3>Análisis Comparativo por Máquina (OEE / FTT / Scrap Promedio)</h3>
                        <div class="chart-container">
                            {fig_bar.to_html(full_html=False, include_plotlyjs='cdn')}
                        </div>

                        <div class="footer">
                            Generado por Master Engineer Erik Armenta | EA Innovation Suite 2026
                        </div>
                    </div>

                    <div class="page-break"></div>

                    <div class="page">
                        {logo_html}
                        <h1>Análisis de Tendencias e Interrupciones</h1>
                        <p>Productividad y Eficiencia de Máquinas</p>

                        <h3>Comportamiento Diario del OEE (Promedio)</h3>
                        <div class="chart-container">
                            {fig_trend.to_html(full_html=False, include_plotlyjs=False)}
                        </div>

                        <h3>Pareto Global de Tiempos Muertos (Minutos)</h3>
                        <div class="chart-container">
                            {fig_pareto.to_html(full_html=False, include_plotlyjs=False)}
                        </div>

                        <div class="footer">
                            Este reporte constituye una auditoría técnica de EA Innovation. <br>
                            Cálculos basados en promedios de los valores registrados.
                        </div>
                    </div>
                </body>
                </html>
                """

                col1, col2 = st.columns(2)
                with col1: st.download_button("📊 Descargar Reporte Completo", reporte_completo, f"Reporte_OEE_Rotarys_{start_d}.html", "text/html", use_container_width=True)
                with col2: st.download_button("📊 Descargar Datos CSV", df_rep.to_csv(index=False).encode('utf-8'), "datos_oee_rotarys.csv", "text/csv", use_container_width=True)
            else:
                st.warning("No hay datos para los filtros seleccionados.")
        else:
            st.info("No se encontraron registros en el rango de fechas seleccionado.")
