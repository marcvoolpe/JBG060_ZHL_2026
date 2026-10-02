# Revisión independiente: fiabilidad de datos públicos de inundación y desplazamiento para acción anticipatoria a escala de condado en Sudán del Sur

## Veredicto y puntuaciones

### Veredicto resumido

**Recomendación: reencuadrar.** El núcleo defendible del proyecto es una auditoría de *fitness-for-purpose* de los datos públicos de inundación y desplazamiento, no una afirmación amplia sobre cuánto puede “confiarse” en el ConvLSTM. IOM documenta que Event Tracking sólo busca movimientos de más de 50 hogares y no garantiza cobertura completa; OCHA advierte que sus cifras de afectados reflejan población evaluada y verificada, no toda la población afectada. Por tanto, los ceros de ET no son ceros observacionales fiables y el 61,7% OCHA→ET no estima una probabilidad de registro identificada. citeturn22search8turn24search1

La parte de inundación tiene valor, pero la procedencia/versionado del producto NASA debe aclararse y la validación necesita Sentinel-1. La parte de pronóstico tiene problemas más graves: lead time ambiguo, etiqueta “recurring” con información futura, particiones temporales débiles y ganancias mínimas frente a persistencia a un dekad. Mantenerla como segundo objetivo haría el trabajo menos coherente y menos factible.

### Puntuaciones

| Criterio | Puntuación | Razón en una línea |
|---|---:|---|
| Novedad | **3/5** | Las limitaciones generales ya están documentadas, pero cuantificar su magnitud y consecuencias en estos datos concretos de Sudán del Sur parece poco estudiado. |
| Validez de referencias y métricas | **2/5** | OCHA y MT no son gold standards equivalentes ni necesariamente independientes; split-half y lluvia local no validan exactitud de inundación. |
| Solidez analítica | **2/5** | CR2/TWFE es razonable, pero el resultado de potencia depende de un modelo de observación no identificado y el pronóstico tiene problemas de diseño previos a cualquier métrica. |
| Robustez frente a sesgo y circularidad | **2/5** | La visibilidad humanitaria compartida, la selección de zonas evaluadas y posibles fuentes comunes permanecen sin acotar. |
| Coherencia del objetivo | **2/5** | La auditoría de medición y la evaluación de un ConvLSTM son, en la práctica, dos problemas empíricos con criterios de validez distintos. |
| Relevancia para decisiones | **3/5** | La auditoría puede cambiar qué datos se usan para screening o contexto, pero no valida directamente una acción comunitaria sobre pérdida de cosecha. |
| Factibilidad en el tiempo restante | **2/5** | Impact data está avanzado, pero añadir validación SAR rigurosa, forecast backtesting, leakage audit y decision table en cuatro semanas es excesivo. |

## Hallazgos sobre novedad y trabajo previo

### Datos de desplazamiento e impacto

**Hecho de fuente externa.** IOM define Event Tracking en Sudán del Sur como una herramienta rápida que verifica nuevos desplazamientos o retornos de **más de 50 hogares** tras recibir alertas. Los enumeradores visitan o evalúan remotamente los lugares, consultan informantes clave y triangulan con fuentes secundarias. El propio documento dice que IOM no puede garantizar cobertura completa en todo el país (IOM DTM, 2021, *Event Tracking Summary January–June 2021*, pp. 1–2). citeturn22search8 El Event Tracking anual de 2021 y 2023 se publica expresamente como complemento de los ejercicios nacionales de Mobility Tracking, no como un censo exhaustivo de eventos. citeturn22search0turn22search1

Esto confirma una parte central de la afirmación del equipo. También cambia la interpretación estadística de los ceros: **“no hay fila ET” no equivale, según la documentación del productor, a “no hubo desplazamiento”**. Es una mezcla de cero real, evento por debajo del umbral, evento no alertado, evento no accesible y posiblemente evento no registrado. citeturn22search8

**Hecho de fuente externa.** Mobility Tracking mide principalmente la **presencia** de IDPs y retornados en lugares y comunidades de acogida mediante evaluaciones de informantes clave a nivel de localización. Por ejemplo, la ronda 14 cubrió 3.916 localizaciones de 78 condados en marzo-abril de 2023. citeturn22search5 Por ello, comparar ET con la primera ronda de MT posterior a una temporada es una triangulación útil, pero no una prueba directa de sensibilidad: uno mide eventos/movimientos y el otro un stock posterior, con posibles salidas, retornos, movimientos secundarios y diferencias de causa y geografía.

Hay además una evidencia oficial particularmente pertinente. En el resumen ET de enero-junio de 2021, IOM informó que el 57% de los IDPs se desplazaron dentro del mismo condado y payam, otro 25% dentro del mismo condado pero a otro payam, y un 14% procedía de otros condados. citeturn22search8 Por tanto, el movimiento transfronterizo entre condados no domina ese periodo, pero tampoco es despreciable. Esto respalda la preocupación del prompt acerca de emparejar impacto en el condado con registros de origen o destino.

**Hecho de fuente externa.** La base pública de OCHA para inundaciones de Sudán del Sur identifica como fuente a “humanitarian partners” y describe la metodología como observación directa/datos anecdóticos. Su advertencia dice que las cifras reflejan personas que han sido evaluadas y verificadas como afectadas hasta la fecha y que pueden no representar a todas las personas afectadas; también distingue explícitamente “affected” de “displaced”. citeturn24search1turn24search4 En 2022, OCHA decía que sus cifras se basaban en evaluaciones completadas en una fracción de los condados que habían reportado inundaciones, mientras continuaban nuevas evaluaciones. citeturn21search7turn21search3

Esto significa que **ET y OCHA son dos observaciones incompletas de constructos diferentes**, no instrumento y referencia verdadera.

La independencia tampoco puede darse por supuesta. OCHA produce los informes junto con la coordinación inter-clúster, combina evaluaciones de autoridades y socios, y en los informes de 2024 atribuye expresamente cifras de desplazados a IOM; otros números proceden de evaluaciones conjuntas o de la Relief and Rehabilitation Commission. citeturn20search12turn21search1 No he encontrado documentación pública que permita reconstruir, condado por condado y año por año, qué entradas de la tabla OCHA utilizada por el equipo derivan directa o indirectamente de DTM. **Independencia de OCHA respecto de ET: no verificada.**

IDMC tampoco sería automáticamente un gold standard independiente. Su metodología global de desplazamiento agrega y reconcilia información de gobiernos, Naciones Unidas, actores humanitarios, organizaciones no gubernamentales y otras fuentes, por lo que puede reutilizar observaciones de IOM/OCHA. citeturn6search1

### ¿Es novedoso estudiar estas limitaciones?

La idea general, “los datos históricos de impacto humanitario tienen huecos que dificultan diseñar y validar acción anticipatoria”, **no es nueva**. El OCHA Centre for Humanitarian Data identifica tres insumos históricos para AA, datos de amenaza, impacto y forecast, y señala que las listas históricas de eventos suelen ser incompletas, que los datos de impacto presentan huecos y problemas subnacionales, y que los archivos históricos de forecasts con frecuencia ni siquiera existen. citeturn23view2 La metodología de 510 para desarrollar triggers también incluye análisis histórico de amenaza-impacto, evaluación de skill y adecuación del lead time. citeturn4search5

En Sudán del Sur existe incluso un precedente operacional directo. Tras las inundaciones de 2022, OCHA describió que las características del Sudd impedían disponer de un forecast suficientemente fiable para un framework formal con trigger temporal, aunque existía evidencia suficiente para actuar anticipadamente de otra forma. citeturn23view9 Esto ya responde parcialmente a la pregunta general de si un forecast de inundación puede convertirse sin más en un trigger fiable.

