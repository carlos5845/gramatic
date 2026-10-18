# Informe de Validación del Módulo de Clasificación y Explicación Gramatical (Fase 8)

Este informe documenta la alineación, taxonomía pedagógica y generación de explicaciones para aprendices de inglés (L2).

### 1. Resumen de Cobertura de la Taxonomía

| Categoría | Nombre en Español | Nombre en Inglés | Frecuencia en Muestra |
|---|---|---|---|
| `VERB_TENSE` | Tiempos Verbales | Verb Tense & Aspect | 1 |
| `VERB_AGREEMENT` | Concordancia Sujeto-Verbo | Subject-Verb Agreement | 1 |
| `VERB_FORM` | Forma Verbal (Infinitivo / Gerundio / Participio) | Verb Form (Infinitive / Gerund / Participle) | 1 |
| `ARTICLES_DETERMINERS` | Artículos y Determinantes | Articles & Determiners | 3 |
| `PREPOSITIONS` | Preposiciones | Prepositions | 1 |
| `PLURALIZATION_NUMBER` | Pluralización y Número Gramatical | Noun Number & Pluralization | 1 |
| `WORD_ORDER` | Orden de Palabras | Word Order | 1 |
| `SPELLING` | Ortografía (Spelling) | Spelling | 2 |
| `ORTHOGRAPHY_PUNCTUATION` | Puntuación y Mayúsculas | Punctuation & Capitalization | 2 |
| `PRONOUNS` | Pronombres | Pronouns | 1 |
| `ADJECTIVES_ADVERBS` | Adjetivos y Adverbios | Adjectives & Adverbs | 0 |
| `VOCABULARY_LEXICAL` | Vocabulario y Selección Léxica | Vocabulary & Word Choice | 1 |
| `COMPLEX_STYLISTIC` | Reestructuración y Fluidez Estilística | Style & Sentence Restructuring | 0 |
| `UNCERTAIN` | Caso Complejo o Incierto | Uncertain / Context-Dependent Change | 1 |

### 2. Distribución por Nivel de Certeza Pedagógica

- **Alta Certeza (Regla Directa)**: 14 ediciones
- **Media Certeza (Colocaciones/Léxico)**: 1 ediciones
- **Casos Inciertos/Estilísticos (Avisos de Flexibilidad)**: 1 ediciones

### 3. Casos de Prueba Validados con Explicaciones Generadas

