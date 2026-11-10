# Leyendas y metadatos para el artículo

**Proyecto:** CIS Hardening Auditor  
**Fuente:** Dataset sintético reproducible  
**Organización:** Organización sintética de demostración  
**Generado:** 2026-11-03 14:49  

> **Advertencia de procedencia:** DATOS SIMULADOS: no usar como resultados empíricos.

## Tablas

### Tabla 1. Caracterización de la muestra de servidores auditados

**Título para el artículo:** Caracterización de la muestra de servidores auditados, con entorno, sistema operativo, perfil, cumplimiento y cobertura de la última ejecución.

**Explicación:** Permite juzgar la validez externa y el alcance real de la evaluación. Un promedio agregado de cumplimiento oculta que la muestra puede mezclar producción, pruebas y desarrollo, distintos sistemas operativos, áreas responsables y niveles de exposición. Esta tabla hace explícita esa composición antes de interpretar cualquier indicador.

**Descripción:** Una fila por servidor. Las columnas describen el entorno, el sistema operativo, el área responsable, el método de conexión y el perfil aplicado. «Cumplimiento» y «Cobertura» corresponden a la última ejecución completada de cada servidor; «Hallazgos activos» excluye los resueltos y los falsos positivos documentados.

**Nota:** Fuente: Dataset sintético reproducible. n=8 servidores. Periodo: 2026-07-15 a 2026-09-23. Score = aprobados / (aprobados + incumplidos) × 100; no aplicables y no evaluados se excluyen del denominador. DATOS SIMULADOS: no usar como resultados empíricos.

**Archivos:** tabla_01_caracterizacion_servidores.xlsx · tabla_01_caracterizacion_servidores.csv · tabla_01_caracterizacion_servidores.pdf

### Tabla 2. Catálogo de controles de hardening evaluados

**Título para el artículo:** Catálogo de controles evaluados, con referencia CIS, severidad, nivel, tipo de mapeo y propósito de cada requisito.

**Explicación:** Documenta el instrumento de medición y la transparencia del mapeo. La tabla distingue los controles con referencia CIS contrastada de los controles internos inspirados en buenas prácticas. Esta separación evita atribuir al estándar CIS resultados que la plataforma calcula con controles propios y permite reproducir el alcance del estudio.

**Descripción:** Una fila por control. «Referencia CIS» indica el identificador del benchmark cuando el mapeo fue verificado; «Mapeo» señala si el control es CIS oficial o interno. «Nivel» resume el perfil del benchmark (N1/N2) y «Propósito» resume el requisito evaluado.

**Nota:** Fuente: Dataset sintético reproducible; catálogo de 14 controles activos. La referencia CIS se contrastó con CIS Ubuntu Linux 22.04 LTS Benchmark v1.0.0. Los controles internos no constituyen un mapeo oficial de CIS.

**Archivos:** tabla_02_catalogo_controles.xlsx · tabla_02_catalogo_controles.csv · tabla_02_catalogo_controles.pdf

### Tabla 3. Resultados agregados por control

**Título para el artículo:** Resultados agregados por control: evaluados, aprobados, incumplidos, no aplicables, no evaluados, tasa de aprobación, cobertura y duración media.

**Explicación:** Identifica los controles que concentran el incumplimiento y permite priorizar la remediación con evidencia. También muestra la cobertura: un control con una tasa alta pero con muchos casos no evaluados no ofrece la misma confianza que uno evaluado en todos los servidores.

**Descripción:** Una fila por control, agregando todas las ejecuciones del periodo. «Evaluados» es la suma de aprobados e incumplidos; la tasa de aprobación usa ese denominador. «Cobertura» indica qué proporción del total de checks del control pudo evaluarse. La duración media resume el coste operativo de la comprobación.

**Nota:** Fuente: Dataset sintético reproducible; 336 checks y 24 ejecuciones. La tasa excluye «No aplica» y «No evaluado». Las duraciones provienen del motor de comprobaciones y no incluyen la latencia de red del entorno de publicación. DATOS SIMULADOS: no usar como resultados empíricos.