También existe trabajo directo de validación geoespacial. IOM realizó para el estudio de daños y necesidades por inundación de 2021 una validación de campo en tres payams para contrastar hallazgos derivados de teledetección/geodatos. citeturn6search3 Revilla-Romero y colaboradores compararon productos Sentinel-1 y VIIRS para Sudán del Sur y destacaron la falta de observaciones in situ suficientes para una validación convencional. citeturn1search2

**Inferencia.** Por ello doy un 3/5 en novedad. La contribución potencial no es descubrir que ET, OCHA o las imágenes ópticas tienen limitaciones. Sí puede ser relativamente nueva la **cuantificación localizada** de cuánto importan esas limitaciones para comparaciones *within-county*, en qué fases de la temporada aparecen y qué afirmaciones concretas deberían quedar descartadas. Esa distinción debería ser explícita en el objetivo.

### Persistencia y evaluación del cambio

El trabajo más cercano que encontré para el Sudd es INFLOW-AI v2.1, de Rapson, Stephens, Maidment y Bonifacio. El preprint de 2026 predice extensión de inundación en el Sudd hasta seis dekads y utiliza un componente espacial ConvLSTM a 1 km; su evaluación temporal intenta mantener el periodo posterior a 2019 fuera del entrenamiento. citeturn23view0

La revisión pública de ese artículo es particularmente relevante: un referee señaló que la inundación del Sudd tiene una persistencia temporal muy alta y que esa persistencia explica por qué un baseline de persistencia funciona casi tan bien como modelos más complejos. Los autores aceptaron el punto y defendieron explícitamente el baseline de persistencia como prueba de skill incremental; también aceptaron que rolling-origin validation y validación temporal estricta fortalecerían el trabajo. citeturn23view0

**Inferencia.** No encontré una norma autoritativa que declare formalmente a la persistencia “el baseline mínimo obligatorio” para toda predicción de inundación. Sí encontré evidencia muy directa de que, **en este mismo sistema hidrológico**, compararse con persistencia es indispensable para que una mejora de corto plazo tenga interpretación.

Los estudios operacionales de mapas de inundación suelen evaluar el **estado** inundado/no inundado mediante métricas de tabla de contingencia, como Critical Success Index, precisión de usuario/productor o equivalentes, en adquisiciones temporalmente emparejadas. La validación de Global Flood Monitoring contra productos Copernicus Rapid Mapping sigue este tipo de planteamiento. citeturn3search1 No encontré un precedente cercano que convierta F1 de “onset/expansion/recession” en una métrica estándar dominante. **Inferencia:** change-F1 es una adición razonable para un sistema muy persistente, pero debe acompañar, no sustituir, evaluación del estado, sesgo de área y error temporal.

## Validez del diseño y de las referencias

### El 61,7% OCHA→ET no es una probabilidad de registro

**Afirmación del equipo.** Entre 115 condado-temporadas con ≥10.000 afectados OCHA, el 61,7% tiene alguna fila ET de inundación. El porcentaje implica 71/115 y el intervalo de Wilson proporcionado, 52,6–70,1%, es aritméticamente consistente.

**Inferencia.** La cantidad que realmente se estima es aproximadamente:

\[
P(\text{algún ET} \mid \text{OCHA observado}\ge 10.000),
\]

no

\[
P(\text{ET registra el evento}\mid \text{hubo desplazamiento real por inundación}).
\]

Hay tres problemas cuyos signos no coinciden:

| Problema | Efecto probable sobre interpretar 0,617 como \(\pi\) |
|---|---|
| OCHA “afectado” ≠ desplazado | **Hacia abajo**: puede haber inundaciones muy grandes sin desplazamiento suficiente para generar ET. |
| OCHA también es incompleto y depende de evaluaciones | **Probablemente hacia arriba respecto a todos los eventos reales**, porque se condiciona en lugares que ya han sido vistos/evaluados por el sistema humanitario. |
| Visibilidad y fuentes compartidas OCHA-IOM | **Hacia arriba en concordancia**, si ambos sistemas encuentran más fácilmente los mismos lugares accesibles o reciben las mismas alertas. |
| Desplazamiento a otro condado y diferencias origen/destino | Puede **reducir el match**, dependiendo de cómo se hizo el emparejamiento. |

La dirección neta, por tanto, **no está identificada**. OCHA confirma además que sus números son personas evaluadas/verificadas y pueden omitir afectados. citeturn24search1 El 0,617 es útil como índice empírico de solapamiento entre dos sistemas, pero usarlo como \(\pi=0,617\) en una simulación del proceso de registro requiere un supuesto adicional que los datos no justifican.

El test contra Mobility Tracking tiene el mismo problema de constructo. MT proporciona una presencia posterior de IDPs/retornados en lugares de destino mediante key informants; no es un registro independiente de todos los episodios de desplazamiento por inundación en el condado de origen. citeturn22search5 Que el porcentaje de coincidencia también sea bajo refuerza la conclusión cualitativa de inconsistencia, pero no identifica una sensibilidad.

La métrica de test-retest de MT de 0,00–0,49 tampoco puede interpretarse automáticamente como error de medición. **Afirmación del equipo:** se comparó “el mismo cohort” en rondas posteriores. **Inferencia:** si entre rondas hubo salidas, retornos, mortalidad, reclasificación o cambios de localización, parte de la discrepancia puede ser cambio real. Habría que demostrar que el estimando mantiene fija la población que debería seguir presente.

### Split-half y ERA5 no validan la máscara de inundación

**Afirmación del equipo.** El split-half odd/even dekad da 0,91 después de Spearman-Brown.

Esto demuestra **consistencia temporal interna**, no exactitud. Las dos mitades observan el mismo evento hidrológico, con fuerte autocorrelación, el mismo sensor/algoritmo y regímenes atmosféricos relacionados. El supuesto que vuelve interpretable un split-half como reliability, errores suficientemente independientes entre formas paralelas condicionados al valor verdadero, es poco plausible aquí.

**Inferencia importante:** llamarlo un “techo” de fiabilidad es demasiado fuerte. Un instrumento puede reproducir de forma extremadamente consistente un sesgo sistemático y obtener reliability interna cercana a 1 mientras tiene mala validez externa.

El mismo problema aparece con el split-half de ET de 0,87. El propio equipo reconoce que un episodio puede descomponerse en varias filas. Si esas filas hermanas caen en ambos halves, los dos pseudo-instrumentos comparten el mismo episodio y el coeficiente queda inflado.

El acuerdo con precipitación ERA5 tampoco constituye una validación directa. La dinámica del Sudd depende fuertemente del sistema del White Nile y de condiciones hidrológicas acumuladas, y el trabajo INFLOW-AI usa historia de inundación y predictores hidrometeorológicos más amplios precisamente porque el estado del humedal presenta larga memoria. citeturn23view0 OCHA documentó ya en 2022 que la complejidad del Sudd hacía difícil generar un forecast de trigger fiable. citeturn23view9 Una correlación baja entre inundación y **lluvia dentro del mismo condado y semestre** puede reflejar transporte fluvial, desfase temporal o almacenamiento, además de error de la máscara.

**Inferencia.** Por tanto, \(r=+0,15\) en 2021–2025 y \(r=-0,11\) en 2001–2025 son descriptivos de la relación entre dos señales, no evidence of validity. En Northern Bahr el Ghazal puede haber más conexión con precipitación regional, pero incluso allí una comparación hidrológica apropiada necesitaría cuenca y desfases, no sólo lluvia contemporánea del polígono admin2.

### El producto NASA necesita una auditoría de procedencia antes de evaluarlo

Aquí encontré una discrepancia material entre el prompt y la documentación pública.

