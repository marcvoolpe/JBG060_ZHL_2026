# Revisión independiente de la pregunta sobre severidad anual de inundación e impacto humanitario en Sudán del Sur

## Resumen del veredicto y puntuaciones

**Veredicto, 137 palabras.** **Proceder con cambios específicos.** La pregunta es distinta de una correlación espacial agrupada y tiene valor científico, pero el diseño propuesto no permite interpretar con seguridad un resultado nulo ni afirmar cuánto añade un pronóstico a la focalización. El principal problema es el resultado de impacto: Mobility Tracking mide población desplazada todavía presente cuando se realiza la evaluación, no nuevos desplazamientos por inundación. Sus fechas de encuesta variables, retornos, destinos y categoría genérica “disaster” contaminan precisamente la variación anual que se quiere estimar. OCHA es útil como resultado secundario, pero su cobertura es selectiva y “missing” no equivale a cero. La potencia publicada por el equipo es aritméticamente razonable bajo independencia ideal, pero optimista con tres años, errores de medida y agrupación por condado. El cambio prioritario es sustituir Mobility Tracking por DTM Event Tracking, tras auditar cobertura, causa y condado de origen. Sin esa auditoría, no usaría el estudio para interpretar un “null”.

| Criterio | Puntuación | Razón en una línea |
|---|---:|---|
| Novedad | **4/5** | Hay precedentes cercanos en Somalia, Bangladesh y África, pero no encontré el mismo panel within-county para Sudán del Sur. |
| Validez de las medidas | **2/5** | Mobility Tracking es un stock tardío y “disaster” no identifica inundaciones; OCHA tiene selección y definición variable. |
| Viabilidad estadística | **2/5** | El diseño puede detectar asociaciones grandes; tres o cuatro años y el error de medida limitan seriamente asociaciones moderadas. |
| Robustez frente a sesgo | **2/5** | Algunos sesgos pueden acotarse, pero varios no se eliminan con efectos fijos o modelos de conteo. |
| Relevancia para decisiones | **3/5** | Puede informar si merece la pena usar anomalías de peligro a escala condado, pero no valida directamente decisiones comunitarias a 3-14 días. |
| Ajuste al tiempo restante | **3/5** | Es realizable en dos sprints solo si se reduce a un resultado primario, una comprobación de inundación independiente y pocos análisis. |

**Convención usada a continuación:** **[Fuente]** indica una afirmación documentada externamente; **[Equipo]** una afirmación o cálculo proporcionado en el prompt que no doy por verificado salvo indicación; **[Inferencia]** mi juicio a partir de la evidencia; **[Cálculo]** un cálculo reproducido a partir de las cantidades dadas.

## Novedad y trabajo previo

**[Fuente] Sudán del Sur.** No encontré un estudio publicado que replique la pregunta exacta: anomalías anuales de extensión o duración de inundación dentro del mismo condado, relacionadas con un resultado humanitario observado anual, netas de la susceptibilidad persistente del condado. El trabajo más próximo en el Sudd es Chol et al. (2026), *Dynamics of human adaptation to flood risk in the Sudd wetlands, South Sudan*. Estudió la adaptación a las inundaciones mediante trabajo de campo en 2024, con 216 participantes, entrevistas y 13 grupos de discusión, y concluyó que las inundaciones extraordinarias de 2019-2022 alteraron medios de vida, movilidad y patrones de desplazamiento. Los autores describen su trabajo como una evaluación sistemática de las interacciones dinámicas población-inundación en el Sudd, pero no estiman un panel condado-año de severidad contra desplazamiento. citeturn5view0

**[Fuente]** Chol et al. (2026), *Geospatial Analysis of Population Exposure to Flooding in the Sudd Region, South Sudan*, combina varias representaciones de peligro y población para estimar exposición. El rango de exposición cambia sustancialmente según la combinación de mapas de inundación y población, y los autores recomiendan comparaciones entre fuentes por esa incertidumbre. Ese estudio es relevante para la medición del peligro y la exposición, pero su variable dependiente es exposición modelada, no impacto humanitario observado. citeturn5view1turn4search4

**[Fuente] Somalia ofrece el precedente más cercano.** Momeni et al. (2024), *Deciphering climate-induced displacement in Somalia: A remote sensing perspective*, estudió 16 distritos del centro y sur de Somalia durante 2016-2019. Construyó indicadores ambientales con Sentinel-1 y Sentinel-2 y utilizó datos mensuales de desplazamiento con causa, origen y destino. Procesó 32 escenas Sentinel-1, además de miles de imágenes Sentinel-2. El trabajo enlaza explícitamente información climática y desplazamiento a escala distrital y subraya problemas de calidad y disponibilidad de variables socioeconómicas. Sin embargo, no plantea el contraste exacto entre componente persistente del distrito y desviación anual ni la validación leave-one-year-out propuesta aquí. Momeni et al. (2024), DOI 10.1371/journal.pone.0304202. citeturn23view0

**[Fuente] África continental.** Nguyen et al. (2026), *Intensifying Flood Extent and Human Displacement Risk Across Africa*, combina inundación mensual derivada de Landsat/Sentinel-2 para 1984-2024 con registros subnacionales de desplazamiento de IDMC y emplea un modelo hurdle. El resumen presentado en EGU 2026 informa que, condicionado a que se produzca desplazamiento, un aumento de una desviación estándar en severidad de inundación se asocia con aproximadamente un 27% más de desplazamiento, con heterogeneidad espacial importante en Sahel, África austral y Cuerno de África. Es un precedente muy próximo conceptualmente, pero a fecha de esta revisión es un resumen de conferencia, no un artículo completo revisado por pares, y ese 27% no es comparable directamente con una correlación de Spearman. Nguyen et al. (2026), DOI 10.5194/egusphere-egu26-16224. citeturn22search1turn7view2

**[Fuente] Bangladesh muestra por qué cabe esperar no linealidad.** Freihardt (2025), *Environmental shocks and migration among a climate-vulnerable population in Bangladesh*, siguió a 1.604 jefes de hogar en 36 aldeas del Jamuna entre 2021 y 2022. La erosión fluvial elevó con claridad la probabilidad de migración, mientras que la inundación en general no mostró un efecto equivalente salvo cuando produjo consecuencias graves o irreversibles. Este resultado es consistente con un mecanismo en el que una crecida “normal” puede formar parte del sistema de vida y el impacto marginal aparece solo al superar ciertos umbrales. Freihardt (2025), DOI 10.1007/s11111-025-00478-7. citeturn7view0

**[Fuente]** En el Okavango, King et al. (2018), *Livelihood Dynamics Across a Variable Flooding Regime*, combinó teledetección, entrevistas cualitativas y mapeo de medios de vida en cinco aldeas durante 2011-2016. Encontró respuestas diferenciadas según localización, magnitud, duración y contexto del pulso de inundación. Es evidencia de que los impactos de una anomalía hidrológica pueden variar fuertemente dentro de un gran humedal, aunque no proporciona un efecto estadístico comparable al que se pretende estimar aquí. King et al. (2018), DOI 10.1007/s10745-018-0039-2. citeturn21view0

**[Fuente]** La literatura de evaluación de pronósticos de impacto también aconseja separar calidad del peligro y calidad del dato de impacto. Kuipers et al. (2026), *Assessing the Riverine Flood Forecast Skill of GloFAS and Google Flood Hub With Impact Data and Discharge Observations to Support Early Actions in Mali*, señala que la utilización de datos de impacto como “ground truth” se ve dificultada cuando la fecha y localización de los impactos no son precisas, por lo que complementa la validación con observaciones hidrológicas. Este problema es directamente pertinente cuando el resultado se asigna a años y condados a partir de evaluaciones realizadas meses después. citeturn2search4turn2search8

**[Fuente]** Kobler et al. (2026), *River Flood Impact Forecasting to Support Humanitarian Anticipatory Action*, compara impactos modelados y reportados para eventos en Etiopía, Nigeria y Uganda. El estudio encuentra que la clasificación relativa de la severidad puede ser útil, pero que los resultados son sensibles a supuestos como la protección frente a inundaciones y contienen sobreestimaciones y subestimaciones. Es evidencia indirecta a favor de comprobar la robustez de rankings, pero no resuelve la calidad de DTM u OCHA. Kobler et al. (2026), DOI 10.5194/egusphere-egu26-22105. citeturn2search0

