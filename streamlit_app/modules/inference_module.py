"""
Fase 6: Módulo de Inferencia de Hardening con Modelo Real Entrenado y Serializado.
Carga el modelo óptimo guardado en models/best_hardening_model.joblib y realiza predicción real.
"""

from __future__ import annotations

import os
import joblib
import numpy as np
import pandas as pd
from PIL import Image
import plotly.graph_objects as go
import streamlit as st


@st.cache_resource
def load_trained_model():
    """Carga el modelo de machine learning real serializado con joblib."""
    model_path = os.path.join(os.getcwd(), "models", "best_hardening_model.joblib")
    if os.path.exists(model_path):
        return joblib.load(model_path)
    return None


def compute_server_severity(probs: dict[str, float], open_ports: int, cis_score: float) -> tuple[float, str, str]:
    """Calcula un score continuo de severidad (0-100) y su categoría de riesgo de seguridad."""
    prob_exposed = probs.get("Exposed", 0.0)
    prob_vuln = probs.get("Vulnerable", 0.0)

    severity_score = (prob_exposed * 60.0) + (prob_vuln * 30.0) + (min(10.0, open_ports * 1.5)) + ((100.0 - cis_score) * 0.1)
    severity_score = round(max(0.0, min(100.0, severity_score)), 1)

    if severity_score >= 65.0:
        risk_level = "CRÍTICO / ALTA SUPERFICIE DE ATAQUE"
        risk_color = "#dc2626"
    elif severity_score >= 35.0:
        risk_level = "MODERADO / VULNERABILIDADES DETECTADAS"
        risk_color = "#f59e0b"
    else:
        risk_level = "SEGURO / POSTURA HARDENED"
        risk_color = "#16a34a"

    return severity_score, risk_level, risk_color