**Afirmación del equipo:** los course files son un “NASA MODIS/VIIRS global flood product”, ~232 m, diario, 2000–2025, con clases “recurring” y “unusual”.

**Documentación pública de NASA:** el producto MODIS NRT MCDWD es aproximadamente 250 m y su ficha de producto actual tiene cobertura operacional desde marzo de 2021; NASA distingue ese producto de su archivo MODIS histórico. citeturn1search0turn1search7 La clase “recurring flood” se añadió al producto en diciembre de 2025 y se define mediante un archivo mensual de 22 años, 2003–2024, marcando como recurrentes lugares inundados en al menos siete de esos años. NASA publicó posteriormente un archivo MODIS reprocesado de 2003–2025, con cambios de procesamiento y geolocalización, en 2026. citeturn1search5turn1search9 VIIRS es un flujo/producto separado, basado en observaciones a 375 m remuestreadas al grid del producto. citeturn1search1

Por tanto, **no pude verificar la existencia de un único producto oficial NASA MODIS/VIIRS “diario 2000–2025” exactamente como se describe en el prompt**. Puede ser un derivado preparado para el curso, una combinación de versiones o un archivo legacy. Esa procedencia debe resolverse antes de asignarle propiedades de un producto NASA concreto.

Esto también importa para el salto de volumen después de 2019. Existe evidencia independiente de un cambio hidrológico real: INFLOW-AI describe inundaciones excepcionalmente extensas en el Sudd a partir de 2019. citeturn23view0 También existe evidencia de cambios en las versiones del producto NASA durante el periodo. citeturn1search5turn1search9 **La explicación “es el régimen del Sudd” y la explicación “es parcialmente el producto” son simultáneamente plausibles con la evidencia disponible. El equipo todavía no puede atribuir el salto a una de ellas.**

### Nubes, estacionalidad y la referencia SAR

El algoritmo MODIS es óptico. La literatura de validación de NASA documenta problemas por cobertura nubosa, sombras de nubes, sombras de terreno y confusión espectral; Lin et al. (2019), *Improvement and Validation of NASA/MODIS NRT Global Flood Mapping*, describe precisamente estos problemas en la validación del producto. citeturn2search6 NASA recomienda interpretar productos de uno o pocos días junto con la imagen fuente porque nubes y sombras pueden contaminar la clasificación. citeturn1search6

Eso hace preocupante el **claim del equipo** de que `cloud_frac` es siempre 0. No pude verificar ese campo en la documentación pública del fichero del curso, por lo que no sé si representa “sin nubes”, un placeholder o una variable perdida durante el preprocesado.

Sin embargo, la estacionalidad descrita en el prompt tampoco prueba por sí sola “ceguera” en julio-septiembre. El equipo compara:

* pixel-días de agua detectada, una variable de **duración/extensión**;
* fecha de comienzo del movimiento ET, una variable de **onset humano**.

**Inferencia:** un desplazamiento puede comenzar en agosto y el mismo episodio de inundación alcanzar su mayor extensión o persistir hasta noviembre-enero. El desajuste temporal es una fuerte señal de alerta, pero no permite separar nubosidad, persistencia hidrológica y verdadero retraso de la extensión inundada. Sentinel-1 es exactamente la prueba necesaria para hacerlo.

Copernicus Global Flood Monitoring utiliza Sentinel-1 SAR, que puede observar de día/noche y atravesar cobertura nubosa; el servicio procesa automáticamente adquisiciones Sentinel-1 globales y combina tres algoritmos independientes. citeturn3search6turn23view4 El diseño técnico de GFM contempla capas separadas para agua observada, agua de referencia, exclusiones, incertidumbre y metadatos de la adquisición; el estudio de viabilidad especificaba Sentinel-1 como fuente principal y una resolución de entrada del orden de 20 m. Matgen et al. (2020), pp. 2, 13. citeturn9view0turn9view1 Wagner et al. (2025) describe posteriormente el servicio operacional global y su arquitectura de ensemble. citeturn3search8

Por tanto, **GFM/Sentinel-1 es la mejor referencia pública que encontré para 2021–2025**, con dos advertencias: no es ground truth y sólo observa cuando existe una adquisición Sentinel-1 válida. Debe compararse fecha con fecha y preservando áreas excluidas/no observadas.

UNOSAT también publicó productos de agua para Sudán del Sur. En octubre de 2021 usó NOAA-20/VIIRS a 375 m e informó explícitamente tanto las zonas cubiertas por nubes como que el análisis era preliminar y no había sido validado en campo. citeturn24search2turn24search11 En febrero de 2025 publicó otro producto VIIRS con zonas cloud-free y la misma advertencia de no validación de campo. citeturn24search7 Esto es útil como contraste de algoritmo, pero **no es una referencia independiente fuerte para un producto basado en VIIRS**, porque comparte sensor y limitación óptica.

No pude verificar una **serie pública WFP de máscaras de inundación SAR 2021–2025** disponible de manera consistente a escala de condado. WFP DataViz sí expone información climática y de emergencias para Sudán del Sur, pero la existencia del archivo específico requerido por este diseño quedó **no verificada**. citeturn24search0

### ¿Cuántas observaciones Sentinel-1 hacen falta?

No hay una respuesta única porque depende del estimando.

Si se quisiera estimar, por ejemplo, una tasa de detección de agua con un error de aproximadamente ±10 puntos porcentuales al 95%, y las unidades positivas fueran independientes, la aproximación binomial

\[
n \approx \frac{1.96^2p(1-p)}{0.1^2}
\]

requiere aproximadamente **62 unidades positivas** si \(p=0,8\) y **96** en el caso conservador \(p=0,5\).

Los píxeles vecinos de una misma escena no son unidades independientes, así que contar miles de píxeles no resuelve el problema. La incertidumbre tendría que agruparse o bootstrapearse por escena, condado-fecha o bloques espaciales.

**Inferencia para este capstone:** 10–20 condado-temporadas seleccionadas intencionadamente pueden servir como *stress test* y detectar problemas grandes, pero no deberían describirse como una “validación nacional”. Para sostener una estimación nacional relativamente precisa de sensibilidad/agreement, esperaría del orden de **60–100 unidades independientes de evaluación**, estratificadas por fase de temporada, región, nivel de inundación y sistema hidrológico, con varias adquisiciones temporalmente emparejadas. Con cuatro semanas, esto favorece explícitamente un **diagnóstico estratificado**, no una validación exhaustiva.

## Solidez analítica y evaluación del pronóstico

### Qué impulsa la simulación de potencia

La conclusión “detection alone caps outcome reliability at ~0,24” **no es una consecuencia matemática general de \(\pi=0,617\)**. Es una propiedad de la simulación concreta.

Por ejemplo, en un modelo de thinning simple \(O|T\sim Binomial(T,\pi)\),

\[
\operatorname{Corr}^2(T,O)=
\frac{\pi\,Var(T)}
{\pi Var(T)+(1-\pi)E(T)},
\]

por lo que la correlación entre observado y verdadero depende también de la distribución de \(T\); no existe un límite universal de 0,24 impuesto sólo por \(\pi\).

En la simulación del equipo, el resultado se genera conjuntamente por al menos cuatro componentes:

**\(\pi=0,617\).** Este es probablemente el supuesto más influyente y, como se ha mostrado, el 0,617 no identifica la probabilidad de registro de un verdadero desplazamiento. OCHA e IOM miden constructos y poblaciones de observación distintos. citeturn24search1turn22search8

**Umbral de 300 personas.** IOM publica un criterio de **más de 50 hogares**, no 300 personas. citeturn22search8 Convertir 50 hogares en 300 personas presupone seis personas por hogar. No encontré una justificación pública para aplicar esa conversión fija: **no verificado**.

