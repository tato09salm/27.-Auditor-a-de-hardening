"""
Aplicación Principal Streamlit: Sistema de Investigación Científica en Deep Learning y Visión Artificial.
Estructurado según el Plan de Desarrollo Fases 0 a 7.
"""

from __future__ import annotations

import streamlit as st
from modules.data_module import render_data_module
from modules.training_module import render_training_module
from modules.evaluation_module import render_evaluation_module
from modules.explainability_module import render_explainability_module
from modules.reports_module import render_reports_module
from modules.inference_module import render_inference_module
from modules.optuna_ui_module import render_optuna_ui_module

# Configuración de página con diseño ancho y título formal
st.set_page_config(
    page_title="DeepVision Lab - Streamlit Research Platform",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS personalizados para apariencia de artículo científico
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4b5563;
        margin-bottom: 1.5rem;
    }
    .badge-q1 {
        background-color: #dbeafe;
        color: #1e40af;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 6px;
    }
    .phase-card {
        padding: 1.2rem;
        background: #f8fafc;
        border-left: 4px solid #3b82f6;
        border-radius: 6px;
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar de Navegación por Fases
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=64)
    st.markdown("### 🛡️ CIS Hardening Lab")
    st.markdown("<span class='badge-q1'>Q1 Framework</span> <span class='badge-q1'>Nested CV 5x3</span>", unsafe_allow_html=True)
    st.markdown("---")

    phase = st.radio(
        "Fases del Proyecto:",
        [
            "Fase 1: Módulo de Datos (MVP)",
            "Fase 2: Módulo de Entrenamiento",
            "Fase 3: Módulo de Evaluación",
            "Fase 4: Módulo de Explicabilidad (Grad-CAM++)",
            "Fase 5: Módulo de Reportes (600 DPI)",
            "Fase 6: Módulo de Inferencia",
            "Fase 7: Optimización Optuna UI",
        ],
        index=0,
    )

    st.markdown("---")
    st.markdown("#### ⚙️ Parámetros de Entorno:")
    st.caption("• **Plataforma:** Python 3.11 + Streamlit\n• **Motor:** PyTorch / Optuna\n• **División:** 70% Dev / 15% Val / 15% Test\n• **CV:** 5 Folds Externos × 3 Inner")

# Contenido Principal
st.markdown("<div class='main-header'>Plataforma de Investigación en Hardening de Servidores (CIS Benchmarks)</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Pipeline reproducible para auditoría de seguridad Linux con CV anidada 5x3, explicabilidad Grad-CAM++ y reportes para revistas Q1.</div>", unsafe_allow_html=True)

if phase == "Fase 1: Módulo de Datos (MVP)":
    render_data_module()

elif phase == "Fase 2: Módulo de Entrenamiento":
    render_training_module()

elif phase == "Fase 3: Módulo de Evaluación":
    render_evaluation_module()

elif phase == "Fase 4: Módulo de Explicabilidad (Grad-CAM++)":
    render_explainability_module()

elif phase == "Fase 5: Módulo de Reportes (600 DPI)":
    render_reports_module()

elif phase == "Fase 6: Módulo de Inferencia":
    render_inference_module()

elif phase == "Fase 7: Optimización Optuna UI":
    render_optuna_ui_module()