**[Fuente] Error de medición.** Griliches y Hausman (1986), *Errors in Variables in Panel Data*, muestran que la transformación “within” puede agravar el sesgo por error de medición cuando la señal verdadera varía lentamente en el tiempo. Bound, Brown y Mathiowetz (2001), *Measurement Error in Survey Data*, documentan que los errores reales rara vez cumplen perfectamente el supuesto clásico de ruido independiente y recomiendan validación externa cuando sea posible. Es especialmente relevante aquí porque el análisis elimina deliberadamente el gran componente espacial estable y conserva el componente temporal pequeño, justo donde una cantidad fija de error representa una fracción mayor de la señal. DOI 10.1016/0304-4076(86)90058-8 y DOI 10.1016/S1573-4412(01)05012-7. citeturn3search9turn3search4

**[Inferencia sobre tamaño de efecto.]** La literatura no proporciona una base sólida para afirmar que una correlación within-county de 0,20, 0,30 o 0,40 sea “esperable” en Sudán del Sur. El 27% por desviación estándar del trabajo africano de Nguyen et al. es prometedor, pero corresponde a otra escala, modelo y definición del resultado. El panel de Bangladesh muestra que una asociación promedio puede ser pequeña cuando predominan inundaciones tolerables y grande entre episodios destructivos. Por ello, no consideraría 0,23-0,26 un umbral que garantice detectar “el efecto relevante”.

**[Inferencia: diferencia con las dos preguntas anteriores.]** La pregunta es **sustantivamente distinta** de una correlación exposición-impacto agrupada. Un análisis agrupado puede ser alto simplemente porque Jonglei o Unity suelen inundarse más y suelen tener más personas afectadas. La transformación within pregunta si un año excepcionalmente severo para *ese mismo condado* coincide con un impacto excepcionalmente alto para *ese mismo condado*. También es distinta de preguntar si superponer población o cultivos mejora la explicación respecto a extensión bruta, porque aquí la comparación principal es temporal y no entre capas de exposición.

Hay, sin embargo, dos problemas de interpretación. Primero, el baseline “usual impact level” contiene más información que “saber dónde se inunda habitualmente”: incorpora vulnerabilidad histórica, tamaño poblacional, accesibilidad y patrones pasados de reporte. Segundo, se está usando **inundación observada posteriormente**, no un pronóstico. Por tanto, el análisis puede estimar el valor explicativo incremental de la **severidad realizada**. No estima directamente el valor incremental de un pronóstico operativo a 3-14 días.

## Validez de las medidas

**[Fuente: producto de inundación.]** La documentación pública de NASA no coincide completamente con la descripción de los archivos del curso. NASA Earthdata publicó en abril de 2026 un archivo reprocesado MCDWD de **2003-2025**, no 2000-2025, y explica que la categoría “recurring flood” utiliza máscaras mensuales construidas con 22 años, 2003-2024, marcando lugares inundados en al menos siete de esos años. La función se incorporó al producto en diciembre de 2025. NASA denomina al producto aproximadamente 250 m y publica el archivo histórico MCDWD_L3 con DOI 10.5067/MODIS/MCDWD_L3.061. citeturn15search0turn15search8turn25search4

**[Equipo]** Que los archivos concretos del curso contengan 2000-2025, solo h20v08 y h21v08, y excluyan la clase de agua permanente son afirmaciones específicas del material proporcionado al proyecto. No encontré documentación pública que describa ese subconjunto exacto, por lo que esas tres propiedades del *course file* son **not verified**.

**[Fuente]** El producto estándar de NASA sí utiliza una máscara de agua de referencia y distingue agua superficial de inundación. La documentación explica además que las categorías de inundación recurrente y no recurrente son clasificaciones posteriores a detectar agua. citeturn25search0turn25search4

**[Inferencia]** Dado que la propuesta suma las clases “recurring” y “unusual”, el uso de 2003-2024 para decidir **entre esas dos etiquetas** tiene bastante menos importancia que tendría si se analizara solo “unusual”. Si las dos clases son exhaustivas para los píxeles clasificados como inundación, reclasificar un píxel de “unusual” a “recurring” no cambia el total combinado. Sigue siendo necesario comprobar cómo los archivos del curso tratan el agua de referencia y si el reprocesamiento histórico cambió detecciones, porque eso sí puede modificar extensión o duración.

**[Fuente: nubes.]** NASA declara expresamente que MCDWD se basa en observación óptica y no puede observar agua en el suelo cuando está cubierta por nubes. Los composites de dos y tres días intentan reducir este problema usando observaciones repetidas, mientras que el producto de un día puede sufrir falsos positivos por sombras de nubes; la máscara de sombras también puede retirar agua real. Por tanto, “sin detección” no es equivalente a “seco”. Slayback/NASA, *MODIS/VIIRS NRT Global Flood Products User Guide*, revisiones D/F. citeturn25search0turn25search4

**[Equipo]** El 5-7% de detecciones en julio-septiembre y el máximo noviembre-febrero son cálculos internos no reproducidos en esta revisión. **[Inferencia]** Incluso aceptándolos, la fracción estacional de *detecciones* no mide directamente la fracción de oportunidades perdidas por nubes. Para demostrar censura diferencial hace falta, como mínimo, un denominador de observaciones válidas o clear-sky por píxel/dekada. Una caída de detecciones también puede contener señal hidrológica real.

Hay, no obstante, evidencia independiente de que el problema puede ser grande en Sudán del Sur. **[Fuente]** Downs et al. (2023), *Assessing the Relative Performance of GNSS-R Flood Extent Observations: Case Study in South Sudan*, comparó un método GNSS-R con productos operativos Sentinel-1, VIIRS y MODIS en Sudán del Sur y el Sudd. En esa comparación, el producto MODIS subestimó el agua superficial en 83,7% respecto al método GNSS-R, mientras que VIIRS lo hizo en 4,8%. Eso no significa que MCDWD 2026 tenga “83,7% de error”, porque cambian algoritmos, periodos, referencia y definición de agua, pero demuestra que asumir alta fiabilidad de un producto MODIS en este ambiente sería injustificado. Downs et al. (2023), DOI 10.1109/TGRS.2023.3237461. citeturn25search6turn25search10

**[Fuente]** Un estudio específico de Sudán del Sur presentado por Revilla-Romero et al. (2024) comparó Sentinel-1 y VIIRS para 2017-2022. Encontró que VIIRS producía mayores extensiones y frecuencias, en parte por su mayor frecuencia de observación, mientras que distintas clasificaciones Sentinel-1 presentaban errores de omisión y comisión. Los autores no pudieron hacer validación in situ y recurrieron a intercomparación entre productos. Esa es probablemente la analogía más directa con la comprobación de fiabilidad que este proyecto necesita. citeturn25search2

**[Fuente: comprobación independiente recomendada.]** Copernicus Global Flood Monitoring, GFM, procesa Sentinel-1 SAR y, por tanto, observa de día o noche y a través de nubes. El servicio operativo empezó en 2021 y existe un archivo reprocesado de Sentinel-1; la documentación de acceso indica que el archivo completo y los datos NRT son accesibles mediante STAC y que existen interfaces WMS, API y descarga. El lanzamiento de CEMS especifica disponibilidad abierta de las capas. citeturn17search2turn17search6turn18view0turn19view0turn19view1

**[Fuente]** El informe de calidad 2024 de GFM, Seewald et al. (2025), evaluó 12 eventos frente a referencias independientes y utiliza el Critical Success Index como métrica temática; la especificación fija 70% como objetivo. El informe también documenta limitaciones por superficies con retrodispersión similar al agua, sombras radar, vegetación y baja cobertura, por lo que SAR tampoco constituye una verdad perfecta. Seewald et al. (2025), *Global Flood Monitoring - Annual Product and Service Quality Assessment Report 2024*, DOI 10.2760/9738940. citeturn25search1turn25search5