**\(\kappa=0,5\).** Controla cuánto comparten el proceso de ocurrencia y la magnitud del desplazamiento. No está estimado de los datos según el prompt. Cuanto más estrechamente conectados estén tamaño y propensión latente, más pueden concentrarse las pérdidas por censura en determinados niveles de severidad.

**Heterogeneidad de detección rank-matched con la frecuencia observada de ET.** Es especialmente delicada porque utiliza un patrón observado que es resultado conjunto de verdaderos eventos y observación para definir el proceso de observación. Puede convertir diferencias reales entre condados en supuestas diferencias de detection, o viceversa.

La simulación sí tiene un punto fuerte: utiliza el skeleton real de \(71\times4\), conserva la escasez de variación *within* y comprueba el tamaño bajo shocks correlacionados. El resultado del prompt, false-positive rate 0,057, es compatible con un procedimiento inferencial razonablemente calibrado **dentro del DGP simulado**, pero no valida el DGP.

Las sensitivities mínimas que considero necesarias antes de afirmar una MDE son:

| Supuesto | Valores que deberían mostrarse |
|---|---|
| Probabilidad de registro \(\pi\) | 0,4; 0,6; 0,8; 1,0 |
| Umbral | 0; criterio explícito de 50 hogares; 300 personas; umbral mayor |
| \(\kappa\) | 0; 0,5; 1 |
| Heterogeneidad de detección | ninguna; aleatoria; rank-matched; correlacionada positiva/negativamente con severidad o acceso |
| Reliability de \(X\) | al menos 0,4–0,9 |
| Ceros ET | todos verdaderos; mezcla missing/zero; límites extremos |
| Misclasificación del trigger | cero y escenarios con error no diferencial/diferencial |
| Dependencia temporal | distintos niveles de autocorrelación/shocks comunes |

**Mi lectura de la conclusión de potencia:** con los resultados actuales se puede decir que *bajo el modelo de observación elegido*, un efecto moderado de \(r=0,35\) tiene poca probabilidad de detectarse. No está demostrado todavía que **cualquier modelo de observación razonable** produzca una MDE cercana a 0,47. La documentación de IOM hace muy plausible que haya under-recording; no determina su magnitud o mecanismo. citeturn22search8

### TWFE, CR2 y la palabra “reliability”

Pustejovsky y Tipton (2018), *Small-Sample Methods for Cluster-Robust Variance Estimation and Hypothesis Testing in Fixed Effects Models*, muestran que las correcciones CR2 junto con aproximaciones tipo Satterthwaite/Bell–McCaffrey pueden mejorar la inferencia con cluster-robust SE en modelos de fixed effects cuando el número efectivo de clusters es limitado. DOI: 10.1080/07350015.2016.1247004. citeturn14search0

**Inferencia:** con 71 clusters nominales, TWFE + CR2 es una elección defendible. El problema principal no está en CR2. Está en que sólo hay cuatro temporadas útiles y, según el prompt, sólo 47 condados cambian de outcome. El contenido empírico del efecto *within* es por tanto mucho menor que “284 observaciones” podría sugerir.

Usar \(r\) entre dos medidas residualizadas como “reliability” también es conceptualmente problemático. Correlación no equivale a acuerdo: dos instrumentos pueden correlacionar perfectamente y diferir sistemáticamente en magnitud. Haghayegh et al. (2020), en una revisión metodológica de agreement, subrayan precisamente la distinción entre asociación y acuerdo. citeturn15search0 Aquí el problema se agrava porque OCHA y ET ni siquiera observan el mismo constructo.

Recomiendo interpretar las cantidades por función de decisión, no buscar un único coeficiente:

1. **Ocurrencia:** sensibilidad/positive agreement de “algún desplazamiento”, sin convertir automáticamente ausencia de registro en ausencia del evento.
2. **Magnitud condicional:** error o acuerdo de los conteos entre episodios comparables.
3. **Ranking:** correlación/rank agreement si la decisión es priorizar condados.
4. **Cambio *within-county*:** asociación de incrementos/decrementos sólo para el uso longitudinal que motivó la auditoría.

Eso convertiría “reliability” en un término operativo y reduciría la posibilidad de que un número alto, como split-half 0,87, sea leído erróneamente como “el dataset es fiable”.

### El ConvLSTM no está listo para una afirmación de confianza

La evaluación propuesta contiene elementos correctos, especialmente persistencia, climatología, cambio, estratificación temporal y una referencia SAR. Pero todavía no puede sostener la frase **“how far the forecast can be trusted”**.

#### El lead time debe resolverse antes de cualquier score

**Afirmación del equipo:** el informe interno alterna entre “6 dekads ahead” y “next dekad”.

Es una diferencia fundamental. Una predicción \(t+1\) dekad puede encajar aproximadamente en la ventana de implementación de 3–14 días indicada por ZOA. Un objetivo \(t+6\) dekads tiene una función de decisión distinta. También es posible que “six dekads ahead” signifique producir una secuencia de seis horizons, lo que sería una tercera interpretación.

Hasta aclararlo, F1 no tiene significado operacional único. El baseline de persistencia debe evaluarse **exactamente al mismo horizonte y con exactamente la misma información disponible al forecast origin**.

#### Las ganancias a un dekad son demasiado pequeñas para interpretarse sin incertidumbre

**Afirmación del equipo:** unusual-F1 mejora de 0,842 a 0,846 en 2023, 0,767 a 0,772 en 2025 y 0,506 a 0,519 en 2019.

Son diferencias absolutas de **0,004, 0,005 y 0,013**. Sin paired confidence intervals o bootstrap espacial/temporal, no se puede saber si son robustas a la muestra, y tampoco se ha demostrado relevancia operacional. En el trabajo independiente INFLOW-AI sobre el mismo Sudd, los propios autores y revisores dan gran importancia a la persistencia precisamente porque el sistema evoluciona lentamente. citeturn23view0

Si el horizonte verdadero fuera seis dekads, los scores de persistencia 0,716 y 0,636 proporcionados por el equipo son más fáciles de superar, pero faltan en el prompt los F1 del **modelo a seis dekads** para hacer la comparación equivalente.

#### La etiqueta recurring introduce look-ahead

NASA define la clase recurrente de la versión reciente a partir de 2003–2024 y un umbral de presencia en al menos siete años. citeturn1search5 Por tanto, al entrenar/evaluar una clasificación histórica de 2019, 2021 o 2023 como “recurring/unusual”, el significado de la clase usa años que todavía no existían en el forecast origin.

Eso es **target-definition leakage**. No significa que el pixel de agua observado en 2021 utilice una imagen futura. Significa que la división entre “recurrente” e “inusual” sí incorpora el futuro.

Para un backtest válido hay dos opciones:

* reconstruir el mapa recurring únicamente con años disponibles antes de cada forecast origin; o
* evaluar primero **water/no-water** contra una referencia contemporánea y tratar recurring/unusual como atributo retrospectivo, no como target operacional.

Sin una de esas correcciones, un F1 por clase no representa íntegramente la tarea que habría podido ejecutarse en tiempo real.

#### La división temporal debe ser estricta

Rapson et al. reciben precisamente esta crítica en INFLOW-AI: un referee cuestionó una validación interna aleatoria en una serie autocorrelacionada y una sola frontera temporal; los autores aceptaron que rolling-origin y una validación separada temporalmente son más apropiados. citeturn23view0

**Afirmación del equipo:** los test years del ConvLSTM están intercalados con training years. Si esto es correcto, es insuficiente para una claim de forward forecast generalisation. Un modelo puede aprender el régimen temporal posterior al año evaluado.

Para una evaluación útil a ZOA harían falta como mínimo:

