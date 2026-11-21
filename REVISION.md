# Revisión de «StudyMaster Studio»

Fecha: 21/11/2026 · Archivo revisado: `original/studymaster_original.txt` (3.355 líneas)
Versión corregida: **`index.html`** (en esta misma carpeta; se abre directamente en el navegador)

---

## 1. Qué era el material

Es **una aplicación web completa en un solo archivo HTML** (HTML + Tailwind CSS por CDN + JavaScript sin frameworks), copiada de la respuesta de otra IA (venía dentro de un bloque ```html```). El alumno **pega sus apuntes en texto**. Un «motor» de reglas escrito en JavaScript (sin inteligencia artificial) detecta temas, definiciones del tipo «Concepto: definición», listas numeradas y cadenas con flechas, y genera 7 pestañas: apuntes y esquema, flashcards 3D, rellenar huecos, preguntas abiertas corregidas por palabras clave, dos juegos y un simulacro tipo test con nota sobre 10. Todo se guarda en el `localStorage` del navegador. No hay servidor, ni cuentas de usuario, ni claves de API.

**Valoración general:** la base está bien hecha para ser un prototipo. La interfaz es cuidada, casi todo el texto se escapa antes de pintarlo y funciona sin conexión a una IA. Pero tenía errores que **regalaban respuestas en el examen**, permitía **inflar los XP** con trucos, **perdía el progreso al recargar** y le faltaban tres cosas clave para tu objetivo: **subir PDF o fotos de apuntes**, **seguimiento del progreso** y una **vista para el profesor**.

---

## 2. Problemas encontrados (por prioridad)

### 🔴 Prioridad alta: afectan al aprendizaje o a la evaluación

| # | Problema | Evidencia |
|---|----------|-----------|
| 1 | **El examen regalaba la respuesta.** La opción correcta repetía el término que aparecía en la pregunta. | Con el texto de demostración: «¿Qué afirmación describe correctamente a **«150 millones de kilómetros»**?» → correcta: «…a **150 millones de kilómetros** del Sol». Lo mismo pasaba con las definiciones del tipo «La X es…». |
| 2 | **Preguntas de examen inventadas.** Si los apuntes no tenían secuencias, se fabricaba una con los 6 primeros conceptos («Orden del temario») y se preguntaba «¿qué etapa va después de X?», aunque ese orden no existiera. | `parseNotesEngine`, bloque «si no hay explícitas, crear una». |
| 3 | **Los pasos de las listas numeradas eran frases enteras.** En el juego de ordenar y en el examen aparecían botones de 100 caracteres, y la pregunta «¿qué va después de "Evaporación: el calor del Sol calienta…"?» ya daba pistas. El título salía como «Fases de 3. FASES DEL CICLO…». | Demostración, bloque 3. |
| 4 | **Conceptos mal detectados.** «Distancia Tierra-Sol: …» no se reconocía porque el guion del término rompía la regla, y acababa como concepto «150 millones de kilómetros». Una frase introductoria larga generaba el concepto basura «Continuamente». Las URL generaban «Https». | Probado con el propio texto de demostración. |
| 5 | **XP que se podían inflar** (o «farmear»), así que la gamificación no medía nada: «Comprobar orden» daba +50 XP cada vez que se pulsaba; el doble clic en el clasificador sumaba varias veces; y «Repetir solo fallos» volvía a dar +150 XP conservando las preguntas ya acertadas. | `checkMethodOrder`, `answerSpeed`, `finishExam`. |
| 6 | **Preguntas abiertas autocorregibles.** Aunque no escribieras nada relevante, salía un botón «Dar por válida mi redacción (+30 XP)», y en «Modo Examen» se podía ver la respuesta modelo antes de contestar. Además, la corrección buscaba subcadenas: «sol» se daba por encontrado dentro de «sólido». | `evaluateOpenQuestion`. |
| 7 | **El progreso se perdía al recargar la página.** Las tarjetas dominadas, las definiciones completadas y los resultados de examen solo vivían en memoria. Solo se guardaban los XP, que sin contexto no sirven. | Variables `masteredCards`, etc. |

### 🟠 Prioridad media: seguridad, privacidad y robustez