**[Inferencia]** Para dos sprints no intentaría reconstruir toda la severidad 2021-2025 con GFM. Tomaría una muestra estratificada de condado-años, especialmente los extremos positivos y negativos de la anomalía MCDWD, y preguntaría si **el ranking de anomalías** se reproduce con GFM. Ese ejercicio estima la fiabilidad de la variable que realmente entra en Spearman y permite distinguir “no hay relación con impacto” de “la anomalía óptica no está midiendo consistentemente la anomalía hidrológica”.

**[Fuente]** NASA VIIRS VCDWD no es una comprobación completa para 2021-2025: el producto VCDWD se lanzó en abril de 2025, aunque emplea un algoritmo similar a MCDWD. citeturn15search8turn25search4 **[Inferencia]** Sirve para 2025 y para comprobaciones contemporáneas, no como serie independiente homogénea de los cinco años.

**[Fuente]** WFP ADAM publica análisis de impacto que combinan, según el informe, NOAA-VIIRS, MODIS NRT, Sentinel-1 y otras fuentes. Por ejemplo, un informe de mayo de 2024 para Sudán del Sur expone extensión inundada y población/cultivos expuestos. citeturn15search3 **No verifiqué** un archivo WFP público, homogéneo, diario o dekadal, descargable para todos los condados de Sudán del Sur durante 2021-2025. Por ello no lo trataría como sustituto inmediato de MCDWD.

**[Equipo]** La duplicación de área inundada después de 2019, los porcentajes de suelo inundado tres meses o más y la descomposición 71-91% condado, 0,3-6% año y 7-24% interacción son análisis internos y **not verified** en sus valores exactos. **[Fuente]** La existencia de un cambio hidrológico importante después de 2019 sí tiene apoyo independiente: Munyejuru et al. (2026), *Lake Victoria to the Sudd Wetland: flood wave timing, connectivity and wetland buffering across the White Nile*, documenta un régimen excepcional 2019-2024 y máximos de extensión del Sudd por encima del máximo MODIS previo durante todos esos años. El estudio encuentra fuerte memoria del sistema y propagación de almacenamiento desde el sistema de lagos ecuatoriales. DOI 10.5194/hess-30-5297-2026. citeturn24search0turn24search8

**[Fuente e hidrología.]** Este último trabajo verifica el fundamento general de que el Bahr el Jebel/Sudd está hidrológicamente conectado con Lake Victoria, Kyoga y Albert y que el almacenamiento aguas arriba puede influir durante meses o años. citeturn24search0 **[Equipo]** No verifiqué en una fuente suficientemente directa, dentro de esta revisión, la formulación geográfica exacta “Bor South está en el Bahr el Jebel aguas abajo de la estación Mongalla”. La considero plausible, pero bajo las reglas solicitadas queda **not verified**. Tampoco verifiqué con una fuente primaria que permita concluir que en el tramo del Lol la lluvia local sea *más importante* que el forzamiento aguas arriba. El Bahr el Ghazal sí presenta una fuerte estacionalidad de precipitación y grandes pérdidas en humedales, pero eso no prueba la comparación causal específica del Lol. citeturn24search1

**DTM Mobility Tracking**

**[Fuente]** La documentación de IOM describe Mobility Tracking como una evaluación de la **presencia** de IDPs y retornados en lugares y comunidades de acogida en el momento de la evaluación. Round 16, por ejemplo, fue recopilado entre diciembre de 2024 y febrero de 2025 en 78 condados y estima la población presente. Round 14 se recopiló en marzo-abril de 2023 y Round 15 en agosto-septiembre de 2024. Por construcción, esas evaluaciones son stocks observados en fechas diferentes, no un registro de incidencias de desplazamiento en el momento del evento. citeturn10search3turn11search13turn11search11turn24search3

**[Fuente]** La metodología de Mobility Tracking recoge características como periodo de llegada, razón y antiguos lugares de residencia a nivel de grupos y, en varias rondas, mediante información de informantes clave o atributos mayoritarios. Eso es útil para perfilar poblaciones presentes, pero no convierte el stock en flujo anual de desplazamiento. citeturn11search13turn24search3

**[Equipo]** Las cifras del prompt en las que, por ejemplo, el cohorte 2022 nacional cae de 219.241 en R14 a 77.381 en R16, Rubkona cae de 47.772 a 13.537, Juba de 28.496 a 286 y Duk 2023 aumenta entre R15 y R16 no fueron recalculadas independientemente aquí. Si los extractos del equipo son correctos, constituyen evidencia interna muy fuerte de retornos, cambios de cobertura o clasificación. No es posible interpretar la diferencia entre esos stocks como únicamente “cuántas personas desplazó la inundación de ese año”.

**[Inferencia: validez.]** “DTM disaster IDPs present, arrival year” es **inadecuado como resultado primario de desplazamiento anual por inundación**. Tiene simultáneamente:

| Problema | Consecuencia para la estimación within |
|---|---|
| Stock en vez de flujo | Un año puede parecer de bajo impacto porque las personas volvieron antes de la encuesta. |
| Intervalo temporada-encuesta distinto | La tasa de supervivencia del stock difiere entre años. |
| “Disaster” no específico de inundación | Introduce eventos meteorológicos o desastres no capturados por la severidad de inundación. |
| Lugar de presencia distinto del origen | Un hub receptor puede recibir impacto sin inundación local. |
| Origen “principal” o mayoritario | Introduce clasificación geográfica imperfecta. |
| Año calendario | Divide una temporada entre diciembre y enero, especialmente cuando el desplazamiento continúa después del pico. |
| Cobertura y clasificación variables | Cohortes pueden incluso aumentar en rondas posteriores. |

Estos problemas no son ruido puramente aleatorio. Varios dependen de accesibilidad, movilidad, gravedad y tiempo transcurrido, por lo que pueden sesgar tanto la magnitud como el signo de una asociación.

**[Fuente: alternativa DTM.]** DTM South Sudan publica **Event Tracking** para 2021, 2022, 2023, 2024 y 2025 como producto separado de Mobility Tracking. Event Tracking está diseñado para registrar movimientos y eventos localizados con mayor rapidez y, por ello, está conceptualmente más cerca de “nuevos desplazamientos asociados a una inundación” que las evaluaciones baseline. Existen páginas de datasets públicos para cada uno de esos años. citeturn11search8turn11search2turn11search3turn11search0turn11search5

**[Fuente]** Event Tracking tampoco es un censo completo. En informes de 2024, IOM especifica que el seguimiento responde a movimientos por encima de determinados umbrales, por ejemplo más de 50 hogares, mediante visitas o informantes clave, triangula con otras fuentes y advierte que no se puede garantizar cobertura nacional completa. citeturn9search6 En 2021, DTM publicó también una base a nivel de movimiento/evento que distinguía, entre otras causas, desastre natural/inundación. citeturn10search2

**[Inferencia]** Event Tracking es el candidato correcto para una auditoría de una o dos jornadas antes de comprometer el análisis. Hay que comprobar en los ficheros descargables de cada año, no solo en los informes, cuatro cosas: fecha del movimiento, causa suficientemente específica para inundación, condado de origen y significado de una ausencia de registro. Si los tres primeros campos son comparables y se puede construir una regla coherente para cobertura, lo usaría como resultado primario. Si no, no sustituiría automáticamente un dato malo por otro dato de selección desconocida.

**[Fuente]** Flow Monitoring de DTM observa movimientos en puntos estratégicos, pasos fronterizos o localizaciones concretas. Informes de Mangala y otros puntos muestran su utilidad operativa, pero su muestreo espacial no pretende representar todos los condados del país. citeturn11search14turn10search1turn10search6 **[Inferencia]** No es un resultado adecuado para este panel nacional.

**OCHA people affected**

**[Fuente]** La ficha pública de OCHA/HDX, *South Sudan: Flood Data*, describe el conjunto como personas reportadas afectadas por inundaciones por estado y condado. La metodología especifica que las cifras reflejan personas **evaluadas y verificadas hasta la fecha** y pueden no representar a todas las personas afectadas. El metadata clasifica la fuente como observación directa/datos anecdóticos. El repositorio incluye recursos para 13 diciembre 2021, 21 octubre y 30 noviembre 2022, 2024 y 2025; no presenta una serie anual completa y homogénea. citeturn14search2