* rolling-origin o train-before/test-after;
* ninguna superposición temporal entre patches de training y test;
* baseline de persistencia y climatología en cada lead;
* precision, recall y false-alarm rate, además de F1;
* area bias y CSI sobre agua;
* onset/expansion/recession con definiciones congeladas;
* intervalos de confianza mediante resampling por bloques/condado-temporada;
* skill específico en los lugares de interés de ZOA, no sólo agregado en Unity/Jonglei;
* evaluación contra Sentinel-1 en fechas coincidentes;
* si el modelo produce probabilidades, reliability/calibration además de clasificación.

Un 99,8% de overall accuracy puede coexistir con poca capacidad para detectar la clase minoritaria cuando domina “dry”; por eso el F1 de unusual ya es claramente más informativo. Esta es una inferencia a partir de la estructura de tres clases descrita en el prompt, no una afirmación independiente sobre el modelo.

## Coherencia, relevancia de decisión y ética

### ¿Uno o dos objetivos?

La parte de **impact data** pregunta si una serie humanitaria observa adecuadamente desplazamientos y si diferentes sistemas concuerdan.

La parte de **forecast** pregunta si un modelo predictivo generaliza en el tiempo, añade skill a baselines, está bien calibrado y produce avisos a determinado horizonte.

Ambas caben bajo el concepto muy amplio de “trust”, pero requieren referencias, estimandos y diseños de validación diferentes. Bajo la restricción del curso, “cada supporting objective debe contribuir directamente y no introducir otro enfoque u outcome”, **mi valoración es que la propuesta actual contiene dos estudios**.

La parte de flood-mask validation sí encaja con el primero, porque es una auditoría de medición de los inputs/targets públicos. El ConvLSTM introduce generalización predictiva, benchmarking y lead-time validation, que constituyen otro problema.

**El objetivo sería más fuerte sin la evaluación completa del forecast.** El forecast puede aparecer como consecuencia: “estas son las limitaciones que cualquier modelo entrenado con estas etiquetas heredará”, con uno o dos checks descriptivos claramente secundarios. No debería prometerse determinar cuánto puede confiarse en todo el modelo.

### El historial no invalida el nuevo objetivo, pero sí cambia cómo debe presentarse

La historia proporcionada por el equipo reduce una preocupación importante: la auditoría de measurement validity estaba especificada de antemano como fallback y la correlación severidad-desplazamiento original nunca se calculó. Eso hace que el cambio sea menos parecido a buscar retrospectivamente una asociación significativa después de obtener un null.

La extensión al forecast sí ocurrió **después** del NO-GO y, según el prompt, después de que el equipo ya conocía al menos varios F1 y problemas del modelo.

**Inferencia:** esto no invalida el nuevo estudio, pero impide presentarlo limpiamente como una evaluación totalmente ex ante. La forma intelectualmente honesta es distinguir:

> “El cambio a measurement validity estaba preespecificado. Las preguntas y métricas adicionales del forecast fueron desarrolladas posteriormente y deben considerarse un análisis posterior/exploratorio salvo que se congelen antes de nuevos resultados.”

Se convierte en un **objetivo sustantivo** si el estimando pasa a ser la aptitud de fuentes concretas para usos concretos, con referencias externas y criterios de falsificación. Sería una mera reformulación del resultado negativo si la tesis central fuera únicamente “no podemos estimar la relación original, por tanto nuestros datos son malos” y las mismas limitaciones ya observadas se usaran como resultado sin validación adicional.

### Qué podría cambiar realmente una decisión de ZOA o ZHL

Tomando las necesidades de stakeholders como **claims del prompt**, veo tres niveles muy distintos.

| Uso | Valor probable de esta auditoría | Juicio |
|---|---|---|
| **Ranking estratégico de condados/regiones** | Saber qué fuentes cubren sistemáticamente unas zonas mejor que otras y si la severidad conserva rankings puede evitar interpretar cobertura como riesgo. | **Útil**, pero entre-condado no valida cambio anual ni comunidad. |
| **Entender dinámica de inundación** | Comparar optical vs SAR por fase de temporada, distinguir agua recurrente/nueva y documentar lags puede responder directamente a la prioridad de ZHL. | **La parte más relevante**. |
| **Seasonal outlook** | Un sistema con varias semanas de horizonte puede apoyar preparación y recursos, siempre que su lead y skill estén establecidos. | Potencialmente útil, pero distinta decisión del trigger 3–14 días. |
| **Trigger in-season 3–14 días** | Requiere habilidad en onset/expansion en la ventana precisa y baja tasa de misses/false alarms. Las cifras actuales del ConvLSTM no lo demuestran. | **No validado**. |
| **Asignación comunitaria de ayuda** | ET y mapas admin2 no identifican exposición, vulnerabilidad y coping capacity de una comunidad concreta. | **Insuficiente como base directa**. |
| **Contexto de vulnerabilidad/desplazamiento** | ET puede indicar que un evento conocido ocurrió, pero sus ceros no son evidencia fuerte de ausencia. | Útil como evidencia positiva, débil para ausencia. |

Esto coincide con la experiencia de OCHA de 2022: en Sudán del Sur se pudo actuar anticipadamente con información incompleta sin pretender que existía un trigger forecast formal fiable. citeturn23view9 Es una distinción especialmente adecuada para la afirmación de ZOA de que ninguna decisión se tomará exclusivamente mediante un modelo.

### Desplazamiento y extensión no son pérdida de cosecha

Este es un déficit real de relevancia. El proyecto estudia amenaza física y una consecuencia humana, pero el **impacto prioritario declarado en el prompt es harvest failure**.

La literatura operacional confirma que la inundación puede afectar directamente producción, pero también que el outcome agrícola es multicausal. La evaluación FAO/WFP de la cosecha de 2024 en Sudán del Sur combinó una misión nacional de evaluación con información sobre superficie sembrada, condiciones climáticas, seguridad y daños por inundación; informó que en 2024 los daños de inundación a cultivos fueron relativamente limitados respecto de otras temporadas y que la producción dependió también de seguridad y superficie plantada. FAO/WFP (2025), *Special Report: 2024 Crop and Food Security Assessment Mission to the Republic of South Sudan*, DOI 10.4060/cd5136en. citeturn18search1

Añadir ahora un nuevo strand de crop-loss modelling sería, en mi opinión, un error de alcance. Existen productos públicos de cropland, como WorldCereal 2021 a 10 m, con documentación de validación propia, y existe incluso un dataset de ground-truth/crop-type para pequeñas explotaciones de Sudán del Sur de 2016–2017. citeturn18search0turn18search3turn18search6 Pero introducirlos exige inmediatamente otra pregunta de validez: qué cultivos representan, en qué año, con qué recall local y si una parcela inundada equivale a pérdida de cosecha.

**Recomendación:** no añadir crop modelling. Sí debe reducirse la claim de decisión a “calidad de dos inputs públicos relevantes para entender hazard y desplazamiento”, dejando claro que **no valida un trigger de harvest failure**.

### ¿Es admin2 demasiado grueso?

Para la decisión comunitaria descrita en el prompt, **sí**: un score de condado no localiza una comunidad, un campo, una carretera ni un asentamiento concreto.

Sin embargo, una auditoría admin2 puede seguir siendo útil si se interpreta como un test de suficiencia mínima. Si una fuente no puede reproducir de forma estable cambios entre años ni siquiera agregada a condado, no existe fundamento empírico para asumir que esa misma fuente es adecuada para una decisión más localizada. Ésta es una inferencia de diseño, no prueba de que su rendimiento a comunidad sea necesariamente peor.

El resultado defendible sería:

> “A escala de condado, y para estos usos concretos, podemos/cannot establish sufficient information quality.”

No:

> “Por tanto sabemos qué comunidades deben recibir acción anticipatoria.”

### Representación, exclusión y accountability