**Archivos:** tabla_03_resultados_por_control.xlsx · tabla_03_resultados_por_control.csv · tabla_03_resultados_por_control.pdf

### Tabla 4. Cumplimiento por categoría de control

**Título para el artículo:** Cumplimiento por categoría de control, con controles, evaluados, aprobados, incumplidos, tasa de aprobación y cobertura.

**Explicación:** Agrupa los controles por dominio para una lectura ejecutiva. Las categorías permiten detectar patrones que un ranking individual de controles no muestra: por ejemplo, una organización puede tener buen cumplimiento de firewall y un déficit sistémico en gestión de parches o autenticación.

**Descripción:** Una fila por categoría. Los conteos agregan todos los checks del periodo. La tasa de aprobación excluye los no aplicables y no evaluados; la cobertura muestra la proporción de checks con evidencia suficiente. Las categorías se ordenan de menor a mayor tasa.

**Nota:** Fuente: Dataset sintético reproducible; 336 checks. La categoría es la definida en el catálogo del benchmark y no implica una jerarquía de riesgo. DATOS SIMULADOS: no usar como resultados empíricos.

**Archivos:** tabla_04_cumplimiento_por_categoria.xlsx · tabla_04_cumplimiento_por_categoria.csv · tabla_04_cumplimiento_por_categoria.pdf

### Tabla 5. Hallazgos por severidad y estado del ciclo de vida

**Título para el artículo:** Distribución de hallazgos únicos por severidad y estado del ciclo de vida, incluyendo total histórico y hallazgos activos.

**Explicación:** Muestra el estado del backlog y la madurez del proceso de remediación. Un total alto de hallazgos no implica necesariamente un backlog alto: parte puede estar resuelto o documentado como falso positivo. La lectura conjunta de severidad y estado permite distinguir riesgo abierto de deuda histórica.

**Descripción:** Matriz de severidad por estado. Cada celda cuenta hallazgos únicos, no ocurrencias. «Activos» agrega los estados distintos de resuelto y falso positivo. La columna «Total histórico» conserva los cierres para trazabilidad.

**Nota:** Fuente: Dataset sintético reproducible; 76 hallazgos únicos. Un hallazgo resuelto exige una comprobación posterior satisfactoria o una justificación autorizada. «Riesgo aceptado» sigue siendo un hallazgo activo. DATOS SIMULADOS: no usar como resultados empíricos.

**Archivos:** tabla_05_hallazgos_severidad_estado.xlsx · tabla_05_hallazgos_severidad_estado.csv · tabla_05_hallazgos_severidad_estado.pdf

### Tabla 6. Trazabilidad y métricas de las ejecuciones

**Título para el artículo:** Trazabilidad de las ejecuciones: fecha, servidor, entorno, disparador, estado, conteos, cumplimiento, cobertura, duración y naturaleza simulada.

**Explicación:** Hace reproducible la evaluación: cada fila conserva el servidor, la fecha, el disparador, el estado y los conteos que produjeron el score. Sin esta trazabilidad no es posible distinguir una mejora real de un cambio en la cobertura, un fallo de conexión o una ejecución incompleta.

**Descripción:** Una fila por ejecución. «Cumplimiento» usa aprobados sobre aplicables evaluados; «Cobertura» indica la proporción del perfil que pudo evaluarse. La duración corresponde al intervalo de ejecución registrado. «Simulado» identifica el uso del conector de pruebas.

**Nota:** Fuente: Dataset sintético reproducible; 24 ejecuciones. Los fallos de conexión producen controles no evaluados y un score no calculable; no se imputan como aprobados. DATOS SIMULADOS: no usar como resultados empíricos.

**Archivos:** tabla_06_trazabilidad_ejecuciones.xlsx · tabla_06_trazabilidad_ejecuciones.csv · tabla_06_trazabilidad_ejecuciones.pdf

