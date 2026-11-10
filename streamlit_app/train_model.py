"""
Script de Entrenamiento Real de Modelos de Hardening (CIS Benchmarks).
Entrena, optimiza con Optuna y persiste el mejor clasificador en disco.
"""

from __future__ import annotations

import os
import joblib
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split
import optuna

from utils.sample_generator import generate_synthetic_dataset

optuna.logging.set_verbosity(optuna.logging.WARNING)


def extract_features(df: pd.DataFrame, images_dir: str):
    X = []
    y = []
    classes = ["Hardened", "Vulnerable", "Exposed"]
    label_map = {c: i for i, c in enumerate(classes)}

    for _, row in df.iterrows():
        fname = row["filename"]
        posture = row["posture_class"]
        img_path = os.path.join(images_dir, fname)

        if not os.path.exists(img_path):
            continue

        img = Image.open(img_path).convert("RGB")
        arr = np.array(img, dtype=np.float32)

        gray = np.array(img.convert("L"), dtype=np.float32)
        gy, gx = np.gradient(gray)
        sharpness = float(np.mean(gx**2 + gy**2))
        contrast = float(np.std(gray))

        # Variables fotométricas de seguridad y numéricas
        mean_r = float(np.mean(arr[:, :, 0]))
        mean_g = float(np.mean(arr[:, :, 1]))
        mean_b = float(np.mean(arr[:, :, 2]))

        cis_score = float(row["cis_score"])
        failed_ctrl = float(row["failed_controls"])
        open_ports = float(row["open_ports"])

        feat = [cis_score, failed_ctrl, open_ports, mean_r, mean_g, mean_b, contrast, sharpness]
        X.append(feat)
        y.append(label_map[posture])

    feature_names = [
        "CIS_Score",
        "Controles_Fallidos",
        "Puertos_Abiertos",
        "Canal_Exposicion_R",
        "Canal_Conformidad_G",
        "Canal_Servicios_B",
        "Contraste_Matriz",
        "Nitidez_Superficie",
    ]
    return np.array(X), np.array(y), feature_names, classes


def main():
    print("=" * 60)
    print("INICIANDO ENTRENAMIENTO REAL DE MODELOS DE HARDENING CIS")
    print("=" * 60)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "sample_data_hardening")
    models_dir = os.path.join(base_dir, "models")
    os.makedirs(models_dir, exist_ok=True)

    img_dir = os.path.join(data_dir, "images")
    meta_path = os.path.join(data_dir, "metadata_hardening.csv")

    if not os.path.exists(meta_path):
        print("Generando dataset de servidores CIS...")
        img_dir, meta_path = generate_synthetic_dataset(data_dir, num_samples=100)

    df = pd.read_csv(meta_path)
    print(f"Dataset cargado con {len(df)} servidores.")

    X, y, feature_names, classes = extract_features(df, img_dir)
    print(f"Matriz de características extraída: {X.shape[0]} muestras x {X.shape[1]} variables.")

    # Split: 70% Dev, 15% Val, 15% Test
    X_dev, X_test, y_dev, y_test = train_test_split(X, y, test_size=0.15, random_state=42, stratify=y)
    X_train, X_val, y_train, y_val = train_test_split(X_dev, y_dev, test_size=0.1765, random_state=42, stratify=y_dev)

    print(f"Particiones: Train={len(y_train)}, Val={len(y_val)}, Test={len(y_test)}")

    # 1. Optimización con Optuna para Random Forest
    print("\n--- Optimizando Random Forest con Optuna ---")
    def objective_rf(trial):
        n_est = trial.suggest_int("n_estimators", 30, 200, step=10)
        max_d = trial.suggest_int("max_depth", 3, 12)
        min_split = trial.suggest_int("min_samples_split", 2, 8)
        clf = RandomForestClassifier(n_estimators=n_est, max_depth=max_d, min_samples_split=min_split, random_state=42)
        clf.fit(X_train, y_train)
        preds = clf.predict(X_val)
        return float(f1_score(y_val, preds, average="macro"))

    study_rf = optuna.create_study(direction="maximize")
    study_rf.optimize(objective_rf, n_trials=15)
    print(f"Mejor F1 en Val (RF): {study_rf.best_value:.4f} con {study_rf.best_params}")

    # 2. Optimización con Optuna para Gradient Boosting
    print("\n--- Optimizando Gradient Boosting con Optuna ---")
    def objective_gb(trial):
        n_est = trial.suggest_int("n_estimators", 30, 150, step=10)
        max_d = trial.suggest_int("max_depth", 2, 6)
        lr = trial.suggest_float("learning_rate", 0.02, 0.25, log=True)
        clf = GradientBoostingClassifier(n_estimators=n_est, max_depth=max_d, learning_rate=lr, random_state=42)
        clf.fit(X_train, y_train)
        preds = clf.predict(X_val)
        return float(f1_score(y_val, preds, average="macro"))

    study_gb = optuna.create_study(direction="maximize")
    study_gb.optimize(objective_gb, n_trials=15)
    print(f"Mejor F1 en Val (GB): {study_gb.best_value:.4f} con {study_gb.best_params}")

    # Reentrenar el mejor modelo en todo X_dev (Train + Val) y evaluar en TEST ciego
    if study_rf.best_value >= study_gb.best_value:
        best_model_name = "RandomForestClassifier"
        best_clf = RandomForestClassifier(**study_rf.best_params, random_state=42)
    else:
        best_model_name = "GradientBoostingClassifier"
        best_clf = GradientBoostingClassifier(**study_gb.best_params, random_state=42)

    best_clf.fit(X_dev, y_dev)
    y_test_pred = best_clf.predict(X_test)
    y_test_prob = best_clf.predict_proba(X_test)

    test_acc = accuracy_score(y_test, y_test_pred)
    test_f1 = f1_score(y_test, y_test_pred, average="macro")

    print("\n" + "=" * 60)
    print(f"EVALUACIÓN FINAL EN TEST CIEGO ({best_model_name}):")
    print(f"Accuracy en Test: {test_acc * 100:.2f}%")
    print(f"Macro F1-Score en Test: {test_f1:.4f}")
    print("\nReporte de Clasificación:")
    print(classification_report(y_test, y_test_pred, target_names=classes))

    # Guardar modelo entrenado y artefactos
    model_payload = {
        "model": best_clf,
        "model_name": best_model_name,
        "classes": classes,
        "feature_names": feature_names,
        "best_params": study_rf.best_params if "Random" in best_model_name else study_gb.best_params,
        "test_accuracy": test_acc,
        "test_f1": test_f1,
    }

    save_path = os.path.join(models_dir, "best_hardening_model.joblib")
    joblib.dump(model_payload, save_path)
    print(f"✅ Modelo entrenado y serializado exitosamente en:\n   {save_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()

