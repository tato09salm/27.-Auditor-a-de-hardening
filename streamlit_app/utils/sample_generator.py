"""
Generador de Dataset Científico: CIS Hardening & Attack Surface Benchmark Dataset.
Crea matrices visuales de postura de seguridad (Security Posture Matrices / Config Byteplots 2D)
y metadata de auditoría de servidores Linux frente a controles CIS Benchmarks.
"""

from __future__ import annotations

import io
import os
import zipfile
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw


def generate_synthetic_dataset(output_dir: str, num_samples: int = 50) -> tuple[str, str]:
    """Genera un dataset estructurado de auditoría de hardening para servidores Linux."""
    os.makedirs(output_dir, exist_ok=True)
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    np.random.seed(42)
    classes = ["Hardened", "Vulnerable", "Exposed"]
    class_probs = [0.45, 0.35, 0.20]
    environments = ["Produccion", "Staging", "Desarrollo"]
    os_versions = ["Ubuntu 22.04 LTS", "Ubuntu 20.04 LTS", "Debian 12"]

    records = []

    for i in range(1, num_samples + 1):
        server_id = f"SRV_{i:04d}"
        file_name = f"{server_id}_posture_matrix.png"
        file_path = os.path.join(images_dir, file_name)

        posture_class = np.random.choice(classes, p=class_probs)
        cluster_id = f"CLUSTER_{(i % 8) + 1:02d}"
        env = np.random.choice(environments, p=[0.50, 0.30, 0.20])
        os_ver = np.random.choice(os_versions, p=[0.60, 0.25, 0.15])

        if posture_class == "Hardened":
            cis_score = round(float(np.random.uniform(84.0, 98.5)), 1)
            failed_controls = int(np.random.randint(0, 3))
            open_ports = int(np.random.choice([1, 2], p=[0.7, 0.3]))
        elif posture_class == "Vulnerable":
            cis_score = round(float(np.random.uniform(48.0, 75.0)), 1)
            failed_controls = int(np.random.randint(4, 8))
            open_ports = int(np.random.randint(3, 7))
        else:  # Exposed
            cis_score = round(float(np.random.uniform(15.0, 42.0)), 1)
            failed_controls = int(np.random.randint(9, 14))
            open_ports = int(np.random.randint(7, 15))

        # Generar matriz visual de postura de seguridad (224x224 px)
        # Representa 5 cuadrantes de hardening: Kernel, SSH, Firewall, Cuentas/PAM, Logging
        width, height = 224, 224
        img = Image.new("RGB", (width, height), color=(20, 24, 33))  # Fondo dark terminal
        draw = ImageDraw.Draw(img)

        # Generar textura de cuadrícula de controles (Grid de 8x8 bloques de configuración)
        cell_size = 28
        for row in range(8):
            for col in range(8):
                x0, y0 = col * cell_size, row * cell_size
                x1, y1 = x0 + cell_size - 2, y0 + cell_size - 2

                # Ponderación según la postura del servidor
                if posture_class == "Hardened":
                    # Mayoría de controles verdes/cian (conformes)
                    val = np.random.uniform(0.7, 1.0)
                    cell_color = (int(16 * val), int(185 * val), int(129 * val))
                elif posture_class == "Vulnerable":
                    # Mezcla de ámbar/naranja y verde (algunos fallos en SSH/Firewall)
                    if (row in [2, 3] and col in [2, 3, 4]):  # Bloque SSH fallando
                        cell_color = (245, 158, 11)
                    else:
                        cell_color = (int(59 * 0.8), int(130 * 0.8), int(246 * 0.8))
                else:  # Exposed
                    # Bloques rojos intensos (fallos críticos de root login, UFW disabled, ASLR disabled)
                    if (row in [1, 2, 3, 4] and col in [1, 2, 3, 4]):
                        cell_color = (239, 68, 68)
                    else:
                        cell_color = (int(160 * 0.5), int(40 * 0.5), int(40 * 0.5))

                draw.rectangle([x0, y0, x1, y1], fill=cell_color)

        img.save(file_path, format="PNG")

        records.append({
            "server_id": server_id,
            "filename": file_name,
            "cluster_group": cluster_id,
            "posture_class": posture_class,
            "cis_score": cis_score,
            "failed_controls": failed_controls,
            "open_ports": open_ports,
            "environment": env,
            "os_version": os_ver,
            "split_assigned": np.random.choice(["Train", "Val", "Test"], p=[0.70, 0.15, 0.15]),
        })

    metadata_path = os.path.join(output_dir, "metadata_hardening.csv")
    df = pd.DataFrame(records)
    df.to_csv(metadata_path, index=False)

    return images_dir, metadata_path