**[Fuente]** En noviembre de 2022 OCHA reportaba aproximadamente 1,1 millones de personas verificadas como afectadas por inundaciones en 39 condados. En 2024 las cifras fueron actualizándose durante la temporada conforme avanzaban evaluaciones y verificaciones, con snapshots de septiembre y noviembre que cubrían distintos conjuntos de condados. citeturn12search1turn14search1turn14search3 Esto confirma que un snapshot es un estado del proceso de evaluación, no necesariamente la incidencia final comparable de todos los condados.

**[Inferencia]** OCHA es más cercano semánticamente a “impacto por inundación” que Mobility Tracking, pero su mecanismo de observación es peor para inferencia estadística estándar: la probabilidad de que exista un número depende probablemente de que haya motivos para evaluar, de acceso y de capacidad operativa. Un condado ausente no puede codificarse como cero.

**[Equipo]** La asociación logit `p ≈ 0,001` entre evaluación y exposición satelital y el problema de muestrear una sola celda de población por píxel son cálculos del equipo, **not verified** externamente. **[Fuente]** La documentación pública confirma la evaluación y verificación incompletas, pero **no encontré documentación que establezca que las cifras de personas afectadas se calculen mecánicamente a partir del mismo producto NASA MCDWD**. citeturn14search2

Por ello, **la circularidad fuerte no está verificada**. Hay una circularidad más débil que sí es plausible: si las imágenes o informes de inundación contribuyen a decidir dónde mandar evaluadores, la inclusión del condado queda condicionada al peligro observado. Eso puede elevar artificialmente la relación entre inundación e impacto entre los condados observados. Al mismo tiempo, falta de acceso a los lugares más gravemente afectados puede generar sesgo en sentido contrario. No asumiría de antemano el signo.

## Diseño estadístico, potencia y sesgos

**Potencia.** **[Cálculo]** La cuenta del equipo basada en Fisher z es correcta como aproximación ideal. Para una prueba bilateral con α = 0,05 y 80% de potencia:

\[
r_{\min}\approx \tanh\left(\frac{1.96+0.842}{\sqrt{n-3}}\right).
\]

Con \(n=142\), da aproximadamente **0,233**. Con \(n=77\), da aproximadamente **0,315**. Si el subconjunto DTM reduce el número efectivo a alrededor de 120 observaciones independientes, el valor es aproximadamente **0,253**. Por tanto, el rango 0,23-0,26 para DTM y 0,31 para OCHA es aritméticamente razonable.

**[Inferencia]** El problema está en llamar a \(\sum(T_i-1)\) “n efectivo”. Es exactamente la dimensión de variación temporal que queda tras retirar medias de condado en un panel sencillo, pero no convierte esas observaciones en pares independientes para una correlación de Spearman. Las observaciones de un mismo condado comparten error de medición y contexto, y los condados de un mismo año comparten shocks nacionales. Con DTM hay solo tres temporadas independientes a nivel temporal. Un bootstrap por condado resuelve parte de la dependencia intraclúster, pero no crea más años.

Como ilustración conservadora, no como cálculo de potencia formal, la misma fórmula usando 60 unidades independientes produce un MDE de aproximadamente **0,355**, y usando 51 produce **0,384**. El verdadero umbral estará entre una visión excesivamente optimista que trata ~142 residuos como independientes y una visión excesivamente conservadora que trata solo los condados como información. La potencia debe presentarse mediante simulación bajo el diseño real, con tres años, ceros, empates, ICC y bootstrap por condado.

**Error de medición.** Bajo el caso clásico e independiente, una correlación observada se atenúa aproximadamente como

\[
r_{obs}=r_{true}\sqrt{R_xR_y},
\]

donde \(R_x\) y \(R_y\) son las fiabilidades de severidad e impacto. Esta fórmula es una sensibilidad, no una estimación de las fiabilidades reales. La literatura de Griliches y Hausman advierte además de que diferenciar o retirar medias puede empeorar la relación señal-ruido de variables persistentes. citeturn3search9

| Fiabilidad severidad | Fiabilidad impacto | Factor de atenuación | Correlación real necesaria para observar 0,23 | Para observar 0,31 |
|---:|---:|---:|---:|---:|
| 0,90 | 0,90 | 0,90 | 0,26 | 0,34 |
| 0,80 | 0,80 | 0,80 | 0,29 | 0,39 |
| 0,60 | 0,60 | 0,60 | 0,38 | 0,52 |
| 0,50 | 0,50 | 0,50 | 0,46 | 0,62 |
| 0,60 | 0,40 | 0,49 | 0,47 | 0,63 |

**[Inferencia]** No afirmo que la fiabilidad sea 0,5 o 0,8. La tabla muestra por qué hace falta medirla. Si el error de MCDWD o del resultado reduce la fiabilidad within a aproximadamente 0,5-0,6, un efecto moderado verdadero puede quedar por debajo del MDE. Un null sin validación de fiabilidad tiene poco contenido.

**[Equipo]** El equipo informa que 71-91% de la varianza de área inundada se atribuye al condado y solo una fracción pequeña al año. **[Inferencia]** Si ese resultado se reproduce, refuerza la preocupación: la pregunta elimina justamente el gran componente que MCDWD parece medir con claridad y basa la inferencia en el residuo temporal relativamente pequeño.

**La desviación leave-one-out.** Para un condado con \(T\) años,

\[
x_{it}-\overline{x}_{i,-t}
=\frac{T}{T-1}(x_{it}-\overline{x}_{i}).
\]

Con tres años es simplemente 1,5 veces la desviación respecto a la media completa del condado. **[Inferencia]** Por tanto, en el panel balanceado DTM de tres años el leave-one-out no genera una noción estadísticamente distinta de “within”; solo reescala la variable. Para Spearman, un factor positivo común ni siquiera cambia los rangos. En OCHA, donde \(T_i\) varía entre condados, el factor sí cambia entre unidades y puede alterar ligeramente la clasificación global.

**[Inferencia]** Hay una razón fuerte para añadir efectos de año. Si 2024 fue simultáneamente un año de inundación más grave, mayor llegada desde Sudán y distinta cobertura humanitaria, una correlación de desviaciones de condado puede recoger ese shock común. Los efectos de año no permiten identificar qué componente nacional causó qué, pero evitan atribuir automáticamente la diferencia nacional a la severidad espacial.

**Enfoque primario recomendado:** **OLS de efectos fijos de condado y año sobre `log1p`, con el coeficiente de severidad estandarizado**, acompañado de intervalos mediante bootstrap por condado. El modelo sería descriptivo:

\[
\log(1+Impact_{it}) =
\alpha_i+\gamma_t+\beta\log(1+Severity_{it})+\varepsilon_{it}.
\]

No lo interpretaría causalmente. Elegiría a priori **una** métrica principal de severidad, preferiblemente extent × duration si se demuestra que su fiabilidad es al menos similar a la de extensión, y trataría las demás como sensibilidad. Con tan pocos años, probar tres métricas y dos outcomes como análisis equivalentes multiplica decisiones analíticas sin aportar mucha información.

**Robustez recomendada:** la correlación de Spearman sobre desviaciones within, con bootstrap por condado, más una versión que retire previamente el efecto de año. Conserva el atractivo original: es transparente, poco sensible a unos pocos conteos gigantes y fácil de explicar a ZOA.

**Por qué no pondría PPML como primario.** PPML es razonable para conteos con ceros y permite efectos fijos. Sin embargo, aquí el principal problema no es la distribución condicional del conteo sino qué significa el conteo. Con tres años y un outcome afectado por supervivencia, ubicación y clasificación, un modelo más sofisticado no recupera la variable de impacto perdida. Si Event Tracking produce un panel de nuevos desplazamientos razonablemente completo, PPML de dos vías sería una buena comprobación adicional, no una prioridad en los dos sprints.

**Por qué no negative binomial.** Ofrece flexibilidad frente a sobredispersión, pero diferentes formulaciones de “fixed-effects negative binomial” no eliminan de la misma manera heterogeneidad fija, y con \(T=3\) no hay ventaja suficiente frente al coste adicional de supuestos. No lo usaría en este capstone.