#### Foco: `VERB_AGREEMENT`
- **Original**: `She go to school every day by bus .`
- **Corregido**: `She goes to school every day by bus .`
- **Ediciones identificadas**: 1
  - **[#1] Concordancia Sujeto-Verbo** (HIGH confidence):
    - *Cambio*: `go` $\rightarrow$ `goes` (Span: 4:6)
    - *Resumen*: Concordancia entre el sujeto y el verbo (Cambiar 'go' por 'goes').
    - *Regla*: En inglés, el verbo debe coincidir en número (singular o plural) con su sujeto. Para la tercera persona singular (he, she, it), se utiliza 'is', 'was', 'has' o terminación '-s/-es' en presente simple, mientras que para sujetos plurales (they, we, you) se utiliza 'are', 'were', 'have' o la forma base.
    - *Ejemplo*: ❌ *She go happy.* | ✔️ *She goes happy.*

#### Foco: `VERB_TENSE`
- **Original**: `Yesterday I see my old friend at the station .`
- **Corregido**: `Yesterday I saw my old friend at the station .`
- **Ediciones identificadas**: 1
  - **[#1] Tiempos Verbales** (HIGH confidence):
    - *Cambio*: `see` $\rightarrow$ `saw` (Span: 12:15)
    - *Resumen*: Ajuste del tiempo verbal (Cambiar 'see' por 'saw').
    - *Regla*: El tiempo verbal debe corresponder al marco temporal de la oración. Si la acción ocurrió en el pasado y está concluida, se requiere pasado simple (-ed o forma irregular). Si describe hábitos o verdades generales, se emplea el presente simple.
    - *Ejemplo*: ❌ *Yesterday I see to school.* | ✔️ *Yesterday I saw to school.*

#### Foco: `VERB_FORM`
- **Original**: `I am looking forward to hear from you soon .`
- **Corregido**: `I am looking forward to hearing from you soon .`
- **Ediciones identificadas**: 1
  - **[#1] Forma Verbal (Infinitivo / Gerundio / Participio)** (HIGH confidence):
    - *Cambio*: `hear` $\rightarrow$ `hearing` (Span: 24:28)
    - *Resumen*: Uso de la forma verbal adecuada (Cambiar 'hear' por 'hearing').
    - *Regla*: Verifica la estructura verbal requerida: tras verbos modales (can, should, must) se usa el infinitivo sin 'to' (forma base). Tras preposiciones o verbos de preferencia (enjoy, avoid), frecuentemente se requiere gerundio (-ing). Tras 'to' con intención de propósito, se suele emplear infinitivo.
    - *Ejemplo*: ❌ *I decided hear.* | ✔️ *I decided hearing.*

#### Foco: `ARTICLES_DETERMINERS`
- **Original**: `I bought apple and book yesterday .`
- **Corregido**: `I bought an apple and a book yesterday .`
- **Ediciones identificadas**: 2
  - **[#1] Artículos y Determinantes** (HIGH confidence):
    - *Cambio*: `` $\rightarrow$ `an` (Span: 8:8)
    - *Resumen*: Inserción del artículo o determinante necesario 'an'.
    - *Regla*: Los sustantivos contables en singular generalmente requieren un artículo o determinante antes de ellos (a/an/the/my). Se usa 'a' antes de sonido consonante y 'an' antes de sonido vocal.
    - *Ejemplo*: ❌ *I saw apple on table.* | ✔️ *I saw an apple on the table.*
  - **[#2] Artículos y Determinantes** (HIGH confidence):
    - *Cambio*: `` $\rightarrow$ `a` (Span: 18:18)
    - *Resumen*: Inserción del artículo o determinante necesario 'a'.
    - *Regla*: Los sustantivos contables en singular generalmente requieren un artículo o determinante antes de ellos (a/an/the/my). Se usa 'a' antes de sonido consonante y 'an' antes de sonido vocal.
    - *Ejemplo*: ❌ *I saw apple on table.* | ✔️ *I saw an apple on the table.*

#### Foco: `PREPOSITIONS`
- **Original**: `He is very interested on learning English .`
- **Corregido**: `He is very interested in learning English .`
- **Ediciones identificadas**: 1
  - **[#1] Preposiciones** (HIGH confidence):
    - *Cambio*: `on` $\rightarrow$ `in` (Span: 22:24)
    - *Resumen*: Elección de la preposición adecuada (Cambiar 'on' por 'in').
    - *Regla*: Las preposiciones en inglés suelen depender del régimen del verbo o adjetivo que las precede (collocations), o del tipo de complemento (lugar, tiempo, medio). Por ejemplo: 'interested in', 'depend on', 'arrive at/in', 'good at'.
    - *Ejemplo*: ❌ *I am interested on this topic.* | ✔️ *I am interested in this topic.*

#### Foco: `PLURALIZATION_NUMBER`
- **Original**: `There are many car in the street .`
- **Corregido**: `There are many cars in the street .`
- **Ediciones identificadas**: 1
  - **[#1] Pluralización y Número Gramatical** (HIGH confidence):
    - *Cambio*: `car` $\rightarrow$ `cars` (Span: 15:18)
    - *Resumen*: Número gramatical del sustantivo (Cambiar 'car' por 'cars').
    - *Regla*: Asegúrate de que los sustantivos contables estén en plural cuando vayan precedidos de cuantificadores plurales (two, many, several, all) o en singular cuando se refieran a un único elemento. Los sustantivos incontables (information, advice) no llevan '-s'.
    - *Ejemplo*: ❌ *I have two car.* | ✔️ *I have two cars.*

#### Foco: `SPELLING`
- **Original**: `I have just recieved your letter .`
- **Corregido**: `I have just received your letter .`
- **Ediciones identificadas**: 1
  - **[#1] Ortografía (Spelling)** (HIGH confidence):
    - *Cambio*: `recieved` $\rightarrow$ `received` (Span: 12:20)
    - *Resumen*: Corrección ortográfica de la palabra (Cambiar 'recieved' por 'received').
    - *Regla*: La palabra 'recieved' contiene un error de escritura. La grafía correcta en inglés estándar es 'received'.
    - *Ejemplo*: ❌ *recieved* | ✔️ *received*

#### Foco: `ORTHOGRAPHY_PUNCTUATION`
- **Original**: `i went to london last summer .`
- **Corregido**: `I went to London last summer .`
- **Ediciones identificadas**: 2
  - **[#1] Puntuación y Mayúsculas** (HIGH confidence):
    - *Cambio*: `i` $\rightarrow$ `I` (Span: 0:1)
    - *Resumen*: Uso de mayúscula inicial en nombres propios o inicio de oración.
    - *Regla*: En inglés, los nombres propios, días de la semana, meses, nacionalidades e inicios de oración deben comenzar con mayúscula.
    - *Ejemplo*: ❌ *i* | ✔️ *I*
  - **[#2] Puntuación y Mayúsculas** (HIGH confidence):
    - *Cambio*: `london` $\rightarrow$ `London` (Span: 10:16)
    - *Resumen*: Uso de mayúscula inicial en nombres propios o inicio de oración.
    - *Regla*: En inglés, los nombres propios, días de la semana, meses, nacionalidades e inicios de oración deben comenzar con mayúscula.
    - *Ejemplo*: ❌ *london* | ✔️ *London*

#### Foco: `PRONOUNS`
- **Original**: `Her gave me a nice present .`
- **Corregido**: `She gave me a nice present .`
- **Ediciones identificadas**: 1
  - **[#1] Pronombres** (HIGH confidence):
    - *Cambio*: `Her` $\rightarrow$ `She` (Span: 0:3)
    - *Resumen*: Corrección del pronombre (Cambiar 'Her' por 'She').
    - *Regla*: Usa pronombres de sujeto (I, he, she, they) en la posición de agente, pronombres de objeto (me, him, her, them) tras verbos y preposiciones, y pronombres posesivos (my, his, her, their) para indicar pertenencia.
    - *Ejemplo*: ❌ *She told Her.* | ✔️ *She told She.*

#### Foco: `ADJECTIVES_ADVERBS`
- **Original**: `He drives very careful on the road .`
- **Corregido**: `He drives very carefully on the road .`
- **Ediciones identificadas**: 1
  - **[#1] Vocabulario y Selección Léxica** (MEDIUM confidence):
    - *Cambio*: `careful` $\rightarrow$ `carefully` (Span: 15:22)
    - *Resumen*: Selección de vocabulario más preciso (Cambiar 'careful' por 'carefully').
    - *Regla*: El término 'careful' fue sustituido por 'carefully' para alinearse con los patrones léxicos habituales en este contexto.
    - *Ejemplo*: ❌ *careful* | ✔️ *carefully*

#### Foco: `WORD_ORDER`
- **Original**: `I have a car red .`
- **Corregido**: `I have a red car .`
- **Ediciones identificadas**: 1
  - **[#1] Orden de Palabras** (HIGH confidence):
    - *Cambio*: `car red` $\rightarrow$ `red car` (Span: 9:16)
    - *Resumen*: Reordenamiento sintáctico de los términos (Cambiar 'car red' por 'red car').
    - *Regla*: En inglés, el orden estándar es Sujeto + Verbo + Objeto. Los adjetivos atributivos se colocan antes del sustantivo al que modifican (e.g., 'a red car', no 'a car red').
    - *Ejemplo*: ❌ *car red* | ✔️ *red car*

#### Foco: `UNCERTAIN_COMPLEX`
- **Original**: `Because I intend to take examination in Septenber .`
- **Corregido**: `This is because I intend to take an examination in September .`
- **Ediciones identificadas**: 3
  - **[#1] Caso Complejo o Incierto** (UNCERTAIN confidence):
    - *Cambio*: `Because` $\rightarrow$ `This is because` (Span: 0:7)
    - *Resumen*: Ajuste sintáctico o estilístico (Añadir 'This is because').
    - *Regla*: Este cambio corresponde a una reestructuración de la frase o a una elección estilística. En inglés existen múltiples formas de expresar la misma idea; la sugerencia busca mejorar la claridad o naturalidad general.
    - *Ejemplo*: ❌ *Because* | ✔️ *This is because*
  - **[#2] Artículos y Determinantes** (HIGH confidence):
    - *Cambio*: `` $\rightarrow$ `an` (Span: 24:24)
    - *Resumen*: Inserción del artículo o determinante necesario 'an'.
    - *Regla*: Los sustantivos contables en singular generalmente requieren un artículo o determinante antes de ellos (a/an/the/my). Se usa 'a' antes de sonido consonante y 'an' antes de sonido vocal.
    - *Ejemplo*: ❌ *I saw apple on table.* | ✔️ *I saw an apple on the table.*
  - **[#3] Ortografía (Spelling)** (HIGH confidence):
    - *Cambio*: `Septenber` $\rightarrow$ `September` (Span: 40:49)
    - *Resumen*: Corrección ortográfica de la palabra (Cambiar 'Septenber' por 'September').
    - *Regla*: La palabra 'Septenber' contiene un error de escritura. La grafía correcta en inglés estándar es 'September'.
    - *Ejemplo*: ❌ *Septenber* | ✔️ *September*