| # | Problema |
|---|----------|
| 8 | **Importar un JSON ajeno no era seguro.** El temario importado se cargaba sin validar. Sus `id` se insertaban dentro de atributos `onclick="checkDefinition(${id})"`, de modo que un JSON manipulado (p. ej. compartido entre alumnos) podía **ejecutar código** (XSS). También podía traer «respuestas correctas» falsas. `escapeHtml` no escapaba la comilla simple. |
| 9 | **Google Fonts.** Cargar fuentes desde Google envía la IP de cada alumno a Google. Un tribunal alemán lo consideró contrario al RGPD (LG München, 2022), y con menores conviene evitarlo. Las librerías por CDN no tenían versión fijada ni comprobación de integridad (SRI). |
| 10 | **Errores silenciosos de guardado.** Si el `localStorage` estaba lleno o en modo privado, los datos «se guardaban» en memoria y se perdían sin avisar. |
| 11 | **El editor podía romper la app.** Si al editar una definición se borraba el marcador `{0}`, el hueco desaparecía y «Comprobar» lanzaba un error de JavaScript (`input` nulo). Al borrar todas las tarjetas, la app quedaba en un estado incoherente. Los contadores podían mostrar «5/3» tras borrar ítems. |
| 12 | **Faltaban colores en la paleta.** Se usaban `bio-300/400/950` y `science-300/800/900`, que no estaban definidos. Por ejemplo, el reverso de las flashcards perdía su degradado oscuro. |
| 13 | Barajado sesgado (`sort(() => Math.random() - 0.5)`). El examen salía **siempre en el mismo orden y con las mismas opciones**. No avisaba de preguntas sin responder al corregir. Las preguntas abiertas de secuencias salían mal numeradas (la 14 aparecía como «15.»). Las expresiones regulares no capturaban «70%» ni «15 ºC». |

### 🟡 Huecos funcionales frente a tu objetivo

| Objetivo | Estado original |
|----------|-----------------|
| Subir apuntes en PDF / foto / Word | ❌ Solo `.txt`, `.md`, `.csv`, `.json`. En la práctica los alumnos tienen PDF, fotos del cuaderno y Word. |
| Generar material | ⚠️ Funciona solo si los apuntes siguen un formato concreto. Con prosa libre la calidad baja mucho, porque no hay IA. |
| Evaluar | ⚠️ Test con fallos graves (puntos 1 a 3) y preguntas abiertas autovalidables. |
| Seguimiento del progreso | ❌ Inexistente: se perdía al recargar y no había historial. |
| Repaso inteligente | ❌ Las flashcards iban siempre en el mismo orden, sin repetición espaciada. |
| Vista del profesor | ❌ No existía. El profesor no podía saber nada de sus alumnos. |
| Privacidad / RGPD | ⚠️ Positivo: no hay servidor ni IA externa. Negativo: Google Fonts, sin aviso de privacidad y sin forma de borrar los datos. |
| Accesibilidad | ⚠️ Las tarjetas no se podían usar con teclado y las pestañas no tenían roles ARIA. |

---

## 3. Qué he corregido y mejorado (en `index.html`)

Se mantiene el mismo stack (un único HTML, Tailwind, JavaScript sin frameworks), el diseño y todas las funciones originales. Cada cambio importante va marcado en el código con un comentario `// REVISIÓN:`.

**Subida de apuntes (nuevo)**
- **PDF** con texto (pdf.js). **PDF escaneados y fotos** mediante **OCR local en español** (Tesseract.js; las primeras 15 páginas). **Word `.docx`** (mammoth). Además de `.txt` y `.md`. Se pueden subir **varios archivos a la vez**.
- **Todo se procesa en el navegador del alumno**: los apuntes no salen del dispositivo. Solo se descargan las librerías, con versión fijada e integridad SRI.
- Se recomponen las líneas partidas típicas de los PDF y del OCR, incluidos los guiones de final de línea y los títulos partidos.
- Con OCR, el texto se deja en el cuadro para que el alumno **lo revise antes de generar**.