**Por qué no primeras diferencias.** Con tres años solo quedan dos diferencias por condado, y diferenciar amplifica el error de medición cuando una variable es persistente, precisamente el problema descrito por Griliches y Hausman (1986). citeturn3search9

**Por qué no un modelo jerárquico Bayesiano como principal.** Un random intercept y una pendiente común son estimables, pero con tres observaciones por condado no hay información suficiente para aprender pendientes de condado de manera robusta sin que las priors y el pooling determinen gran parte del resultado. Tampoco corrige selección o medición errónea por sí mismo.

**Por qué no Heckman.** Con 44 condados OCHA que tienen al menos dos observaciones según el equipo, y sin una variable de exclusión creíble que afecte evaluación pero no impacto, un modelo de selección Heckman se identificaría en buena medida por forma funcional. La recomendación anterior de usarlo puede tener sentido en una base mucho mayor y con un mecanismo de selección bien caracterizado. Aquí no. Preferiría mostrar explícitamente el patrón de evaluación, comparar condados observados y no observados y ejecutar una sensibilidad de selección o ponderación solo si se puede defender una probabilidad de evaluación.

**Controles de conflicto.** El conflicto es sustantivamente pertinente porque puede causar desplazamiento y afectar acceso y respuesta. Sin embargo, **[Equipo]** el UCDP disponible tiene una mediana aproximada de dos eventos por condado. **[Inferencia]** Añadir varios controles de conflicto, retorno, ayuda y mercados a un panel de tres años puede consumir la poca variación útil y añadir más error. Usaría, como máximo, un indicador preespecificado de intensidad de conflicto como sensibilidad. No convertiría el análisis en una regresión causal multivariable.

**ACLED, DHIS2 y cólera.** La recomendación previa de usar ACLED como control es conceptualmente razonable, pero no esencial para contestar la pequeña pregunta propuesta. DHIS2 y cólera responden a otra cadena causal, con distintos tiempos y mecanismos, y no son sustitutos naturales de desplazamiento o cosecha. No los añadiría a este sprint únicamente porque aparecieron en una revisión anterior.

**Leave-one-year-out.** En DTM tal como está propuesto habría tres folds, y cada modelo se entrenaría solo con dos años. Eso permite un ejercicio de honestidad predictiva, pero no una estimación estable de generalización interanual. Más importante, el predictor es la **severidad observada de ese año**, así que el ejercicio no simula una decisión a 3-14 días. Lo denominaría “out-of-year explanatory prediction with observed severity”, no validación de forecast.

**[Inferencia]** Informaría MAE o error absoluto sobre `log1p`, y para cada año mostraría la diferencia de error entre baseline y baseline + severidad. No resumiría tres folds en una cifra aparentemente precisa sin mostrar los tres resultados.

**Ranking de amenazas**

| Rango | Amenaza | Clasificación | Razón y tratamiento |
|---:|---|---|---|
| 1 | Supervivencia y timing de Mobility Tracking | **Fatal para el outcome propuesto** | El stock puede caer por retorno y varía el retraso encuesta-evento. Sustituir por Event Tracking o redefinir explícitamente el outcome como stock superviviente. |
| 2 | Desplazamiento entre condados / hub de destino | **Fatal si se usa destino contra peligro de origen** | El hazard local no puede explicar lógicamente personas desplazadas desde otro condado. Usar origen del movimiento cuando sea fiable. |
| 3 | Selección OCHA | **Grave, parcialmente manejable** | Nunca poner missing = 0. Describir selección y usar OCHA como resultado secundario; sensibilidad de ponderación solo con modelo de selección defendible. |
| 4 | Error de medición de severidad óptica | **Grave, manejable parcialmente** | Estimar fiabilidad del ranking frente a GFM Sentinel-1 en una muestra o en todo el panel si es barato. |
| 5 | Confusores variables en el tiempo | **Grave, parcialmente manejable** | Efectos de año y una sensibilidad de conflicto. No afirmar causalidad. |
| 6 | Año calendario frente a temporada | **Grave, manejable con mejor outcome** | Event Tracking permite ventanas estacionales por fecha; arrival-year de Mobility Tracking no. |
| 7 | Solo años post-2020 | **Manejable para el estimando, fatal para extrapolar regímenes** | Formular la conclusión específicamente para el régimen húmedo 2021-2025. |
| 8 | Pocos años | **Estructural** | No se corrige con otro estimador. Limitar claims y reportar incertidumbre real. |

**[Fuente sobre el contexto del régimen.]** La restricción post-2020 merece atención porque Munyejuru et al. (2026) encuentra que 2019-2024 constituye un periodo hidrológico excepcional con memoria multianual en el sistema Lake Victoria-Sudd. citeturn24search0turn24search8 **[Inferencia]** Un resultado en 2021-2025 puede ser muy pertinente para el régimen operativo reciente y, al mismo tiempo, poco informativo sobre décadas normales o secas.

## Relevancia para ZOA y para el trabajo de pronóstico

La interpretación propuesta necesita restringirse en los tres posibles resultados.

| Resultado | Qué sí permitiría concluir | Qué no permitiría concluir |
|---|---|---|
| **Vínculo claro** | Las anomalías de severidad **observada** contienen información sobre qué condados tuvieron impactos excepcionalmente altos respecto a su propio nivel usual. Eso justifica investigar si un forecast hábil puede anticipar esa señal. | Que el forecast actual añade esa información con 3-14 días de antelación, o que permite elegir comunidades concretas. |
| **Null claro** | Solo si las dos medidas tienen fiabilidad demostrada y el intervalo excluye un efecto operacionalmente relevante: no se detecta una relación within grande durante 2021-2025. | “El impacto sigue el mapa de recurrencia” o “los forecasts solo sirven para timing”. Con medición pobre, un null es compatible con una relación real atenuada. |
| **Inconcluso** | Los datos actuales no pueden validar el uso de anomalías de inundación para priorización espacial. | Que el hazard o el forecast carezcan de valor real. |

El segundo renglón es la divergencia más importante respecto a la interpretación de los proponentes. **Un null estadístico no se convierte automáticamente en evidencia a favor del baseline estático.** Para hacer esa afirmación hay que demostrar primero que la variable dinámica tenía suficiente variación y fiabilidad para superar razonablemente al baseline.

**[Equipo]** ZOA opera a nivel comunitario, necesita 3 días como mínimo, considera 10 días suficientes y 14 días un límite robusto, y en sus áreas prioriza principalmente fracaso de cosecha. **[Inferencia]** Un outcome anual a admin2 no está alineado directamente con esas decisiones en tres dimensiones: escala espacial, escala temporal y tipo de impacto.

El condado sigue teniendo una función legítima como prueba intermedia: puede responder “¿la variación interanual observada del hazard contiene alguna señal de impacto por encima de la geografía persistente?”. Eso es útil para decidir si merece la pena invertir en una siguiente capa de modelado de impacto. No responderá “¿qué comunidad de Bor South debería recibir semillas, efectivo o transporte dentro de nueve días?”.

**[Equipo]** En Aweil/Lol los archivos del curso muestran severidades muy pequeñas y Bor South habría permanecido dentro de aproximadamente -20% a +25% de su nivel usual en 2022-2024. Esas cifras son **not verified** externamente. **[Inferencia]** Si se reproducen, implican que incluso un resultado nacional positivo puede tener poca relevancia para las dos zonas de ZOA. Aweil podría estar cerca del suelo de detección del producto, mientras que Bor South tendría poca separación entre los años disponibles. Es imprescindible mostrar a ZOA los resultados de sus dos áreas por separado, sin inferir que el efecto nacional se aplica localmente.

**[Fuente]** La hidrología reciente del Sudd respalda que la severidad local puede tener memoria y drivers aguas arriba, por lo que “este año” tampoco equivale necesariamente a “lluvia local de esta estación”. Munyejuru et al. (2026) estima lags prolongados a través del sistema Lake Victoria-Sudd y destaca almacenamiento multianual. citeturn24search0turn24search8 Para interpretación de Bor, eso favorece describir el predictor como **estado de inundación observado**, sin atribuirlo automáticamente a precipitación anual local.

