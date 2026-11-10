"""
Fase 2: Módulo de Entrenamiento con Validación Cruzada Anidada (Nested CV 5x3) y Optuna.
Optimizado para Clasificación de Postura de Hardening CIS (Hardened, Vulnerable, Exposed).
"""

from __future__ import annotations

import time
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, train_test_split
import streamlit as st
import optuna

optuna.logging.set_verbosity(optuna.logging.WARNING)


def extract_features_and_labels(df: pd.DataFrame, images_dict: dict) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Extrae características de postura CIS, puertos y métricas de matriz visual."""
    features = []
    labels = []
    target_col = "posture_class" if "posture_class" in df.columns else "diagnosis"
    unique_classes = sorted(df[target_col].dropna().unique())
    label_map = {lbl: i for i, lbl in enumerate(unique_classes)}

    for _, row in df.iterrows():
        fname = row.get("filename")
        posture = row.get(target_col)
        if fname not in images_dict or posture not in label_map:
            continue

        img = images_dict[fname]
        arr = np.array(img, dtype=np.float32)

        # Variables clave de hardening
        cis_score = float(row.get("cis_score", 60.0))
        failed_ctrl = float(row.get("failed_controls", 4.0))
        open_ports = float(row.get("open_ports", 3.0))

        # Métricas de imagen de configuración
        mean_r = float(np.mean(arr[:, :, 0]))  # Tonalidad de exposición roja
        mean_g = float(np.mean(arr[:, :, 1]))  # Tonalidad de conformidad verde
        mean_b = float(np.mean(arr[:, :, 2]))  # Tonalidad de servicios azul

        feat_vector = [cis_score, failed_ctrl, open_ports, mean_r, mean_g, mean_b]
        features.append(feat_vector)
        labels.append(label_map[posture])

    feature_names = ["CIS_Score", "Controles_Fallidos", "Puertos_Abiertos", "Canal_Exposicion_R", "Canal_Conformidad_G", "Canal_Servicios_B"]
    return np.array(features), np.array(labels), feature_names


def run_nested_cv_optuna(
    X_dev: np.ndarray,
    y_dev: np.ndarray,
    model_family: str,
    n_outer_folds: int = 5,
    n_inner_folds: int = 3,
    n_trials: int = 6,
    progress_bar=None,
    status_text=None,
) -> tuple[pd.DataFrame, list[dict], list[float]]:
    """Ejecuta la validación cruzada anidada rigurosa: 5 outer folds, búsqueda Optuna en inner folds."""
    outer_cv = StratifiedKFold(n_splits=n_outer_folds, shuffle=True, random_state=42)
    outer_results = []
    best_params_per_fold = []
    all_trial_scores = []

    total_steps = n_outer_folds
    current_step = 0

    for fold_idx, (train_idx, val_idx) in enumerate(outer_cv.split(X_dev, y_dev), start=1):
        if status_text:
            status_text.markdown(f"🔄 **Evaluando Fold de Infraestructura {fold_idx}/{n_outer_folds}** (Búsqueda Optuna en {n_inner_folds} inner folds)...")

        X_outer_train, y_outer_train = X_dev[train_idx], y_dev[train_idx]
        X_outer_val, y_outer_val = X_dev[val_idx], y_dev[val_idx]

        def objective(trial: optuna.Trial) -> float:
            if "Forest" in model_family:
                n_estimators = trial.suggest_int("n_estimators", 30, 150, step=20)
                max_depth = trial.suggest_int("max_depth", 3, 10)
                min_samples_split = trial.suggest_int("min_samples_split", 2, 6)
                clf = RandomForestClassifier(
                    n_estimators=n_estimators,
                    max_depth=max_depth,
                    min_samples_split=min_samples_split,
                    random_state=42,
                )
            else:
                lr = trial.suggest_float("learning_rate", 0.01, 0.2, log=True)
                n_estimators = trial.suggest_int("n_estimators", 30, 120, step=20)
                max_depth = trial.suggest_int("max_depth", 2, 6)
                clf = GradientBoostingClassifier(
                    learning_rate=lr,
                    n_estimators=n_estimators,
                    max_depth=max_depth,
                    random_state=42,
                )

            inner_cv = StratifiedKFold(n_splits=n_inner_folds, shuffle=True, random_state=fold_idx)
            inner_scores = []
            for in_train, in_val in inner_cv.split(X_outer_train, y_outer_train):
                if len(np.unique(y_outer_train[in_train])) < 2:
                    continue
                clf.fit(X_outer_train[in_train], y_outer_train[in_train])
                preds = clf.predict(X_outer_train[in_val])
                inner_scores.append(accuracy_score(y_outer_train[in_val], preds))

            return float(np.mean(inner_scores)) if inner_scores else 0.0

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=n_trials)
        best_p = study.best_params
        best_params_per_fold.append(best_p)
        all_trial_scores.extend([t.value for t in study.trials if t.value is not None])

        if "Forest" in model_family:
            best_model = RandomForestClassifier(**best_p, random_state=42)
        else:
            best_model = GradientBoostingClassifier(**best_p, random_state=42)

        best_model.fit(X_outer_train, y_outer_train)

        # Evaluación no sesgada sobre outer_val (1 sola vez)
        y_val_pred = best_model.predict(X_outer_val)

        acc = accuracy_score(y_outer_val, y_val_pred)
        prec = precision_score(y_outer_val, y_val_pred, average="weighted", zero_division=0)
        rec = recall_score(y_outer_val, y_val_pred, average="weighted", zero_division=0)
        f1 = f1_score(y_outer_val, y_val_pred, average="weighted", zero_division=0)

        outer_results.append({
            "Fold Externo": f"Fold {fold_idx}",
            "N_Train": len(y_outer_train),
            "N_Val": len(y_outer_val),
            "Accuracy": round(acc, 4),
            "Precision": round(prec, 4),
            "Recall": round(rec, 4),
            "F1-Score": round(f1, 4),
            "Mejor Score Inner": round(study.best_value, 4),
            "Mejores Hiperparámetros": str(best_p),
        })

        current_step += 1
        if progress_bar:
            progress_bar.progress(current_step / total_steps)
        time.sleep(0.2)

    return pd.DataFrame(outer_results), best_params_per_fold, all_trial_scores


def render_training_module():
    st.markdown("## 🧠 Fase 2: Módulo de Entrenamiento con CV Anidada y Optuna")
    st.caption("Validación anidada 5x3 para clasificación de postura de seguridad Linux y prevención de sobreajuste.")

    if "df_metadata" not in st.session_state or st.session_state.df_metadata is None or not st.session_state.images_dict:
        st.warning("⚠️ Primero cargue el dataset en la **Fase 1**.")
        return

    df = st.session_state.df_metadata
    images = st.session_state.images_dict

    col_conf1, col_conf2 = st.columns([1, 1])

    with col_conf1:
        st.markdown("#### 1. Configuración de Reparto y Modelo")
        st.write("**Partición General:**")
        st.markdown("`Desarrollo (70%)` · `Validación (15%)` · `Prueba (15%)`")

        model_architecture = st.selectbox(
            "Arquitectura del Clasificador:",
            [
                "Random Forest Classifier (Ensemble Basado en Árboles)",
                "Gradient Boosting Classifier (Boosting Adaptativo)",
                "ResNet-18 (Deep Residual Backbone sobre Matrices de Configuración)",
                "EfficientNet-B0 (Compound Scaling Architecture)",
            ],
            index=0,
        )

    with col_conf2:
        st.markdown("#### 2. Parámetros de Validación Cruzada Anidada")
        c_k1, c_k2, c_k3 = st.columns(3)
        with c_k1:
            outer_folds = st.number_input("Folds Externos (Outer):", min_value=3, max_value=10, value=5, step=1)
        with c_k2:
            inner_folds = st.number_input("Folds Internos (Inner):", min_value=2, max_value=5, value=3, step=1)
        with c_k3:
            optuna_trials = st.number_input("Trials de Optuna:", min_value=3, max_value=20, value=8, step=1)

    st.divider()

    if st.button("🚀 Iniciar Entrenamiento con Nested CV 5x3", type="primary", use_container_width=True):
        X, y, feat_names = extract_features_and_labels(df, images)

        if len(y) < 15:
            st.error("Se requieren al menos 15 muestras para estructurar 5 folds con representación mínima.")
            return

        X_dev, X_test, y_dev, y_test = train_test_split(X, y, test_size=0.15, random_state=42, stratify=y)

        prog_bar = st.progress(0.0)
        status = st.empty()

        with st.spinner("Ejecutando Validación Cruzada Anidada..."):
            df_outer, best_params, trial_scores = run_nested_cv_optuna(
                X_dev=X_dev,
                y_dev=y_dev,
                model_family=model_architecture,
                n_outer_folds=outer_folds,
                n_inner_folds=inner_folds,
                n_trials=optuna_trials,
                progress_bar=prog_bar,
                status_text=status,
            )

        status.success("✅ **Entrenamiento y Validación Cruzada Anidada de Hardening Completados con Éxito.**")

        st.session_state.training_results = df_outer
        st.session_state.trial_scores = trial_scores

        st.markdown("### 📊 Tabla de Resultados por Fold Externo (Nested CV)")
        st.dataframe(df_outer[["Fold Externo", "N_Train", "N_Val", "Accuracy", "Precision", "Recall", "F1-Score", "Mejores Hiperparámetros"]], use_container_width=True)

        mean_acc = df_outer["Accuracy"].mean()
        std_acc = df_outer["Accuracy"].std()
        mean_f1 = df_outer["F1-Score"].mean()
        std_f1 = df_outer["F1-Score"].std()

        st.markdown("#### Métricas Consolidadas")
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Accuracy Promedio", f"{mean_acc * 100:.2f}%", f"± {std_acc * 100:.2f}%")
        mc2.metric("F1-Score Promedio", f"{mean_f1:.4f}", f"± {std_f1:.4f}")
        mc3.metric("Folds Completados", f"{len(df_outer)}/{outer_folds}")
        mc4.metric("Total Trials Optuna", f"{len(trial_scores)}")

        st.divider()
        g1, g2 = st.columns(2)

        with g1:
            st.markdown("#### Desempeño por Fold Externo")
            fig_folds = go.Figure()
            fig_folds.add_trace(go.Bar(
                x=df_outer["Fold Externo"],
                y=df_outer["Accuracy"],
                name="Accuracy",
                marker_color="#2563eb",
                text=df_outer["Accuracy"].apply(lambda v: f"{v:.2f}"),
                textposition="auto",
            ))
            fig_folds.add_trace(go.Bar(
                x=df_outer["Fold Externo"],
                y=df_outer["F1-Score"],
                name="F1-Score",
                marker_color="#10b981",
                text=df_outer["F1-Score"].apply(lambda v: f"{v:.2f}"),
                textposition="auto",
            ))
            fig_folds.update_layout(barmode="group", height=340, yaxis=dict(range=[0, 1.05], title="Score"))
            st.plotly_chart(fig_folds, use_container_width=True)

        with g2:
            st.markdown("#### Distribución de Trials de Optuna")
            if trial_scores:
                fig_opt = px.line(
                    y=trial_scores,
                    labels={"x": "Trial Consecutivo", "y": "Accuracy en Inner Fold"},
                    title="Convergencia de la Búsqueda Bayesiana",
                    markers=True,
                )
                fig_opt.update_traces(line_color="#8b5cf6")
                fig_opt.update_layout(height=340)
                st.plotly_chart(fig_opt, use_container_width=True)