**Generación y evaluación**
- Examen: el término se **oculta** con «_____» dentro de su propia definición. Ya no se inventan secuencias. Los pasos usan etiquetas cortas («Evaporación») y el detalle completo se ve al pulsar en el diagrama. Opciones sin duplicados. **Barajado real en cada intento.** Aviso si quedan preguntas sin responder.
- Mejor detección: términos con guion, frases introductorias largas, URL, porcentajes y grados.
- Preguntas abiertas: la corrección **tolera variaciones** («evapora» ≈ «evaporación») y respeta los límites de palabra. En **Modo Examen** no hay pistas ni autovalidación, y la respuesta modelo solo aparece tras intentarlo. En práctica, autovalidar da la mitad de XP y **queda marcado como «autovalidada»** para el profesor.
- XP sin trampas: la secuencia suma una sola vez, el doble clic queda bloqueado y repetir fallos no suma XP. El examen solo da XP completo si **mejoras tu mejor nota**.

**Aprendizaje y progreso**
- **Repetición espaciada (sistema Leitner, 5 cajas)** en las flashcards: primero salen las tarjetas que toca repasar hoy y se indican la caja y la fecha del siguiente repaso.
- **Progreso persistente por temario.** Se guarda solo y se recupera al recargar o al reabrir un temario. También se recupera el último temario abierto.
- **Nueva pestaña «📈 Mi Progreso»**: resumen, dominio por bloque (tarjetas, huecos y examen), historial de simulacros, conceptos a repasar (tarjetas falladas y fallos del último examen) y botón **«Descargar informe»** para el profesor. El informe es un JSON **sin los apuntes**, con alias o código de alumno.

**Profesor (nuevo, sin servidor)**
- **Nueva pestaña «👩‍🏫 Profesor»**: explica el flujo (preparar el temario → revisarlo con el editor → exportar el JSON → repartirlo). Permite **cargar a la vez los informes de toda la clase** y muestra una tabla por alumno (tarjetas, huecos, abiertas y cuántas autovalidadas, nº de simulacros, mejor y última nota). También muestra **los bloques con más dificultad de la clase** y permite **exportar a CSV** (separador «;» para Excel en español, protegido contra inyección de fórmulas). Los datos solo se ven en el navegador del profesor y no se guardan.

**Seguridad, privacidad y robustez**
- Validación estricta (`sanitizeDeck`) de todo JSON importado y de los temarios guardados: solo ids numéricos, textos recortados, y las preguntas del test **se regeneran siempre**. `escapeHtml` ahora escapa también `'`.
- Se elimina Google Fonts (se usa la fuente del sistema). Se añade `no-referrer` y SRI en Font Awesome y en las librerías.
- Aviso de privacidad visible y botón **«Borrar todos mis datos de este dispositivo»** (derecho de supresión).
- Aviso si no se puede guardar. Editor robusto (restaura los marcadores `{n}`, descarta ítems vacíos y ajusta los contadores).
- Paletas de color completas. Las tarjetas se pueden usar con teclado (Intro/Espacio). Las pestañas tienen roles ARIA y el aviso flotante usa `aria-live`.

---

## 4. Cómo lo he verificado

- `node --check` sobre los dos bloques `<script>` → **sin errores de sintaxis**.
- **Pruebas unitarias** (`tools/unit.js`, 10/10 OK): JSON malicioso, corrección tolerante, recomposición de texto de PDF, ocultación del término, números con unidades y URL.
- **Prueba de extremo a extremo en Chrome sin interfaz** (`tools/e2e.js`, **28/28 OK**, sin errores en la consola). Cubre:
  - demo, flashcards, huecos y preguntas abiertas (modo examen y práctica);
  - anti-farmeo de XP, examen con nota y repetición de fallos, aviso de preguntas sin responder;
  - «Mi Progreso», descarga del informe, **recarga de la página conservando temario y progreso**;
  - vista profesor con el informe cargado, editor;
  - **importación de un JSON malicioso sin que se ejecute código**;
  - **subida real de un .docx, de un PDF y de una foto (OCR)**, y borrado total de datos.
- Comparativa con el texto de demostración: preguntas de examen que delataban la respuesta **3 → 0**; conceptos basura **2 → 0**.

Para repetir las pruebas: `cd tools && npm i puppeteer-core@23`. Después, desde la carpeta `app-apuntes/`, `python3 -m http.server 8765 &`, y de nuevo en `tools/`, `node unit.js && node e2e.js`.