**¿Es desplazamiento el impacto correcto?** Para la pregunta amplia “¿se traduce una anomalía de flood hazard en impacto humanitario observable?”, sí es defendible, siempre que se mida como flujo y origen. Para la necesidad concreta de ZOA, **no es el outcome de mayor alineación**, porque la prioridad indicada es fracaso de cosecha.

**[Fuente]** FAO/WFP realiza Crop and Food Security Assessment Missions, CFSAM, en Sudán del Sur, y el repositorio CLiMIS publica informes y datos de producción agrícola. Se verificaron públicamente informes para 2021, 2022, 2024 y 2025, y el informe de 2024 incluye estimaciones de superficie cosechada y producción y trabajo de evaluación realizado durante plantación y cosecha. El informe 2021 atribuyó parte de la caída de producción a inundaciones y sequías prolongadas. citeturn24search2turn25search3turn25search7

Sin embargo, **no verifiqué una variable uniforme, a nivel de condado, 2021-2025, que mida específicamente “cosecha perdida por inundación” con cobertura comparable cada año**. Por las reglas de este encargo, no recomiendo sustituir el outcome por un dataset de pérdidas agrícolas que no he podido verificar. Una auditoría rápida de las tablas de CFSAM/CLiMIS puede determinar si producción o rendimiento de cereal por condado existe de forma consistente, pero no debe asumirse.

**[Equipo]** IPC está disponible en cinco rondas entre 2022-2025. **[Inferencia]** IPC no sería un sustituto limpio de harvest failure porque integra múltiples determinantes de inseguridad alimentaria, incluidos conflicto, precios y acceso. Tampoco utilizaría FEWS NET harvested area como outcome principal dado el resultado negativo within ya reportado por el equipo y su componente modelado.

Para el equipo que desarrolla el forecast, el análisis propuesto debe presentarse como una prueba de **impact relevance of observed hazard**, que antecede a la validación de un forecast. La secuencia lógica sería:

`forecast → flood severity → exposure/vulnerability → impact`.

Este estudio solo contrasta de forma retrospectiva el segundo enlace con el cuarto. Incluso una relación fuerte no demuestra que el primer enlace sea suficientemente preciso a 3-14 días.

## Cambios recomendados y veredicto final

**Prioridad máxima: cambiar el resultado primario.** Sustituir “Mobility Tracking disaster IDPs present by arrival year” por **DTM Event Tracking, nuevos movimientos atribuibles específicamente a inundación/desastre natural y asignados al condado de origen**, solo si una auditoría de los ficheros 2021-2025 confirma campos comparables y suficiente cobertura. Este cambio corrige simultáneamente stock versus flujo, gran parte del sesgo de retorno, el desfase de rondas y, si existe el origen, el problema de hubs. Los datasets Event Tracking de los cinco años existen públicamente, aunque su cobertura es event-driven y debe cuantificarse. citeturn11search8turn11search2turn11search3turn11search0turn11search5turn9search6

**Segunda prioridad: validar la variable de severidad, no reconstruirla.** Comparar el ranking de anomalías MCDWD con Copernicus GFM Sentinel-1. Como mínimo incluir condado-años con anomalías MCDWD extremas, los dos ámbitos de ZOA y algunos casos cercanos a cero. El problema que resuelve es la atenuación por nubes y la posibilidad de que el componente temporal sea menos fiable que el espacial. GFM ofrece SAR all-weather y archivo accesible. citeturn17search2turn19view1turn25search1

**Tercera prioridad: cambiar el estimando verbal.** La pregunta debería decir aproximadamente: *“¿La severidad de inundación observada en una temporada aporta información sobre la variación anual del impacto registrado dentro de los condados, más allá de diferencias persistentes entre condados?”* El problema que resuelve es el salto injustificado desde severidad retrospectiva a “valor añadido de un pronóstico”. El forecast solo entra después.

**Cuarta prioridad: efectos de año y un solo análisis principal.** Usaría TWFE `log1p` con efectos de condado y año como análisis principal y Spearman within como robustez. Preespecificaría una métrica primaria de severidad. El problema que resuelve es la contaminación por shocks nacionales y la multiplicidad de tres métricas casi redundantes.

**Quinta prioridad: redefinir el periodo por temporada cuando el outcome lo permita.** Con Event Tracking, usar una ventana de inundación razonada hidrológicamente y asignar movimientos por fecha, en lugar de asumir que 1 enero-31 diciembre corresponde a un evento independiente. El problema que resuelve es el desplazamiento que cruza enero.

**Sexta prioridad: relegar OCHA a triangulación.** Mantener únicamente condado-años explícitamente evaluados, documentar el denominador de evaluación y nunca transformar missing en cero. Informar si las conclusiones cambian al usar OCHA, pero no combinar ambos outcomes como si fueran dos mediciones independientes del mismo constructo. El problema que resuelve parcialmente es selección y ascertainment. citeturn14search2

**Séptima prioridad: sustituir el cálculo de potencia simple por simulación.** Simular paneles con exactamente los \(T_i\) observados, distribución de ceros, efecto de año, ICC y las fiabilidades observadas en la comprobación GFM. Evaluar la probabilidad de detectar correlaciones verdaderas de 0,2, 0,3, 0,4 y 0,5. El problema que resuelve es que Fisher z con \(n=\sum(T_i-1)\) ignora estructura del panel y empates.

No recomendaría, dentro de los dos sprints, añadir simultáneamente Heckman, negative binomial, Bayesian hierarchical, ACLED, DHIS2, cólera y múltiples outcomes. Esa ampliación reduciría auditabilidad y no corrige el defecto central de medición.

**Justificación de la puntuación, Novedad 4/5.** Existe trabajo próximo a nivel distrital en Somalia y un análisis subnacional africano reciente, además de literatura de movilidad y grandes humedales. citeturn23view0turn22search1turn21view0 No encontré el contraste concreto within-county de severidad anual versus impacto observado para Sudán del Sur. No otorgo 5 porque Momeni et al. ya enlaza teledetección y desplazamiento a escala distrital en un contexto extraordinariamente comparable, y Nguyen et al. aborda directamente inundación y desplazamiento subnacional africano.

**Validez de las medidas 2/5.** NASA MCDWD tiene una limitación óptica explícita y estudios de Sudán del Sur encuentran discrepancias sustanciales entre sensores. citeturn25search0turn25search6 Mobility Tracking mide presencia de IDPs en una fecha de evaluación, mientras que OCHA dice explícitamente que sus cifras reflejan población evaluada y verificada y pueden no representar todos los afectados. citeturn24search3turn14search2 Estos problemas afectan directamente el componente interanual. No doy 1 porque Event Tracking y GFM ofrecen rutas verificables para mejorar las dos medidas.

**Viabilidad estadística 2/5.** El MDE ideal de ~0,23 para 142 dimensiones within y ~0,31 para 77 es correcto matemáticamente, pero los datos contienen solo tres años DTM y cuatro snapshots potenciales OCHA, con dependencia por condado, ceros y error de medición. La teoría de paneles con measurement error indica que la transformación within puede agravar la atenuación. citeturn3search9 La muestra puede detectar asociaciones grandes y consistentes, pero no proporciona una prueba sensible de relaciones pequeñas o moderadas.

**Robustez frente a sesgo 2/5.** Efectos de año, asignación por origen, análisis de selección y validación GFM pueden reducir problemas. No pueden reconstruir retrospectivamente las personas que volvieron antes de una ronda DTM, convertir OCHA en una muestra probabilística ni añadir años independientes al panel. La dirección de algunos sesgos es además ambigua. Un nivel 3 requeriría poder acotar cuantitativamente varios de esos problemas, algo que todavía no se ha hecho.

**Relevancia para decisiones 3/5.** El resultado puede decidir si una anomalía de hazard a escala condado merece utilizarse como input para priorización, lo que es relevante para el trabajo de forecasting. Sin embargo, el diseño anual/admin2 no replica decisiones comunitarias a 3-14 días y desplazamiento no coincide con la prioridad de fracaso de cosecha. Un vínculo positivo tendría una implicación clara; un null solo sería decisivo después de demostrar buena fiabilidad. Por ello no todos los resultados actuales mapean limpiamente a una decisión.

