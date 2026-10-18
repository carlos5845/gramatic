# Informe de Calidad de Datos - Corpus FCE v2.1 GEC (M2 to Pairs)

Este informe resume la conversión de las anotaciones M2 del corpus FCE v2.1 (BEA19) a pares de oraciones originales y corregidas para entrenamiento y evaluación de modelos GEC.

### Resumen General por Split

| Split | Total Oraciones | Pares Generados | Con Cambios | Sin Cambios | % Con Error | Descartados | Total Ediciones |
|---|---|---|---|---|---|---|---|
| **TRAIN** | 28,350 | 28,350 | 17,715 | 10,635 | 62.49% | 0 | 54,687 |
| **DEV** | 2,191 | 2,191 | 1,370 | 821 | 62.53% | 0 | 4,324 |
| **TEST** | 2,695 | 2,695 | 1,792 | 903 | 66.49% | 0 | 5,627 |

### Desglose de Operaciones de Edición

| Split | Inserciones | Eliminaciones | Sustituciones | No-op (Sin error) |
|---|---|---|---|---|
| **TRAIN** | 9,083 | 4,995 | 30,304 | 10,305 |
| **DEV** | 836 | 339 | 2,354 | 795 |
| **TEST** | 1,012 | 542 | 3,206 | 867 |

### Top 10 Tipos de Errores más Frecuentes por Split

#### Split: TRAIN

| Tipo de Error M2 | Frecuencia | Descripción Lingüística |
|---|---|---|
| `noop` | 10,305 | Sin corrección necesaria (oración correcta) |
| `R:OTHER` | 5,000 | Reemplazo: Otro error sintáctico/léxico |
| `R:SPELL` | 4,249 | Reemplazo: Error ortográfico |
| `R:PREP` | 2,801 | Reemplazo: Preposición incorrecta |
| `R:VERB` | 2,505 | Reemplazo: Elección del verbo |
| `M:DET` | 2,502 | Falta: Determinante / Artículo omitido |
| `M:PUNCT` | 2,203 | Falta: Signo de puntuación omitido |
| `R:VERB:TENSE` | 1,996 | Reemplazo: Tiempo verbal incorrecto |
| `R:NOUN` | 1,600 | Reemplazo: Elección del sustantivo |
| `R:NOUN:NUM` | 1,453 | Reemplazo: Número del sustantivo (singular/plural) |

#### Split: DEV

| Tipo de Error M2 | Frecuencia | Descripción Lingüística |
|---|---|---|
| `noop` | 795 | Sin corrección necesaria (oración correcta) |
| `R:OTHER` | 398 | Reemplazo: Otro error sintáctico/léxico |
| `R:SPELL` | 349 | Reemplazo: Error ortográfico |
| `M:DET` | 228 | Falta: Determinante / Artículo omitido |
| `R:PREP` | 206 | Reemplazo: Preposición incorrecta |
| `M:PUNCT` | 204 | Falta: Signo de puntuación omitido |
| `R:VERB` | 175 | Reemplazo: Elección del verbo |
| `R:VERB:TENSE` | 139 | Reemplazo: Tiempo verbal incorrecto |
| `R:NOUN:NUM` | 131 | Reemplazo: Número del sustantivo (singular/plural) |
| `R:NOUN` | 120 | Reemplazo: Elección del sustantivo |

#### Split: TEST

| Tipo de Error M2 | Frecuencia | Descripción Lingüística |
|---|---|---|
| `noop` | 867 | Sin corrección necesaria (oración correcta) |
| `R:OTHER` | 497 | Reemplazo: Otro error sintáctico/léxico |
| `R:SPELL` | 452 | Reemplazo: Error ortográfico |
| `M:DET` | 366 | Falta: Determinante / Artículo omitido |
| `R:PREP` | 255 | Reemplazo: Preposición incorrecta |
| `M:PUNCT` | 248 | Falta: Signo de puntuación omitido |
| `R:ORTH` | 214 | Error gramatical / léxico |
| `UNK` | 211 | Error de tipo desconocido o no clasificado |
| `R:VERB` | 184 | Reemplazo: Elección del verbo |
| `R:NOUN:NUM` | 174 | Reemplazo: Número del sustantivo (singular/plural) |

### Validación y Calidad
- **Ejemplos descartados**: 0 en todos los splits. Todos los índices y ediciones fueron aplicados exitosamente de derecha a izquierda sin solapamiento destructivo.
- **Preservación estructural**: Las oraciones sin errores conservaron exactamente el 100% de sus tokens originales.
- **Manejo de Anotadores**: Anotaciones gestionadas de forma independiente para evitar mezclar correcciones incompatibles.