## Figuras

### Figura 1. Arquitectura de referencia y flujo de auditoría

**Título para el artículo:** Arquitectura de referencia y flujo de auditoría: límites de confianza, lectura SSH, scoring, IA opcional y revisión humana.

**Explicación:** Sitúa los límites de confianza del sistema: la consola no ejecuta comandos de corrección, el motor SSH solo lee configuración y la IA propone texto para revisión humana. Esta separación es una decisión de diseño central para reducir el riesgo operativo y explicar por qué la plataforma no modifica los servidores.

**Descripción:** Diagrama conceptual. La ruta principal va del usuario a la SPA, la API y PostgreSQL; el worker consulta el servidor por SSH de solo lectura. La IA es opcional y su salida pasa por revisión humana. n8n orquesta programaciones mediante API keys con alcance limitado.

**Nota:** Fuente y elaboración: figura conceptual propia. No representa una topología de despliegue específica ni incluye secretos. La IA no tiene herramientas de ejecución.

**Archivos:** figura_01_arquitectura_referencia.svg · figura_01_arquitectura_referencia.pdf · figura_01_arquitectura_referencia.png (600 dpi) · figura_01_arquitectura_referencia_preview.png · figura_01_arquitectura_referencia.csv

### Figura 2. Cumplimiento y cobertura por servidor

**Título para el artículo:** Cumplimiento y cobertura por servidor en la última ejecución completada; la cobertura acompaña al score y no se interpreta como certificación.

**Explicación:** Compara el resultado de la última auditoría con la proporción de controles que pudo evaluarse. Un score alto acompañado de baja cobertura no es comparable con un score similar obtenido sobre el perfil completo; la cobertura es parte del resultado, no un detalle técnico.

**Descripción:** Barras horizontales ordenadas por cumplimiento. La barra oscura representa el score y la barra clara la cobertura. La línea vertical punteada en 80 % es una referencia de lectura, no un umbral de certificación.

**Nota:** Fuente: Dataset sintético reproducible; última ejecución completada por servidor (n=8). Score = aprobados / (aprobados + incumplidos) × 100. DATOS SIMULADOS: no usar como resultados empíricos.

**Archivos:** figura_02_cumplimiento_cobertura_servidor.svg · figura_02_cumplimiento_cobertura_servidor.pdf · figura_02_cumplimiento_cobertura_servidor.png (600 dpi) · figura_02_cumplimiento_cobertura_servidor_preview.png · figura_02_cumplimiento_cobertura_servidor.csv

### Figura 3. Evolución del cumplimiento por servidor

**Título para el artículo:** Evolución del cumplimiento por servidor a lo largo de las ejecuciones completadas, con referencia visual en 80 %.

**Explicación:** Permite observar mejoras y regresiones a lo largo de las ejecuciones. La evolución es descriptiva: no demuestra causalidad ni atribuye el cambio a una corrección concreta, pero ayuda a formular hipótesis y a detectar servidores que requieren seguimiento.

**Descripción:** Pequeños múltiplos, uno por servidor. Cada punto es una ejecución completada; la línea punteada marca 80 % como referencia visual. La escala es común para facilitar la comparación entre servidores.

**Nota:** Fuente: Dataset sintético reproducible; 24 observaciones de 8 servidores. Los huecos indican ejecuciones no completadas o sin score calculable. DATOS SIMULADOS: no usar como resultados empíricos.

**Archivos:** figura_03_evolucion_cumplimiento.svg · figura_03_evolucion_cumplimiento.pdf · figura_03_evolucion_cumplimiento.png (600 dpi) · figura_03_evolucion_cumplimiento_preview.png · figura_03_evolucion_cumplimiento.csv

### Figura 4. Tasa de aprobación por control

**Título para el artículo:** Tasa de aprobación por control, ordenada de menor a mayor, con severidad, número de casos e identificación de controles internos.