**Ajuste al tiempo restante 3/5.** Un proyecto reducido a un outcome Event Tracking auditado, una métrica principal de severidad, una comprobación GFM y dos estimadores es realizable como capstone. El programa completo del prompt, más sustitutos agrícolas, selección OCHA, múltiples modelos y validación de forecast, no lo es razonablemente en dos sprints. Esta puntuación presupone que el equipo elimina análisis secundarios.

**Veredicto final: proceder con cambios específicos.** No procedería **como está escrito**. El estudio sí conserva una pregunta identificable y razonablemente novedosa si se interpreta como asociación retrospectiva within-county y se cambia la medición de impacto.

El **cambio único más importante** es sustituir el stock de Mobility Tracking por una medida de **nuevo desplazamiento por inundación en el condado de origen**, comenzando por una auditoría de DTM Event Tracking 2021-2025.

La evidencia que revertiría mi recomendación hacia **“do not proceed”** sería que Event Tracking no permita construir de forma comparable al menos tres o cuatro temporadas con causa de inundación, fecha y origen, y que OCHA siga siendo el único outcome alternativo. En ese caso la pregunta sobre “year-specific flood impact” no estaría suficientemente observada. En sentido contrario, si una auditoría demostrara que Mobility Tracking recupera casi exhaustivamente nuevos desplazamientos, con origen correcto y poca sensibilidad al intervalo encuesta-evento, esa evidencia podría justificar mantenerlo. La información disponible actualmente apunta en la dirección contraria.

## Tabla de evidencia

| Afirmación evaluada | Fuente | Aplicación |
|---|---|---|
| No hay un precedente idéntico identificado en Sudán del Sur; la literatura local estudia adaptación y exposición | Chol et al. (2026), *Dynamics of human adaptation to flood risk in the Sudd wetlands*; Chol et al. (2026), *Geospatial Analysis of Population Exposure to Flooding in the Sudd Region* | **Directa** al contexto, indirecta al estimando citeturn5view0turn5view1 |
| Teledetección + desplazamiento a escala distrital es factible en un contexto cercano | Momeni et al. (2024), *Deciphering climate-induced displacement in Somalia*, DOI 10.1371/journal.pone.0304202 | **Análoga muy cercana** citeturn23view0 |
| Mayor severidad de inundación puede asociarse con mayor desplazamiento subnacional africano | Nguyen et al. (2026), *Intensifying Flood Extent and Human Displacement Risk Across Africa*, DOI 10.5194/egusphere-egu26-16224 | **Análoga**, evidencia preliminar de conferencia citeturn22search1 |
| Inundación ordinaria y destrucción severa pueden tener relaciones distintas con movilidad | Freihardt (2025), *Environmental shocks and migration among a climate-vulnerable population in Bangladesh*, DOI 10.1007/s11111-025-00478-7 | **Análoga** citeturn7view0 |
| Grandes humedales producen respuestas locales heterogéneas a cambios del pulso de inundación | King et al. (2018), *Livelihood Dynamics Across a Variable Flooding Regime*, DOI 10.1007/s10745-018-0039-2 | **Análoga** citeturn21view0 |
| Measurement error puede ser especialmente dañino en estimadores within | Griliches & Hausman (1986), *Errors in Variables in Panel Data*, DOI 10.1016/0304-4076(86)90058-8 | **Directa al diseño estadístico** citeturn3search9 |
| MCDWD es óptico y no observa agua bajo nubes | NASA/Slayback, *MODIS/VIIRS NRT Global Flood Products User Guide* | **Directa a la medida de severidad** citeturn25search0turn25search4 |
| El archivo NASA estándar es 2003-2025 y la máscara recurring usa 2003-2024, ≥7 años | NASA Earthdata (2026), *NASA Enhances Global Flood Products...* | **Directa** citeturn15search0turn15search8 |
| Productos MODIS, VIIRS, SAR pueden diferir mucho en Sudán del Sur | Downs et al. (2023), *Assessing the Relative Performance of GNSS-R Flood Extent Observations*, DOI 10.1109/TGRS.2023.3237461 | **Directa** citeturn25search6 |
| GFM Sentinel-1 ofrece una comprobación SAR con archivo abierto | Copernicus EMS, *Global Flood Monitoring*; Seewald et al. (2025), QA report, DOI 10.2760/9738940 | **Directa** citeturn17search2turn25search1 |
| Mobility Tracking estima IDPs presentes durante la evaluación | IOM DTM, *South Sudan Baseline Assessment Round 16* y rondas anteriores | **Directa** citeturn24search3turn10search3 |
| Event Tracking existe públicamente para 2021-2025 y está más orientado a movimientos/eventos | IOM DTM South Sudan annual Event Tracking datasets | **Directa** citeturn11search8turn11search2turn11search3turn11search0turn11search5 |
| Event Tracking no garantiza un censo nacional exhaustivo | IOM DTM, Event Tracking Report #62 y metodología asociada | **Directa** citeturn9search6 |
| OCHA “affected” es assessed/verified to date y puede subcubrir el total | OCHA South Sudan, *Flood Data*, HDX | **Directa** citeturn14search2 |
| 2019-2024 fue un régimen hidrológico excepcional en el Sudd conectado a almacenamiento aguas arriba | Munyejuru et al. (2026), *Lake Victoria to the Sudd Wetland...*, DOI 10.5194/hess-30-5297-2026 | **Directa al régimen hidrológico** citeturn24search0turn24search8 |
| Existen evaluaciones agrícolas FAO/WFP, pero no he verificado un outcome county-year uniforme de pérdida por inundación 2021-2025 | FAO/WFP/CLiMIS CFSAM reports | **Directa a disponibilidad, insuficiente para sustituir outcome** citeturn24search2turn25search3 |

**Afirmaciones del prompt no verificadas o que disputo**

| Afirmación del prompt | Evaluación |
|---|---|
| “MCDWD course files for 2000-2025” | **Disputada si se refiere al archivo histórico oficial actual.** NASA publica MCDWD reprocesado 2003-2025. Los archivos específicos del curso podrían contener otros años, pero eso es **not verified**. citeturn15search0turn15search8 |
| “Recurring = ≥7 de los 22 años 2003-2024” | **Verificada** para la versión actual de NASA. citeturn15search0 |
| “Permanent-water class is not in the files” | **Not verified para los archivos del curso.** El producto estándar sí utiliza y reporta una clase/máscara de agua de referencia. citeturn25search4 |
| Solo h20v08 y h21v08, sin datos al norte de 10°N | **Not verified.** Es una propiedad del subconjunto del curso, no del producto NASA global. |
| 71 de 79 unidades tienen ≥95% de cobertura | **Not verified.** Cálculo geoespacial interno. |
| 5-7% de detecciones 2020-2025 caen en julio-septiembre | **Not verified.** Cálculo interno. Además, no equivale por sí solo a una tasa de censura por nubes. |
| Inundación inusual media ~5.300 → 12.800 km² después de 2019 y duración ≥3 meses 1-5% → 24-31% | Valores exactos **not verified**. El cambio de régimen después de 2019 sí está respaldado externamente. citeturn24search0 |
| Condado explica 71-91% de la varianza, año 0,3-6%, interacción 7-24% | **Not verified.** Cálculo interno. |
| Severidad de Aweil Centre 2-27 km²×dekads y Duk 2.300-8.200 | **Not verified.** Cálculo sobre archivos del curso. |
| Bor South estuvo entre -20% y +25% de su usual en 2022-2024 | **Not verified.** Cálculo interno. |
| R12/R13 no contienen arrival-year × reason en el formato usado | **No verificado con suficiente detalle de esquema** en esta revisión. |
| Tabla exacta de stocks DTM R14/R15/R16 por cohorte | **Not verified por recálculo.** La naturaleza de stock de las rondas sí está verificada públicamente. citeturn24search3 |
| 82% de origins = own county y 15% Unknown en R14 | **Not verified.** Cálculo interno del equipo. |
| DTM: 60 condados con desastre en ≥2 años, 51 en los tres | **Not verified.** Cálculo interno. |
| OCHA: 56 condados observados, 121 county-years, 44 con ≥2 años | **Not verified por recálculo.** La falta de cobertura completa está verificada en la documentación. citeturn14search2 |
| Snapshot OCHA “20 Dec 2024” | **Ambiguo.** El repositorio tiene un fichero fechado en diciembre de 2024, pero los metadatos visibles describen también una fecha de situación anterior. No asumiría la fecha exacta sin inspeccionar el workbook. citeturn14search2 |
| OCHA assessment selection logit p≈0,001 | **Not verified.** Cálculo interno. |
| Exposición OCHA subestimada por muestrear una celda de población por píxel | **Not verified.** Implementación interna. |
| Fisher-z MDE ≈0,23-0,26 DTM y 0,31 OCHA | **Verificado aritméticamente bajo independencia ideal**, pero considero la interpretación como potencia efectiva optimista. |
| UCDP median ≈2 eventos por condado | **Not verified.** Cálculo interno. |
| FEWS NET harvested area no tiene relación within con extensión | **Not verified.** Resultado interno. |
| Bor South está en Bahr el Jebel aguas abajo de Mongalla | La conectividad general Lake Victoria-Bahr el Jebel-Sudd está **verificada**; la formulación geográfica específica Bor South/Mongalla quedó **not verified** en esta revisión. citeturn24search0 |
| En el Lol la lluvia local importa más | **Not verified.** No encontré evidencia suficiente para comparar cuantitativamente drivers locales y aguas arriba en ese tramo. |

