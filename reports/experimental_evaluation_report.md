# Informe Experimental de Evaluación: Detección (GED) y Corrección Gramatical (GEC)

Este informe consolida los resultados cuantitativos y cualitativos de los modelos desarrollados en las Fases 2 a 7 sobre los corpus FCE v2.1 (BEA19) y REALEC.

### 1. Resumen Comparativo Global

| Tarea | Modelo | Dataset | Precision | Recall | F0.5 Score | F1 Score | Latencia Media |
|---|---|---|---|---|---|---|---|
| **GED (Tokens)** | Baseline (Regresión Logística + spaCy) | FCE Dev | 21.40% | 47.23% | 0.2403 | 0.2946 | ~0.08 ms/token |
| **GED (Tokens)** | BERT (bert-base-cased fine-tuned) | FCE Dev | 73.96% | 39.65% | **0.6305** | **0.5163** | ~0.15 ms/token |
| **GEC (Ediciones)** | Preentrenado (Unbabel/gec-t5_small) | FCE Dev | 47.50% | 30.05% | 0.4256 | 0.3681 | 25.4 ms/orac |
| **GEC (Ediciones)** | GEC Ajustado (T5 Fine-Tuned FCE) | FCE Dev | 49.33% | 33.38% | **0.4503** | **0.3982** | 27.0 ms/orac |
| **GEC (Ediciones)** | Preentrenado (Unbabel/gec-t5_small) | FCE Test | 49.22% | 29.25% | 0.4330 | 0.3669 | 22.9 ms/orac |
| **GEC (Ediciones)** | GEC Ajustado (T5 Fine-Tuned FCE) | FCE Test | 51.30% | 32.88% | **0.4613** | **0.4008** | 22.0 ms/orac |

### 2. Evaluación de Corrección Gramatical (ERRANT M2 en FCE Test)

La métrica estándar de la comunidad GEC es el $F_{0.5}$ sobre ediciones M2 calculadas con ERRANT, donde $\beta=0.5$ otorga el doble de importancia a la precisión que al recall para minimizar la introducción de correcciones erróneas o innecesarias.

| Métrica M2 | GEC Preentrenado | GEC Ajustado (FCE Fine-Tuned) | Mejora Absoluta |
|---|---|---|---|
| **Precision** | 49.22% | 51.30% | +2.08% |
| **Recall** | 29.25% | 32.88% | +3.63% |
| **$F_0.5$ Score** | 0.4330 | **0.4613** | **+0.0283** |
| **$F_1$ Score** | 0.3669 | **0.4008** | **+0.0339** |
| **Preservación Oraciones Limpias** | 86.16% | 87.43% | +1.27% |
| **Ediciones Falsas (Incorrectas)** | 454 | 541 | 87 |

### 3. Análisis Cualitativo de Errores Lingüísticos

Se analizaron cuatro categorías fundamentales de comportamiento del modelo:

#### A. Aciertos (True Positives)
- **Oración original**: `As far as organisation is concerned , adequate number of double rooms with shower or bath have been booked for your group at the Palace hotel located across the main street from the train station .`
  - **Tipo de error**: `M:DET` | **Corrección**: `an`
  - **Salida generada**: `As far as organisation is concerned , an adequate number of double rooms with shower or bath have been booked for your group at the Palace hotel located across the main street from the train station .`

- **Oración original**: `It will start by a speech from the Director of the conference , followed by a meal .`
  - **Tipo de error**: `R:PREP` | **Corrección**: `with`
  - **Salida generada**: `It will start with a speech from the Director of the conference , followed by a meal .`

- **Oración original**: `Of course it allows to be reached everywhere ( even in places you would n't want . )`
  - **Tipo de error**: `M:PRON` | **Corrección**: `us`
  - **Salida generada**: `Of course it allows us to be reached everywhere ( even in places you would n't want . )`

#### B. Falsos Positivos / Modificaciones Innecesarias
- **Oración original**: `Depending on the interests of your students , I would suggest that you visit the internet site of the tourist office : www.neuchatel.ch .`
  - **Edición espuria**: `R:NOUN` (`website`)
  - **Salida generada**: `Depending on the interests of your students , I would suggest that you visit the website of the tourist office : www.neuchatel.ch .`

- **Oración original**: `is very often the first question that you will be asked when answering the phone .`
  - **Edición espuria**: `M:DET` (`This`)
  - **Salida generada**: `This is very often the first question that you will be asked when answering the phone .`

- **Oración original**: `The mobile phone .`
  - **Edición espuria**: `U:DET` (`Mobile`)
  - **Salida generada**: `Mobile phone .`

#### C. Falsos Negativos / Errores Omitidos
- **Oración original**: `I am sad to read about Richard not being at his best .`
  - **Error no corregido**: `R:OTHER` (esperaba: `well`)
  - **Salida generada**: `I am sad to read about Richard not being at his best .`

- **Oración original**: `As far as organisation is concerned , adequate number of double rooms with shower or bath have been booked for your group at the Palace hotel located across the main street from the train station .`
  - **Error no corregido**: `M:DET` (esperaba: `the`)
  - **Salida generada**: `As far as organisation is concerned , an adequate number of double rooms with shower or bath have been booked for your group at the Palace hotel located across the main street from the train station .`

- **Oración original**: `As far as organisation is concerned , adequate number of double rooms with shower or bath have been booked for your group at the Palace hotel located across the main street from the train station .`
  - **Error no corregido**: `R:ORTH` (esperaba: `Hotel`)
  - **Salida generada**: `As far as organisation is concerned , an adequate number of double rooms with shower or bath have been booked for your group at the Palace hotel located across the main street from the train station .`

#### D. Falsas Ediciones / Correcciones Incorrectas
- **Oración original**: `Appart of that , there is no recommendation as to what to wear .`
  - **Esperado**: `Apart from` | **Propuesto por modelo**: `Regarding`
  - **Salida generada**: `Regarding that , there is no recommendation as to what to wear .`

- **Oración original**: `Mobile phone is a marvellous invention but as for cigarettes , we should right on it`
  - **Esperado**: `:` | **Propuesto por modelo**: `.`
  - **Salida generada**: `The mobile phone is a marvellous invention but as for cigarettes , we should right on it .`

- **Oración original**: `Firstly , I would like to tell you , that the group has been booked into Palace Hotel , which locates beside the congress house in the centre .`
  - **Esperado**: `` | **Propuesto por modelo**: `-NONE-`
  - **Salida generada**: `Firstly , I would like to tell you that the group has been booked into the Palace Hotel , which is located beside the congress house in the centre .`

### 4. Eficiencia y Rendimiento Computacional

- **Rendimiento GEC T5**: 45.52 oraciones/segundo.
- **Latencia Media GEC**: 21.97 ms por oración en GPU.
- **Latencia GED BERT**: ~0.15 ms por token.

### 5. Limitaciones Identificadas y Alcance del Estudio

- **Especifidad del Dominio (Learner English)**: Los modelos entrenados sobre FCE v2.1 están optimizados para aprendices de nivel intermedio (B1/B2 CEFR). Su rendimiento puede degradarse en ensayos académicos avanzados o textos informales de redes sociales.
- **Dependencias de Contexto Extendido**: El modelo procesa oraciones individuales de forma aislada, por lo que no puede resolver concordancias o tiempos verbales que dependen del contexto del párrafo completo o del discurso global.
- **Ambigüedad y Variación Estilística**: En oraciones con múltiples formulaciones gramaticalmente válidas, el modelo puede elegir una paráfrasis distinta a la referencia humana, siendo penalizado estrictamente por métricas de coincidencia exacta de edición.

