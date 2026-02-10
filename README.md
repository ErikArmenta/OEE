# Sistema de Gestión OEE - EA Innovation

Este es un dashboard interactivo para el cálculo y monitoreo del **OEE (Overall Equipment Effectiveness)**, diseñado para reemplazar flujos de trabajo basados en Excel con una aplicación web moderna y centralizada.

## Características

-   **Dashboard en Tiempo Real**: Visualización de OEE, Disponibilidad, Rendimiento y Calidad con gráficos de anillo (Altair) y líneas de tendencia (Plotly).
-   **Captura de Datos**: Formulario optimizado para operadores (basado en "Celdas Naranjas") con cálculo automático de métricas y tiempos muertos.
-   **Base de Datos**: Integración con **Supabase** para almacenamiento seguro y persistente en la nube.
-   **Reportes Inteligentes**: Generación de reportes HTML interactivos de 2 páginas y exportación a CSV.
-   **Personalización**: Meta de OEE ajustable y filtros dinámicos por línea y turno.

## Instalación Local

1.  Clonar el repositorio:
    ```bash
    git clone <tu-repositorio>
    cd Dashboard_OEE
    ```

2.  Instalar dependencias:
    ```bash
    pip install -r requirements.txt
    ```

3.  Configurar Secretos:
    Crear un archivo `.streamlit/secrets.toml` con tus credenciales de Supabase:
    ```toml
    [supabase]
    url = "TU_SUPABASE_URL"
    key = "TU_SUPABASE_ANON_KEY"
    ```

4.  Ejecutar la aplicación:
    ```bash
    streamlit run OEE_Dash.py
    ```

## Despliegue en Streamlit Cloud

1.  Sube este código a un repositorio de GitHub.
2.  Inicia sesión en [share.streamlit.io](https://share.streamlit.io/).
3.  Haz clic en **"New App"** y selecciona tu repositorio.
4.  **IMPORTANTE**: Antes de desplegar, ve a "Advanced Settings" (Configuración Avanzada) en el área de despliegue.
5.  Copia el contenido de tu archivo local `.streamlit/secrets.toml` y pégalo en el área de "Secrets" de Streamlit Cloud.
6.  Haz clic en **Deploy**.

## Estructura del Proyecto

-   `OEE_Dash.py`: Aplicación principal.
-   `modules/supabase_client.py`: Manejador de conexión a base de datos.
-   `modules/schema.sql`: Script SQL para crear la tabla en Supabase.
-   `requirements.txt`: Lista de librerías Python necesarias.

---
Desarrollado para **EA Innovation**