La preocupación ética tiene respaldo, pero conviene limitar la claim.

El IASC define data responsibility como gestión segura, ética y efectiva de datos en acción humanitaria y asigna obligaciones sobre calidad, propósito, riesgo y responsabilidad a los actores del sistema. La guía fue adoptada inicialmente en 2021 y revisada en 2023. citeturn16search3turn16search0

En un estudio basado en 60 entrevistas sobre third-party monitoring humanitario en Somalia, Diepeveen, Bryant y Wasuge (2025) hallaron que datos parciales podían adquirir una apariencia de objetividad y completitud ante donantes, mientras que las prácticas de producción de esos datos ocultaban contexto y reproducían asimetrías respecto de actores locales; los autores vinculan explícitamente esto con accountability tanto hacia donantes como hacia comunidades afectadas. DOI 10.1177/20539517251328250. citeturn16search1turn16search11

Clausen, Fejerskov y Seddig (2025) argumentan de forma relacionada que la “datafied localization” puede representar realidades locales a distancia y reducir comunidades a fuentes de datos descontextualizados, reproduciendo jerarquías que la localización pretende corregir. DOI 10.1177/20539517241304693. citeturn17search11 Una revisión de ODI sobre inclusión y exclusión en acción humanitaria también identifica la falta de datos adecuados y la invisibilidad de determinados grupos como mecanismos que pueden contribuir a exclusión. citeturn17search4

La implicación estadística aquí es concreta: si **“sin registro ET” se codifica como “cero desplazamiento”**, un proceso de no observación diferencial puede entrar tanto en una regresión como en una validación de triggers como si fuera resultado humano verdadero.

Lo que la literatura revisada **no demuestra** es que los huecos concretos de ET de Sudán del Sur perjudiquen sistemáticamente a una etnia, género, condado o grupo de subsistencia específico. Esa claim sería especulativa con la evidencia disponible y no debería hacerse.

## Evidencia, cambios recomendados y claims no verificados

### Tabla de evidencia

| Claim relevante para el veredicto | Fuente principal | Aplicación |
|---|---|---|
| ET sólo busca movimientos >50 hogares y no garantiza cobertura nacional completa | IOM DTM, 2021, *Event Tracking Summary January–June 2021*, pp. 1–2. citeturn22search8 | **Directa** |
| ET es una herramienta rápida/localizada complementaria a Mobility Tracking | IOM DTM, datasets ET 2021 y 2023. citeturn22search0turn22search1 | **Directa** |
| MT mide stocks/presencia mediante KI a nivel de localización | IOM DTM, 2023, *Mobility Tracking Round 14*. citeturn22search5 | **Directa** |
| OCHA flood affected es población evaluada/verificada y puede omitir afectados | OCHA South Sudan, *South Sudan: Flood Data* metadata. citeturn24search1turn24search4 | **Directa** |
| OCHA combina fuentes y en 2024 usa explícitamente cifras de IOM para desplazamiento | OCHA, *Flooding Situation Flash Update No. 5*, 2024. citeturn20search12 | **Directa** |
| Historical impact data incompleto es un problema conocido en AA | OCHA Centre for Humanitarian Data, 2022, *Data Requirements for Anticipatory Action*. citeturn23view2 | **Directa al problema metodológico** |
| En 2022 no había forecast suficientemente fiable para un trigger formal en el Sudd | OCHA Centre for Humanitarian Data, 2024, *Lessons from the 2022 South Sudan Floods on Acting Ahead*. citeturn23view9 | **Directa** |
| MODIS flood mapping tiene limitaciones por nubes/sombras | Lin et al., 2019, *Improvement and Validation of NASA/MODIS NRT Global Flood Mapping*. citeturn2search6 | **Directa al producto, análoga geográficamente** |
| La clase recurring actual utiliza 2003–2024 y ≥7 años | NASA Earthdata, 2025/2026 product documentation. citeturn1search5 | **Directa** |
| Sentinel-1 GFM proporciona flood mapping global con SAR y ensemble de tres algoritmos | Copernicus/JRC; Wagner et al., 2025. citeturn3search6turn3search8 | **Directa** |
| Existe precedente de comparación Sentinel-1/VIIRS en Sudán del Sur, con falta de ground truth | Revilla-Romero et al., 2024. citeturn1search2 | **Directa** |
| Persistencia es un baseline crítico en el Sudd y rolling-origin mejora la validación | Rapson et al., 2026 + peer review/response. citeturn23view0 | **Directa** |
| CR2 aborda small-sample bias de cluster-robust inference en fixed-effects | Pustejovsky & Tipton, 2018. citeturn14search0 | **Análoga estadística** |
| Correlación y agreement no son conceptos equivalentes | Haghayegh et al., 2020. citeturn15search0 | **Análoga estadística** |
| Datos parciales pueden distorsionar accountability humanitaria | Diepeveen, Bryant & Wasuge, 2025. citeturn16search1 | **Análoga, Somalia** |
| Pérdida agrícola en Sudán del Sur requiere información más amplia que flood extent | FAO/WFP, 2025 CFSAM. citeturn18search1 | **Directa al país** |

### Cambios recomendados, por prioridad

| Prioridad | Cambio | Problema que resuelve |
|---|---|---|
| **Crítica** | **Reformular el objetivo principal como una auditoría de fitness-for-purpose de los datos públicos de inundación y desplazamiento y retirar la afirmación “how far the ConvLSTM can be trusted” del objetivo central.** El forecast puede quedar como aplicación exploratoria o apéndice si sobra tiempo. | Coherencia del curso, alcance de cuatro semanas, evita prometer una validación predictiva que el diseño actual no puede proporcionar. |
| **Muy alta** | Establecer y documentar la procedencia exacta del flood raster: producto, versión, fechas de reprocessing, significado de clases, QA/cloud fields y por qué se denomina MODIS/VIIRS 2000–2025. | Sin ello no se sabe exactamente qué instrumento se está auditando y el cambio post-2019 puede mezclar hidrología y versión. |
| **Muy alta** | Sustituir “OCHA detection rate = recording probability” por “observed cross-system coverage”, presentar 61,7% como tal y no usarlo como \(\pi\) único sin sensitivity analysis. | Elimina una interpretación causal/measurement-error no identificada. |
| **Alta** | Añadir sensitivities de \(\pi\), umbral, \(\kappa\), heterogeneidad de detection, Rx y zero-vs-missing; mostrar MDE como rango. | Determina si el NO-GO original es robusto o depende del DGP elegido. |
| **Alta** | Hacer un check SAR estratificado y temporalmente emparejado con Copernicus GFM/Sentinel-1; describirlo como *validation sample* sólo si tiene suficiente tamaño, y como *stress test* si es pequeño. | Es el único check propuesto que evalúa agua con un sensor físicamente distinto de MODIS óptico bajo nubes. |
| **Alta si el forecast permanece** | Resolver el lead time antes de ejecutar más métricas, reconstruir/eliminar la etiqueta recurring con look-ahead y usar rolling-origin temporal. | Sin estas tres correcciones, el score no representa una predicción operacional real. |
| **Media** | Sustituir la palabra global “reliability” por métricas separadas de occurrence, magnitude, ranking y temporal change. | Evita que correlaciones o split-halves inflados se interpreten como exactitud. |
| **Media** | No añadir crop-loss modelling. Declarar explícitamente que el estudio no valida el outcome prioritario de harvest failure. | Evita un tercer strand y una nueva cadena de measurement validity imposible de resolver en cuatro semanas. |
| **Media** | Congelar ahora el protocolo restante y marcar claramente qué análisis fueron definidos antes y después de ver los resultados. | Reduce selección retrospectiva de métricas y hace transparente el cambio de objetivo. |