### Lo que NO he podido verificar
- **Apuntes reales de tus alumnos.** Las pruebas usan textos bien estructurados. Con prosa libre, esquemas raros o apuntes de matemáticas (fórmulas), la calidad del motor de reglas seguirá siendo limitada.
- **OCR de letra manuscrita.** Tesseract funciona bien con texto impreso o fotos nítidas, pero **reconoce mal la letra a mano**. Para fotos del cuaderno haría falta una IA con visión (ver decisiones).
- Navegadores móviles (Safari en iPhone o iPad, tabletas Android). Solo he probado Chrome de escritorio.
- PDF muy grandes (más de 80 páginas) en ordenadores modestos, y el funcionamiento abriendo el archivo con doble clic (`file://`) en vez de servirlo desde una web. Lo he probado servido por HTTP.
- No es asesoramiento legal. La parte de RGPD es orientativa y conviene consultarla con el delegado de protección de datos de tu centro o consejería.

---

## 5. Decisiones que te tocan a ti

1. **¿Quieres una IA de verdad?** Es el salto de calidad más grande: resúmenes, preguntas mejores a partir de prosa libre, corrección de respuestas abiertas con explicación y lectura de letra manuscrita. Implica:
   - **Un pequeño servidor** que guarde la clave de API. **Nunca debe ir dentro del HTML**, porque cualquiera podría copiarla y gastar a tu cargo.
   - **Elegir proveedor** (OpenAI, Google Gemini, Anthropic, Mistral u otro) con contrato de encargado de tratamiento, servidores en la UE y sin uso de los datos para entrenar.
   - **Coste por uso** y **autorización del centro y de las familias** si los alumnos son menores de 14 años (en España, edad del consentimiento digital según la LOPDGDD).
   - Alternativa intermedia: que solo **tú** uses la IA para preparar el temario y repartas el JSON ya revisado. Así los alumnos no envían nada a ninguna IA.
2. **¿Login para alumnos?** Hoy no hay cuentas: cada alumno tiene sus datos en su navegador y te envía un archivo. Si quieres ver el progreso automáticamente y que no se pueda manipular, hacen falta cuentas y una base de datos. Lo ideal es usar las del centro (Google Workspace for Education o Microsoft 365 con inicio de sesión del centro), lo que implica más trabajo y más obligaciones RGPD.
3. **¿Dónde alojarla?** Tal como está es un archivo estático: puede ir en el Moodle o Aula Virtual del centro, en Google Sites (como enlace), GitHub Pages, Netlify, etc., o repartirse como archivo. Si añades IA o login, necesitarás un alojamiento con servidor, preferiblemente en la UE.
4. **Uso de la nota.** Mientras no haya login, úsala como **evaluación formativa**. Un informe JSON se puede editar a mano.
5. **Edad y datos.** Decide qué identificador usarán los alumnos en los informes. Recomiendo un **código** (p. ej. «2ºB-07») en vez del nombre completo.

---

## 6. Siguientes pasos recomendados

1. **Pruébala tú con 2 o 3 temas reales** (PDF de tus apuntes, fotos impresas, un Word) y apunta qué conceptos detecta mal. El editor «🛠️ Revisar y Editar Ítems» permite corregirlos antes de repartir.
2. **Piloto con un grupo pequeño**: tú preparas y revisas el temario, exportas el JSON, lo repartes y recoges los informes en la pestaña Profesor.
3. Para producción: **compilar Tailwind** en vez de usar el CDN (que no está pensado para producción) y **alojar las librerías en tu propio dominio**, para no depender de terceros y no exponer IPs. Añadir una política CSP.
4. Si decides usar IA: montar un backend mínimo (p. ej. una función serverless en la UE) con la clave en el servidor, límite de uso por alumno y registro de consentimiento. Empezar por la **corrección de preguntas abiertas** y la **generación de preguntas a partir de prosa**, que es donde el motor de reglas falla más.
5. Más adelante: tipos de pregunta nuevos (verdadero/falso, relacionar columnas), soporte de fórmulas (KaTeX) para ciencias y exámenes con temporizador.

---

## 7. Archivos

```
app-apuntes/
├── index.html                      ← versión corregida y mejorada (la app)
├── REVISION.md                     ← este informe
├── original/
│   ├── studymaster_original.txt    ← lo que te dio la otra IA, sin tocar
│   └── studymaster_original.html   ← el mismo código sin el envoltorio ```html (para comparar)
└── tools/                          ← pruebas automáticas (unit.js, e2e.js, probe.js, fixtures/)
```
