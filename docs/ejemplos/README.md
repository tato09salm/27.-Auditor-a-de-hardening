# Ejemplos de reportes

> **Todos los archivos de esta carpeta son EJEMPLOS CON DATOS SIMULADOS.** Fueron generados con el
> conector simulado de la plataforma y una organización de demostración. No describen infraestructura
> real, no son una certificación CIS y no deben usarse para tomar decisiones de producción.

## Archivos

| Archivo | Tipo | Contenido |
| --- | --- | --- |
| `EJEMPLO_SIMULADO_reporte_tecnico_portal.pdf` | Técnico PDF | 14 controles, 9 incumplimientos, evidencia y limitaciones |
| `EJEMPLO_SIMULADO_reporte_tecnico_portal.docx` | Técnico Word | Mismo alcance, editable |
| `EJEMPLO_SIMULADO_reporte_tecnico_portal.xlsx` | Técnico Excel | Hojas Resumen, Controles, Hallazgos y Recomendaciones |
| `EJEMPLO_SIMULADO_reporte_ejecutivo.pdf` | Ejecutivo PDF | Consolidado del periodo, tendencia y riesgos |
| `EJEMPLO_SIMULADO_reporte_ejecutivo.docx` | Ejecutivo Word | Mismo alcance, editable |
| `EJEMPLO_SIMULADO_reporte_ejecutivo.xlsx` | Ejecutivo Excel | Resumen, tendencia, fallos, riesgos y acciones |

## Marcas de simulación

Los archivos incluyen:

- prefijo `simulado_` en el nombre interno generado por la API;
- campo **Naturaleza: datos simulados de pruebas**;
- párrafo de advertencia en la portada;
- nombre de archivo `EJEMPLO_SIMULADO_...` en esta carpeta.

La API no permite habilitar el conector simulado en `ENVIRONMENT=production`.

## Cómo se generaron

1. Organización temporal, servidores simulados y auditorías.
2. Ejecución del motor con salidas de prueba.
3. `POST /api/v1/reports` para cada formato.
4. Descarga desde `GET /api/v1/reports/{id}/download`.
5. Eliminación de los datos de demostración de la base de desarrollo.

Los archivos no contienen contraseñas, claves privadas ni tokens. Las evidencias mostradas son
metadatos y salidas simuladas de configuración.

## Cómo generar sus propios reportes

Use la consola en **Reportes**, con una auditoría real completada. Los reportes de producción no
llevan el prefijo `simulado_` y muestran **Naturaleza: evaluación real**.