**Referencias completas**

Chol, D. M., Paszkowski, A., Wheeler, K. G., Smith-Kroll, S., et al. (2026). *Dynamics of human adaptation to flood risk in the Sudd wetlands, South Sudan*. Regional Environmental Change. DOI: **10.1007/s10113-026-02664-1**. citeturn5view0

Chol, D. M., Hall, J. W., Wheeler, K. G., Bernhofen, M., Di Vittorio, C. A., Strzepek, K. M., et al. (2026). *Geospatial Analysis of Population Exposure to Flooding in the Sudd Region, South Sudan*. Journal of Flood Risk Management, 19(1). DOI: **10.1111/jfr3.70168**. citeturn5view1

Momeni, R., Bircan, T., King, R., & Santos, E. Z. (2024). *Deciphering climate-induced displacement in Somalia: A remote sensing perspective*. PLOS ONE, 19(8), e0304202. DOI: **10.1371/journal.pone.0304202**. citeturn23view0

Freihardt, J. (2025). *Environmental shocks and migration among a climate-vulnerable population in Bangladesh*. Population and Environment, 47, 6. DOI: **10.1007/s11111-025-00478-7**. citeturn7view0

King, B., Yurco, K., Young, K. R., Crews, K. A., Shinn, J. E., & Eisenhart, A. C. (2018). *Livelihood Dynamics Across a Variable Flooding Regime*. Human Ecology, 46, 865-874. DOI: **10.1007/s10745-018-0039-2**. citeturn21view0

Nguyen, H.-M.-T., Hoffmann, R., Foreman, T., Lee, H., Omer, A., Yamazaki, D., & Kim, H. (2026). *Intensifying Flood Extent and Human Displacement Risk Across Africa*. EGU General Assembly 2026. DOI: **10.5194/egusphere-egu26-16224**. citeturn22search1

Kobler, et al. (2026). *River Flood Impact Forecasting to Support Humanitarian Anticipatory Action*. EGU General Assembly 2026. DOI: **10.5194/egusphere-egu26-22105**. citeturn2search0

Kuipers, et al. (2026). *Assessing the Riverine Flood Forecast Skill of GloFAS and Google Flood Hub With Impact Data and Discharge Observations to Support Early Actions in Mali*. Journal of Flood Risk Management. citeturn2search4

Griliches, Z., & Hausman, J. A. (1986). *Errors in variables in panel data*. Journal of Econometrics, 31(1), 93-118. DOI: **10.1016/0304-4076(86)90058-8**. citeturn3search9

Bound, J., Brown, C., & Mathiowetz, N. (2001). *Measurement Error in Survey Data*. Handbook of Econometrics, Vol. 5, 3705-3843. DOI: **10.1016/S1573-4412(01)05012-7**. citeturn3search4

Downs, B., Kettner, A. J., Chapman, B. D., Brakenridge, G. R., O'Brien, A. J., & Zuffada, C. (2023). *Assessing the Relative Performance of GNSS-R Flood Extent Observations: Case Study in South Sudan*. IEEE Transactions on Geoscience and Remote Sensing, 61. DOI: **10.1109/TGRS.2023.3237461**. citeturn25search6

Munyejuru, I., Stephens, E. M., et al. (2026). *Lake Victoria to the Sudd Wetland: flood wave timing, connectivity and wetland buffering across the White Nile*. Hydrology and Earth System Sciences, 30, 5297 ff. DOI: **10.5194/hess-30-5297-2026**. citeturn24search0turn24search8

NASA Earthdata (2026). *NASA Enhances Global Flood Products: Smarter Detection of Flooding, and the Release of a 23-Year Archive*. NASA Earthdata. Describe el archivo MCDWD 2003-2025 y la máscara mensual recurring basada en 2003-2024. citeturn15search0

Slayback, D./NASA Goddard Space Flight Center (2025). *MODIS and VIIRS NRT Global Flood Products User Guide, Revision F*. NASA Earthdata. Producto MCDWD DOI: **10.5067/MODIS/MCDWD_L3.061**. VIIRS NRT DOI: **10.5067/VIIRS/VCDWD_L3_NRT.002**. citeturn25search4turn15search8

Copernicus Emergency Management Service (2021-2026). *Global Flood Monitoring, GFM*. European Commission/JRC. Documentación del procesamiento Sentinel-1, productos, archivo y accesos. citeturn17search2turn17search6

Seewald, M., Pasik, A., Gruber, C., Innerbichler, F., Riffler, M., Reimer, C., Stachl, T., Kidd, R., McCormick, N., & Salamon, P. (2025). *Global Flood Monitoring - Annual Product and Service Quality Assessment Report 2024*. Publications Office of the European Union/JRC. DOI: **10.2760/9738940**. citeturn25search1

International Organization for Migration, DTM South Sudan (2023). *Baseline Assessment Round 14*. IOM Displacement Tracking Matrix. citeturn10search3turn11search13

International Organization for Migration, DTM South Sudan (2024). *Baseline Assessment Round 15*. IOM Displacement Tracking Matrix. citeturn11search11

International Organization for Migration, DTM South Sudan (2025). *Baseline Assessment Round 16*. IOM Displacement Tracking Matrix. Periodo de evaluación diciembre 2024-febrero 2025. citeturn24search3

International Organization for Migration, DTM South Sudan (2021). *Event Tracking Dataset, January-December 2021*. Public dataset. citeturn11search8

International Organization for Migration, DTM South Sudan (2022). *Event Tracking Dataset, January-December 2022*. Public dataset. citeturn11search2

International Organization for Migration, DTM South Sudan (2023). *Event Tracking Dataset, January-December 2023*. Public dataset. citeturn11search3

International Organization for Migration, DTM South Sudan (2024). *Event Tracking Dataset, January-December 2024*. Public dataset. citeturn11search0

International Organization for Migration, DTM South Sudan (2025). *Event Tracking Dataset, January-December 2025*. Public dataset. citeturn11search5

International Organization for Migration, DTM South Sudan (2024). *Event Tracking Report #62*. Metodología de detección y verificación de movimientos. citeturn9search6

United Nations Office for the Coordination of Humanitarian Affairs, OCHA South Sudan (2021-2025). *South Sudan: Flood Data*. Humanitarian Data Exchange. Datos reportados de personas afectadas por inundación por condado y estado; metodología basada en cifras evaluadas y verificadas. citeturn14search2

FAO/WFP (2025). *Special report: 2024 FAO/WFP Crop and Food Security Assessment Mission to the Republic of South Sudan*. FAO. DOI: **10.4060/cd5136en**. citeturn25search3turn25search11

FAO/WFP/CLiMIS South Sudan (2022-2026). *Crop and Food Security Assessment Mission and Crop Production Data Reports*. CLiMIS Data Warehouse. Incluye informes de producción agrícola de 2021, 2022 y años posteriores, incluido el informe 2025 publicado en 2026. citeturn24search2