### Qué evidencia cambiaría mi recomendación

Cambiaría de **“reframe”** a **“proceed with specific changes” incluyendo el forecast** si, antes de comprometer una parte grande de las cuatro semanas, el equipo pudiera aportar conjuntamente:

1. una definición inequívoca del forecast origin y de cada horizon;
2. provenance completa de las etiquetas;
3. targets sin información futura;
4. un backtest estrictamente forward/rolling-origin;
5. comparación paired contra persistencia al mismo lead con intervalos de incertidumbre;
6. skill material en onset/expansion, no sólo mantenimiento de agua existente;
7. concordancia razonable con Sentinel-1 en una muestra estratificada que incluya al menos los contextos hidrológicos relevantes para Bor South y Northern Bahr el Ghazal.

En ausencia de eso, el añadido del forecast reduce la calidad científica del objetivo principal.

### Claims del prompt que no pude verificar o que disputo

| Claim del prompt | Evaluación |
|---|---|
| “NASA MODIS/VIIRS global flood product, ~232 m, daily, 2000–2025” | **Disputado / provenance no verificada.** La documentación NASA encontrada separa MODIS y VIIRS y describe otras coberturas/versiones. citeturn1search0turn1search5turn1search7 |
| “recurring = flooded ≥7 of 22 years 2003–2024” | **Verificado para la clase recurring reciente de NASA.** citeturn1search5 |
| `cloud_frac = 0` en todos los ficheros | **No verificado.** Es una propiedad de los course files, no de la documentación pública que encontré. |
| 71 de 79 condados tienen ≥95% dentro de h20v08/h21v08 | **No verificado.** Además, OCHA usa “78 counties” en publicaciones recientes, por lo que la versión de límites administrativos debe explicarse. citeturn20search0 |
| 7% de detecciones unusual anuales en Jul–Sep; mediana 4% | **No verificado externamente.** Resultado de cálculo del equipo. |
| 86% del desplazamiento ET empieza Jul–Oct | **No verificado externamente.** Requiere reproducir los ficheros ET. |
| Split-half flood severity = 0,91 | **No verificado como cálculo; disputo su interpretación como ceiling de validez.** |
| ERA5 correlations +0,15 / −0,11 | **No verificadas.** Además no constituyen una prueba de exactitud de inundación. |
| Tile × season explica 2,3% | **No verificado.** |
| El salto posterior a 2019 es un “regime shift in the Sudd” | **Parcialmente plausible pero atribución no demostrada.** Hay evidencia externa de inundación extrema desde 2019 y también de cambios del producto NASA. citeturn23view0turn1search5 |
| Todos los conteos ET 2021–2025 de la tabla | **No verificados fila por fila.** La existencia de los datasets 2021/2023 y reportes 2025 sí está verificada. citeturn22search0turn22search1turn22search10 |
| “ET records moves over 50 households” y no garantiza cobertura completa | **Verificado.** citeturn22search8turn22search6 |
| 579 filas “Forced return” en 2023 | **No verificado.** |
| Sólo cuatro de 71 condados tienen flood displacement ET en Jun–Dec 2023 | **No verificado.** |
| Razón del colapso ET en 2023 | **No verificado**, coherentemente con el propio prompt. |
| 2025 termina en noviembre y no hay diciembre en ningún fichero | **Parcialmente verificado:** existe un reporte de noviembre de 2025; no pude demostrar exhaustivamente que no exista ningún producto/dataset posterior de diciembre. citeturn22search2turn22search10 |
| 47/71 condados tienen outcome variable; 24 siempre cero | **No verificado.** |
| OCHA ≥10.000: 61,7%, n=115, CI 52,6–70,1 | **Aritméticamente consistente; datos subyacentes no reproducidos.** |
| Ese 61,7% es una “detection probability” | **Disputado.** Es cross-system coverage, no sensibilidad identificada. |
| MT detection 52,2%; 2023 15% | **No verificado como cálculo y no debe interpretarse como sensibilidad directa.** |
| ET–OCHA within-county \(r=0,11\) | **No verificado.** Constructos distintos limitan la interpretación aunque el cálculo sea correcto. |
| ET split-half 0,87 | **No verificado; probablemente optimista como reliability por filas agrupadas en episodios.** |
| MT test-retest 0,00–0,49 | **No verificado; puede mezclar measurement error y movilidad real.** |
| Tabla de Aweil Centre | **No verificada fila por fila.** OCHA sí documenta Aweil Centre entre condados afectados/evaluados en 2022. citeturn21search7 |
| “Detection alone caps reliability near 0,24” | **Disputado como afirmación general.** Sólo vale dentro del DGP de la simulación. |
| Threshold de 300 personas | **No verificado como regla IOM.** La regla publicada es >50 hogares. citeturn22search8 |
| MDE \(r\approx0,47\) a Rx=0,8 | **No verificado sin código/skeleton.** Debe convertirse en intervalo de sensitivity. |
| Between-county Spearman 0,68 y placebo 0,087 | **No verificados.** |
| Arquitectura, corridor y scores del ConvLSTM | **No verificados externamente**, tal como pide el prompt. |
| “6 dekads ahead” vs “next dekad” | **No verificado externamente, pero si el brief contiene ambas frases es una contradicción crítica que debe resolverse.** |
| Test years entre training years | **No verificado externamente.** Si es correcto, la partición no basta para forward generalisation. |
| Overall accuracy 99,8% | **No verificado y, por sí solo, insuficiente para una clase minoritaria.** |

## Referencias completas

