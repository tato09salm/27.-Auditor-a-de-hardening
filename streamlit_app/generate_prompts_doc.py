"""
Generador del Documento Oficial de Prompts Mejorados: PromptMejorado.docx.
Reúne de forma estructurada los prompts de ingeniería para las Fases 1 a 7.
"""

from __future__ import annotations

import os
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Inches, Pt, RGBColor


def add_prompt_block(doc, phase_title: str, prompt_text: str):
    h = doc.add_heading(phase_title, level=1)
    h.paragraph_format.space_before = Pt(14)
    h.paragraph_format.space_after = Pt(6)

    table = doc.add_table(rows=1, cols=1)
    table.alignment = 1
    cell = table.rows[0].cells[0]
    cell.width = Inches(6.5)

    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F1F5F9"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(prompt_text.strip())
    r.font.name = "Consolas"
    r.font.size = Pt(8.5)
    r.font.color.rgb = RGBColor(30, 41, 59)


def generate_prompts_doc(output_path: str):
    doc = Document()
    for s in doc.sections:
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)

    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_t = t.add_run("Compendio de Prompts Mejorados — Plan de Desarrollo Streamlit App")
    r_t.font.name = "Arial"
    r_t.font.size = Pt(18)
    r_t.font.bold = True
    r_t.font.color.rgb = RGBColor(30, 58, 138)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run("Auditoría de Hardening de Servidores Linux (CIS Benchmarks) · Fases 1 a 7")
    r_sub.font.size = Pt(11)
    r_sub.font.italic = True
    p_sub.paragraph_format.space_after = Pt(20)

    # FASE 1
    add_prompt_block(
        doc,
        "FASE 1: MVP — Módulo de Datos (Ingestión, Metadata, Inspección y Fuga)",
        """Actúa como Arquitecto de Software Científico e Ingeniero Senior de Machine Learning.
Desarrolla el Módulo de Datos (Fase 1) en Streamlit para un dataset de auditoría de hardening de servidores Linux (CIS Benchmarks).
Especificaciones obligatorias:
1. Ingestión de matrices de postura de seguridad 2D (Security Posture Matrices de 224x224 px) y archivo CSV de metadatos de servidores.
2. Editor interactivo de metadata mediante st.data_editor con soporte para filtrado dinámico, modificación de estados y descarga en CSV.
3. Visualizador y galería de matrices con paginación, filtros por postura (Hardened, Vulnerable, Exposed) e histogramas cromáticos RGB de superficie de ataque.
4. Validación rigurosa de independencia de infraestructura: verificación de integridad 1:1 y prevención de fuga de clusters/subredes entre Train, Val y Test.
5. Estadística descriptiva con formato de publicación Q1 (Tabla 1) con Media, DE, Mediana, IQR, asimetría, curtosis y prueba de Shapiro-Wilk, acompañada de explicabilidad metodológica en lenguaje natural."""
    )

    # FASE 2
    add_prompt_block(
        doc,
        "FASE 2: Módulo de Entrenamiento (Nested CV 5x3 y Optuna)",
        """Actúa como Científico de Datos Senior y Especialista en Aprendizaje Estadístico para Ciberseguridad.
Desarrolla el Módulo de Entrenamiento (Fase 2) en Streamlit implementando el esquema más riguroso contra el sobreajuste:
1. Partición estricta: Desarrollo (70%), Validación (15%) y Prueba Ciega Independiente (15%).
2. Selector de arquitecturas: Ensamble de árboles (Random Forest), Boosting adaptativo (Gradient Boosting) y Deep Learning residual (ResNet-18).
3. Estructura de Validación Cruzada Anidada (Nested CV 5x3):
   - 5 Folds Externos (Outer Folds) + 3 Folds Internos (Inner Folds).
   - En CADA fold externo: optimización bayesiana de hiperparámetros con Optuna sobre los inner folds; reentrenamiento completo con los mejores parámetros sobre outer_train; evaluación imparcial UNA SOLA VEZ sobre outer_val.
4. Monitoreo en tiempo real con barra de progreso y métricas consolidadas (Media ± Desv. Est.).
5. Tablas y gráficos de estabilidad inter-fold y convergencia bayesiana con interpretabilidad metodológica."""
    )

    # FASE 3
    add_prompt_block(
        doc,
        "FASE 3: Módulo de Evaluación Diagnóstica y Pruebas Estadísticas",
        """Actúa como Bioestadístico Senior y Evaluador de Algoritmos de Clasificación Crítica.
Desarrolla el Módulo de Evaluación (Fase 3) en Streamlit orientado a revistas Q1:
1. Métricas globales con intervalos de confianza al 95% calculados por Bootstrap (B=500 iteraciones): Accuracy, Kappa de Cohen, MCC y F1 macro.
2. Rendimiento desglosado por clase: Sensibilidad (Recall), Especificidad, Precisión (VPP), VPN y F1-Score.
3. Matrices de confusión multiclase interactivas con Plotly: conteo absoluto y normalizada por filas para visualizar errores Tipo I y Tipo II.
4. Curvas de discriminabilidad: Curvas ROC (One-vs-Rest) con cálculo explícito de AUC por clase y curvas Precision-Recall (PR).
5. Pruebas de hipótesis formales: Prueba de rangos con signo de Wilcoxon inter-fold con cálculo de estadístico W y p-valor (p < 0.05), más calibración con Brier Score."""
    )

    # FASE 4
    add_prompt_block(
        doc,
        "FASE 4: Módulo de Explicabilidad (XAI con Grad-CAM++)",
        """Actúa como Investigador Senior en IA Explicable (XAI) y Visión Artificial Aplicada a Ciberseguridad.
Desarrolla el Módulo de Explicabilidad (Fase 4) en Streamlit:
1. Grad-CAM++ (Gradient-weighted Class Activation Mapping++) aplicado sobre matrices de configuración de servidores Linux.
2. Control interactivo de opacidad (deslizador Alpha) para superponer el mapa térmico Jet sobre la matriz del servidor.
3. Visualización comparativa cuádruple: (1) Matriz original, (2) Superposición Grad-CAM++, (3) Mapa de atención/saliencia, (4) Máscara binaria del foco de controles vulnerados (SSH, Firewall, Kernel).
4. Cuantificación rigurosa de métricas XAI: Energy in ROI (> 70%), Pointing Game en reglas críticas, Average Drop (< 10%) y Faithfulness causal (Spearman r > 0.75).
5. Explicabilidad clínica/técnica que descarte atajos de aprendizaje (Clever Hans effect)."""
    )

    # FASE 5
    add_prompt_block(
        doc,
        "FASE 5: Módulo de Reportes Científicos (Figuras a 600 DPI y Exportación)",
        """Actúa como Editor Técnico de Revistas Científicas de Alto Impacto (IEEE / Elsevier).
Desarrolla el Módulo de Reportes (Fase 5) en Streamlit:
1. Generador de figuras editoriales nativas a ultra-alta resolución (600 DPI) con matplotlib (Curvas ROC y PR listas para imprenta) y botón de descarga directa en PNG.
2. Tablas científicas con formato estandarizado APA y notas metodológicas al pie de tabla.
3. Exportación multiformato en un solo clic:
   - Libro de datos Excel (.xlsx) estructurado en múltiples hojas con openpyxl.
   - Manuscrito Word borrador (.docx) con python-docx.
   - Informe formal ejecutivo (.pdf) con reportlab."""
    )

    # FASE 6
    add_prompt_block(
        doc,
        "FASE 6: Módulo de Inferencia, Severidad y Remediación Asistida",
        """Actúa como Especialista en Sistemas de Apoyo a la Decisión en Ciberseguridad (SecOps / Hardening).
Desarrolla el Módulo de Inferencia (Fase 6) en Streamlit conectado con el modelo real entrenado:
1. Evaluación interactiva de nuevos servidores o matrices del inventario.
2. Predicción de postura (Hardened, Vulnerable, Exposed) con distribución de probabilidad a posteriori y cuantificación de incertidumbre diagnóstica mediante entropía normalizada de Shannon.
3. Estratificación cuantitativa de severidad de riesgo (0 a 100 puntos) con tarjeta de estado cromática (Verde / Ámbar / Rojo).
4. Recomendación operativa y formulación automática de los comandos Bash de remediación específicos para Linux (ej. desactivar PermitRootLogin en sshd_config, habilitar cortafuegos UFW, configurar auditd)."""
    )

    # FASE 7
    add_prompt_block(
        doc,
        "FASE 7: Módulo de Optimización Optuna UI y Visualización Bayesiana",
        """Actúa como Ingeniero Senior de AutoML y Optimización de Hiperparámetros.
Desarrolla el Módulo de Optimización Optuna UI (Fase 7) en Streamlit:
1. Configuración interactiva del espacio de búsqueda con soporte para algoritmos TPESampler, CmaEsSampler y RandomSampler.
2. Monitoreo en tiempo real de ensayos (trials) con tabla histórica detallada, métrica objetivo y registro de hiperparámetros explorados.
3. Tres visualizaciones canónicas interactivas de Optuna en Plotly:
   - Historial de optimización y convergencia del mejor valor acumulado.
   - Importancia relativa de hiperparámetros (gráfico de barras de varianza explicada).
   - Coordenadas paralelas multidimensionales para mapear las trayectorias hacia la meseta de máximo rendimiento.
4. Explicabilidad metodológica sobre la sensibilidad del espacio de búsqueda para la sección experimental del artículo."""
    )

    doc.save(output_path)
    print(f"✅ Documento de Prompts generado exitosamente en: {output_path}")


if __name__ == "__main__":
    out_file = os.path.join(os.getcwd(), "PromptMejorado.docx")
    generate_prompts_doc(out_file)