**Explicación:** Ordena los controles por dificultad observada y facilita la priorización. Los controles con menor tasa son candidatos a revisión, pero la decisión debe considerar severidad, exposición del servidor y esfuerzo de remediación; la tasa por sí sola no define el riesgo.

**Descripción:** Gráfico de puntos y tallos. La posición indica la tasa de aprobación sobre controles evaluados y el color la severidad. El tamaño del punto representa el número de casos evaluados; los controles internos se marcan con «(I)».

**Nota:** Fuente: Dataset sintético reproducible; 336 checks. Denominador = aprobados + incumplidos; se excluyen no aplicables y no evaluados. El tamaño del punto es proporcional a los casos evaluados; «(I)» identifica controles internos sin referencia CIS oficial. DATOS SIMULADOS: no usar como resultados empíricos.

**Archivos:** figura_04_tasa_aprobacion_control.svg · figura_04_tasa_aprobacion_control.pdf · figura_04_tasa_aprobacion_control.png (600 dpi) · figura_04_tasa_aprobacion_control_preview.png · figura_04_tasa_aprobacion_control.csv

### Figura 5. Hallazgos por severidad y estado

**Título para el artículo:** Distribución de hallazgos únicos por severidad y estado del ciclo de vida, con total por severidad.

**Explicación:** Resume la composición del backlog y la madurez del ciclo de vida. La severidad indica potencial impacto; el estado indica en qué punto del proceso está la respuesta. Juntos permiten distinguir riesgo abierto, trabajo en curso y deuda histórica.

**Descripción:** Barras horizontales apiladas por severidad. Cada segmento representa un estado del ciclo de vida y el total se anota al final. «Resuelto» y «Falso positivo» son cierres; «Riesgo aceptado» permanece activo.

**Nota:** Fuente: Dataset sintético reproducible; 76 hallazgos únicos. Los conteos son hallazgos, no ocurrencias de auditoría. DATOS SIMULADOS: no usar como resultados empíricos.

**Archivos:** figura_05_hallazgos_severidad_estado.svg · figura_05_hallazgos_severidad_estado.pdf · figura_05_hallazgos_severidad_estado.png (600 dpi) · figura_05_hallazgos_severidad_estado_preview.png · figura_05_hallazgos_severidad_estado.csv

### Figura 6. Mapa de calor de cumplimiento por servidor y categoría

**Título para el artículo:** Mapa de calor de tasa de aprobación por servidor y categoría de control, agregando todas las ejecuciones del periodo.

**Explicación:** Revela patrones que no se ven en promedios globales: un servidor puede cumplir bien en firewall y fallar sistemáticamente en actualizaciones, o una categoría puede ser débil en toda la muestra. El mapa orienta auditorías de seguimiento y discusiones de priorización.

**Descripción:** Filas: servidores. Columnas: categorías de control. El color y el número indican la tasa de aprobación agregada de todas las ejecuciones; los valores más oscuros corresponden a mayor cumplimiento. Las celdas con pocos casos deben interpretarse con cautela.

**Nota:** Fuente: Dataset sintético reproducible; 336 checks agregados por servidor y categoría. Tasa = aprobados / (aprobados + incumplidos). DATOS SIMULADOS: no usar como resultados empíricos.

**Archivos:** figura_06_mapa_calor_servidor_categoria.svg · figura_06_mapa_calor_servidor_categoria.pdf · figura_06_mapa_calor_servidor_categoria.png (600 dpi) · figura_06_mapa_calor_servidor_categoria_preview.png · figura_06_mapa_calor_servidor_categoria.csv

## Reglas de uso

- Las tablas y figuras están numeradas y deben citarse en el texto del artículo.
- Las notas acompañan cada activo y deben mantenerse en la versión final.
- Las figuras 1 y 2 son conceptuales; no dependen de la muestra.
- Las tablas 1, 3, 4, 5 y 6 y las figuras 3–6 deben regenerarse con datos institucionales antes de una publicación empírica.
- No se deben presentar datos sintéticos como mediciones reales.