1. **International Organization for Migration, Displacement Tracking Matrix (IOM DTM). 2021.** *Event Tracking Summary January–June 2021*, pp. 1–2. Metodología de Event Tracking, umbral de 50 hogares, key informants, triangulación y advertencia de cobertura. [IOM DTM](https://dtm.iom.int/dtm_download_track/15616?amp%3Bid=11978&amp%3Btype=node&file=1). citeturn22search8

2. **IOM DTM. 2021.** *South Sudan – Event Tracking (January–December 2021).* [IOM DTM dataset](https://dtm.iom.int/datasets/south-sudan-event-tracking-january-december-2021). citeturn22search0

3. **IOM DTM. 2023.** *South Sudan – Event Tracking (January–December 2023).* [IOM DTM dataset](https://dtm.iom.int/datasets/south-sudan-event-tracking-january-december-2023). citeturn22search1

4. **IOM DTM. 2023.** *Mobility Tracking Round 14, South Sudan.* Evaluaciones mediante informantes clave a nivel de localización. [IOM DTM](https://dtm.iom.int/sites/g/files/tmzbdl1461/files/reports/DTM%20SSD%20MT%20Round%2014%20report_firts%20release.pdf). citeturn22search5

5. **IOM DTM. 2025.** *South Sudan Event Tracking Report #92 – Flood Displacements, 1–30 November 2025.* [IOM DTM](https://dtm.iom.int/reports/south-sudan-event-tracking-report-92-flood-displacements-1-30-november-2025). citeturn22search10

6. **IOM DTM. Study period 2021.** *South Sudan – Flood Damage and Needs Assessment Study (2021).* Estudio con validación de campo de resultados geoespaciales en tres payams. citeturn6search3

7. **OCHA South Sudan. 2021–2025.** *South Sudan: Flood Data.* Humanitarian Data Exchange. Metadata: “Humanitarian partners”; metodología observacional/anecdótica y caveat sobre cobertura de personas afectadas. [HDX](https://data.humdata.org/dataset/south-sudan-flood-data). citeturn24search1turn24search4

8. **OCHA South Sudan. 2021.** *South Sudan Flooding Situation Report: Inter-Cluster Coordination Group, as of 12 November 2021.* [OCHA](https://www.unocha.org/publications/report/south-sudan/south-sudan-flooding-situation-report-inter-cluster-coordination-group-12). citeturn19search0

9. **OCHA South Sudan. 2022.** *South Sudan: Flooding Situation Report No. 1, as of 31 October 2022.* [OCHA](https://www.unocha.org/publications/report/south-sudan/south-sudan-flooding-situation-report-no-1-31-october-2022). citeturn21search3

10. **OCHA South Sudan. 2024.** *South Sudan: Flooding Situation Flash Update No. 5, as of 25 September 2024.* Incluye cifras atribuidas expresamente a IOM y evaluaciones conjuntas/RRC. [OCHA](https://www.unocha.org/publications/report/south-sudan/south-sudan-flooding-situation-flash-update-no-5-25-september-2024). citeturn20search12

11. **OCHA Centre for Humanitarian Data. 2022.** *Data Requirements for Anticipatory Action.* Revisión de requisitos de hazard, impact y forecast data y de sus principales huecos. [Centre for Humanitarian Data](https://centre.humdata.org/data-requirements-for-anticipatory-action/). citeturn23view2

12. **OCHA Centre for Humanitarian Data. 2024.** *Lessons from the 2022 South Sudan Floods on Acting Ahead.* Caso de acción anticipatoria sin trigger forecast formal suficientemente fiable. [Centre for Humanitarian Data](https://centre.humdata.org/lessons-from-the-2022-south-sudan-floods-on-acting-ahead/). citeturn23view9

13. **510, Netherlands Red Cross. 2023.** *Trigger Model Development.* Metodología para hazard-impact databases, forecast skill, lead times y trigger development. citeturn4search5

14. **NASA Earthdata. 2026.** *Near Real-Time Global Flood Products.* Documentación de MCDWD y VCDWD, resolución y fuentes MODIS/VIIRS. citeturn1search0

15. **NASA Earthdata. 2025/2026.** *NASA Enhances Global Flood Products with Recurring Flood Classification and Reprocessed Archive.* Definición de recurring flood mediante 2003–2024 y cambios del archivo. citeturn1search5

16. **NASA LP DAAC.** *MCDWD_L3_NRT Version 6.1.* DOI **10.5067/MODIS/MCDWD_L3_NRT.061**. Ficha del producto MODIS global flood. citeturn1search7

17. **Lin, L., Di, L., Yu, E. G., Tang, J., Shrestha, R., Rahman, M. S., et al. 2019.** “Improvement and Validation of NASA/MODIS NRT Global Flood Mapping.” *Remote Sensing*, 11(2), 205. DOI **10.3390/rs11020205**. citeturn2search6

18. **Matgen, P., et al. 2020.** *Feasibility Assessment of an Automated, Global, Satellite-Based Flood-Monitoring Product for the Copernicus Emergency Management Service.* European Commission Joint Research Centre. DOI **10.2760/653891**. Véanse especialmente pp. 2 y 13 para Sentinel-1 y output layers. citeturn9view0turn9view1

19. **Copernicus Emergency Management Service.** *Global Flood Monitoring.* Documentación del servicio Sentinel-1, procesamiento global y ensemble de algoritmos. citeturn3search6

20. **Wagner, W., et al. 2025.** “The fully-automatic Sentinel-1 Global Flood Monitoring service: Scientific challenges and future directions.” *Remote Sensing of Environment*, 333, 115108. DOI **10.1016/j.rse.2025.115108**. citeturn3search8turn23view4

21. **Revilla-Romero, B., et al. 2024.** Estudio EGU sobre mapeo de inundación de Sudán del Sur mediante Sentinel-1 y VIIRS y comparación de productos 2017–2022. citeturn1search2

22. **United Nations Satellite Centre, UNOSAT. 2021.** *South Sudan Imagery Analysis, 15–19 October 2021.* Producto NOAA-20/VIIRS a 375 m, con áreas cloud-obstructed y caveat de no validación de campo. [UNOSAT product](https://unosat.org/static/unosat_filesystem/3162/UNOSAT_A3_Natural_Landscape_FL20211015SSD_15Oct_19Oct2021_SouthSudan.pdf). citeturn24search2

23. **UNOSAT. 2025.** *Satellite detected water extents between 01 and 05 February 2025 over South Sudan.* Producto VIIRS distribuido en HDX. [HDX](https://data.humdata.org/dataset/satellite-detected-water-extents-between-01-and-05-february-2025-over-south-sudan). citeturn24search7

24. **Rapson, J., Stephens, E., Maidment, R. I., & Bonifacio, R. 2026.** “INFLOW-AI v2.1: A Machine Learning Framework for Predicting Out-of-Sample Extreme Seasonal Flood Extents.” *EGUsphere* preprint. DOI **10.5194/egusphere-2026-66**. Incluye discusión pública de reviewers y respuestas de autores sobre persistencia, temporal splits, rolling-origin y baselines. [EGUsphere](https://egusphere.copernicus.org/preprints/2026/egusphere-2026-66/). citeturn23view0

25. **Pustejovsky, J. E., & Tipton, E. 2018.** “Small-Sample Methods for Cluster-Robust Variance Estimation and Hypothesis Testing in Fixed Effects Models.” *Journal of Business & Economic Statistics*, 36(4), 672–683. DOI **10.1080/07350015.2016.1247004**. citeturn14search0

26. **Haghayegh, S., Kang, H. A., Khoshnevis, S., Smolensky, M. H., & Diller, K. R. 2020.** “A comprehensive guideline for Bland–Altman and intra class correlation calculations to properly compare two methods of measurement and interpret findings.” *Physiological Measurement*, 41. DOI **10.1088/1361-6579/ab86d6**. citeturn15search0

27. **Inter-Agency Standing Committee / OCHA Centre for Humanitarian Data. 2021, revised 2023.** *IASC Operational Guidance on Data Responsibility in Humanitarian Action.* [Centre for Humanitarian Data](https://centre.humdata.org/iasc-operational-guidance-on-data-responsibility-in-humanitarian-action/). citeturn16search3

28. **Diepeveen, S., Bryant, J., & Wasuge, M. 2025.** “Outsourcing accountability: Extractive data practice and inequities of power in humanitarian third-party monitoring.” *Big Data & Society*, 12. DOI **10.1177/20539517251328250**. Estudio basado en 60 entrevistas en Somalia. citeturn16search1turn16search11

29. **Clausen, M.-L., Fejerskov, A. M., & Seddig, S. 2025.** “Datafied localization: Reproducing unequal power hierarchies in humanitarianism.” *Big Data & Society*, 12(2). DOI **10.1177/20539517241304693**. citeturn17search11

30. **Humanitarian Policy Group, ODI. 2020.** *Inclusion and exclusion in humanitarian action: the state of play.* Discute falta de datos adecuados, invisibilidad y mecanismos de exclusión. citeturn17search4

31. **FAO & WFP. 2025.** *Special Report: 2024 FAO/WFP Crop and Food Security Assessment Mission to the Republic of South Sudan.* CFSAM Special Reports 03/2025. DOI **10.4060/cd5136en**. citeturn18search1

32. **Lesiv, M., Karanam, S., Duerauer, M., See, L., Gilliams, S., Laso Bayas, J. C., et al. 2024.** *WorldCereal Phase 1: Validation Report.* 35 pp. DOI **10.5281/zenodo.13908673**. citeturn18search6

33. **Rustowicz, R., Cheong, R., Wang, L., Ermon, S., Burke, M., & Lobell, D. 2020.** *Semantic Segmentation of Crop Type in South Sudan Dataset*, version 1.0. DOI **10.34911/rdnt.v6kx6n**. Datos Sentinel-1, Sentinel-2 y PlanetScope con ground labels de 2016–2017. citeturn18search3