def render_inference_module():
    st.markdown("## ⚡ Fase 6: Módulo de Inferencia de Hardening (Modelo Real Entrenado)")
    st.caption("Inferencia diagnóstica en tiempo real utilizando el clasificador optimizado con Optuna y guardado en disco.")

    model_payload = load_trained_model()
    images_dict = st.session_state.get("images_dict", {})
    df_meta = st.session_state.get("df_metadata")

    if model_payload:
        st.success(f"🧠 **Modelo Activo en Memoria:** `{model_payload['model_name']}` (Exactitud en Test: `{model_payload['test_accuracy']*100:.1f}%` | Hiperparámetros Optuna: `{model_payload['best_params']}`)")
    else:
        st.warning("⚠️ No se encontró el modelo serializado en disco. Ejecute el entrenamiento.")

    col_inf1, col_inf2 = st.columns([1, 1])

    with col_inf1:
        st.markdown("#### 1. Ingestión de Matriz de Servidor")
        upload_mode = st.radio("Origen de la Matriz:", ["Seleccionar del Inventario", "Subir Matriz de Servidor (.PNG/.JPG)"], horizontal=True)

        input_img = None
        srv_name = ""

        if upload_mode == "Seleccionar del Inventario" and images_dict:
            srv_name = st.selectbox("Seleccione un servidor para diagnosticar:", list(images_dict.keys()))
            if srv_name:
                input_img = images_dict[srv_name]
        else:
            up_file = st.file_uploader("Subir matriz de configuración:", type=["png", "jpg", "jpeg"])
            if up_file:
                input_img = Image.open(up_file).copy()
                srv_name = up_file.name

        if input_img:
            st.image(input_img, caption=f"Matriz de Servidor: {srv_name}", width=260)

    with col_inf2:
        st.markdown("#### 2. Clasificación de Postura y Probabilidades (Inferencia Real)")
        if input_img is None:
            st.info("👈 Seleccione o cargue un servidor para evaluar.")
            return

        arr = np.array(input_img, dtype=np.float32)
        gray = np.array(input_img.convert("L"), dtype=np.float32)
        gy, gx = np.gradient(gray)
        sharpness = float(np.mean(gx**2 + gy**2))
        contrast = float(np.std(gray))

        mean_r = float(np.mean(arr[:, :, 0]))
        mean_g = float(np.mean(arr[:, :, 1]))
        mean_b = float(np.mean(arr[:, :, 2]))

        # Si tenemos metadata para este servidor, usar sus datos reales; de lo contrario inferir
        cis_score = 75.0
        failed_ctrl = 4
        open_ports = 3

        if df_meta is not None and srv_name in df_meta["filename"].values:
            row_meta = df_meta[df_meta["filename"] == srv_name].iloc[0]
            cis_score = float(row_meta.get("cis_score", 75.0))
            failed_ctrl = int(row_meta.get("failed_controls", 4))
            open_ports = int(row_meta.get("open_ports", 3))

        # Vector de características real
        feature_vector = np.array([[cis_score, failed_ctrl, open_ports, mean_r, mean_g, mean_b, contrast, sharpness]])

        if model_payload:
            clf = model_payload["model"]
            classes = model_payload["classes"]
            real_probs = clf.predict_proba(feature_vector)[0]
            probs = {classes[i]: float(real_probs[i]) for i in range(len(classes))}
            predicted_class = classes[int(np.argmax(real_probs))]
            confidence = probs[predicted_class] * 100
        else:
            probs = {"Hardened": 0.33, "Vulnerable": 0.33, "Exposed": 0.34}
            predicted_class = "Vulnerable"
            confidence = 33.3

        p_vec = np.array(list(probs.values()))
        entropy = -np.sum(p_vec * np.log2(p_vec + 1e-9)) / np.log2(len(p_vec))

        st.success(f"### Postura Predicha: **{predicted_class.upper()}** (Confianza: {confidence:.1f}%)")
        st.caption(f"Incertidumbre Diagnóstica (Entropía): `{entropy:.3f}` | CIS Evaluado: `{cis_score}%`")

        fig_probs = go.Figure(go.Bar(
            x=list(probs.values()),
            y=list(probs.keys()),
            orientation="h",
            marker_color=["#10b981" if k == "Hardened" else "#f59e0b" if k == "Vulnerable" else "#ef4444" for k in probs.keys()],
            text=[f"{v*100:.1f}%" for v in probs.values()],
            textposition="auto",
        ))
        fig_probs.update_layout(xaxis=dict(range=[0, 1.05], title="Probabilidad a Posteriori (Modelo Real)"), height=200, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_probs, use_container_width=True)

    st.divider()

    st.markdown("### 3. Estratificación de Riesgo y Plan de Remediación")
    sev_score, risk_lvl, risk_color = compute_server_severity(probs, open_ports, cis_score)

    c_s1, c_s2, c_s3 = st.columns([1, 1, 2])

    with c_s1:
        st.metric("Puntuación de Severidad CIS", f"{sev_score} / 100", help="Índice continuo que pondera exposición y controles no conformes.")

    with c_s2:
        st.markdown("**Estratificación de Riesgo:**")
        st.markdown(f"<div style='background-color:{risk_color}; color:white; padding:8px 14px; border-radius:6px; font-weight:700; text-align:center;'>{risk_lvl}</div>", unsafe_allow_html=True)

    with c_s3:
        st.markdown("**Comandos de Remediación de Hardening Sugeridos:**")
        if predicted_class == "Exposed":
            commands = """# 1. Deshabilitar login directo de root en SSH
sudo sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
# 2. Habilitar y configurar Firewall UFW
sudo ufw default deny incoming && sudo ufw default allow outgoing && sudo ufw enable
# 3. Forzar aleatorización de memoria (ASLR)
sudo sysctl -w kernel.randomize_va_space=2"""
        elif predicted_class == "Vulnerable":
            commands = """# 1. Habilitar servicio de bitácora y auditoría
sudo systemctl enable --now auditd
# 2. Configurar política de bloqueo por intentos fallidos (faillock)
sudo authselect select sssd with-faillock --force"""
        else:
            commands = "# Postura Conforme (Hardened): El servidor cumple los controles base CIS."

        st.code(commands, language="bash")
