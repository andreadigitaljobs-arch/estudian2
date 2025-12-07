# Documentación Técnica: Estudian2

**Versión:** 1.0  
**Fecha:** 07 de Diciembre, 2025  
**Tecnología Principal:** Streamlit (Python) + Google Gemini 2.0 Flash

---

## 1. Resumen General

**Estudian2** es una aplicación web "todo en uno" diseñada para asistir estudiantes de **Diplomados o Cursos Intensivos**. Su función central es convertir material crudo (videos de clases, PDFs de lecturas, fotos de preguntas) en material de estudio estructurado e inteligencia accionable. Actúa como un "Segundo Cerebro" que acumula conocimiento localmente para utilizarlo posteriormente en la resolución de tareas y exámenes.

## 2. Objetivo del Código

El objetivo técnico del script `app.py` y sus módulos auxiliares (`study_assistant.py`, `transcriber.py`) es orquestar un flujo de **Generación Aumentada por Recuperación (RAG) Simplificada**.
En lugar de una base de datos vectorial compleja, el sistema aprovecha la **ventana de contexto masiva de Gemini 1.5/2.0** para inyectar todo el conocimiento del curso (transcripciones + biblioteca) en cada consulta, garantizando respuestas hiper-contextualizadas sin perder detalles.

---

## 3. Estructura de la Aplicación (Pestañas)

La aplicación se divide en una Barra Lateral (Configuración) y 6 Pestañas Funcionales:

1. **📹 Transcriptor:** Ingesta de video a texto.
2. **📝 Apuntes Simples:** Generación de resúmenes estructurados.
3. **🗺️ Guía de Estudio:** Creación de estrategias de estudio para exámenes.
4. **🧠 Ayudante Quiz:** Resolución visual de preguntas (imágenes).
5. **👩‍🏫 Ayudante de Tareas:** Resolución de consignas complejas usando la biblioteca.
6. **📚 Tutoría 1 a 1:** Chatbot conversacional con persistencia y memoria.

---

## 4. Explicación Detallada por Módulo

### Barra Lateral (Configuración & Spotlight)

* **Gestión de Espacios de Trabajo:** Permite crear, seleccionar, renombrar y borrar "Diplomados" (Carpetas raíz en `output/`).
* **Spotlight Académico:** Un motor de búsqueda rápida (`run_spotlight`) que escanea toda la bibliografía cargada para dar definiciones precisas o análisis profundos sobre un término.
* **API Key:** Gestión segura de la clave de Gemini.

### Pestaña 1: Transcriptor

* **Función:** Convierte videos (`.mp4`, `.mov`, etc.) en archivos de texto plano.
* **Lógica (`transcriber.py`):**
    1. Verifica instalación de `ffmpeg`.
    2. Extrae el audio del video (`ffmpeg -vn`).
    3. Divide el audio en fragmentos de 10 minutos (para optimizar subida y evitar timeouts).
    4. Procesa los fragmentos en **paralelo** (ThreadExecutor) enviándolos a Gemini.
    5. Une las respuestas y guarda el `.txt` final en `output/CURSO/transcripts/`.

### Pestaña 2: Apuntes Simples

* **Función:** Transforma una transcripción cruda en un objeto JSON con 3 niveles de profundidad.
* **Datos:** Lee archivos de `transcripts/` y el Contexto Global (`get_global_context`).
* **Salida:** Archivo `.json` en `output/CURSO/notes/`.
* **Niveles Generados:**
  * *Ultracorto:* 5 puntos clave.
  * *Intermedio:* Conceptos explicados.
  * *Profundo:* Resumen detallado de 1 página.

### Pestaña 3: Guía de Estudio

* **Función:** Genera una hoja de ruta estratégica para aprobar un examen sobre un tema.
* **Salida:** Archivo `.txt` en `output/CURSO/guides/`.
* **Estructura:** Mapa jerárquico de la unidad, "Trampas comunes" en exámenes y Resumen "En 5 minutos".

### Pestaña 4: Ayudante Quiz

* **Función:** Resuelve preguntas de opción múltiple a partir de capturas de pantalla.
* **Entrada:** Subida de imágenes o **Pegado desde Portapapeles (`PIL.ImageGrab`)**.
* **Lógica:**
  * Guarda la imagen temporalmente forzando formato PNG (para evitar pérdida de calidad).
  * Envía la imagen + Contexto Global a Gemini.
  * Usa Regex (`re.search`) para extraer la "Respuesta Corta" y mostrarla en una lista resumen.
  * Muestra la explicación detallada en un desplegable.

### Pestaña 5: Ayudante de Tareas & Biblioteca

* **Gestor de Biblioteca:**
  * Botón "Alimentar Memoria": Permite subir PDFs, TXTs o pegar texto.
  * Botón "Importar Chat": Divide logs gigantes de ChatGPT en fragmentos (`process_bulk_chat`) para no exceder límites, y los organiza en archivos Markdown individuales.
  * Gestión de Archivos: Renombrar y Borrar archivos/carpetas.
* **Solucionador de Tareas:**
  * **Modo Normal:** Resuelve la consigna basándose en las Unidades seleccionadas.
  * **Modo Argumentador (Abogado del Diablo):** Genera una respuesta JSON con 4 secciones: Respuesta Directa, Fuentes Citadas, Paso a Paso lógico, y Contra-argumento (crítica a sí mismo).

### Pestaña 6: Tutoría 1 a 1

* **Función:** Chat persistente (`st.session_state['tutor_chat_history']`) que simula un profesor.
* **Contexto:** Inyecta *todo* el contenido de la biblioteca en cada interacción como "System Prompt" o contexto inicial.
* **Adjuntos:** Permite subir archivos temporales al chat para que el profesor los lea en ese momento.

---

## 5. Flujo de Usuario Típico

1. **Inicio:** El usuario abre la app, selecciona su "Diplomado" y pone su API Key.
2. **Alimentación (Ingesta):**
    * Sube los videos de la clase en **Tab 1**.
    * Sube los PDFs del temario o pega apuntes sueltos en **Tab 5 (Biblioteca)**.
3. **Procesamiento:**
    * Espera a que termine la transcripción.
    * Va a **Tab 2** y genera los apuntes de esa clase para repasarlos rápido.
4. **Uso Activo:**
    * *Durante el estudio:* Usa **Tab 3** para hacer su guía de repaso.
    * *Durante la tarea:* Usa **Tab 5**, selecciona la unidad correspondiente y pega la consigna del trabajo práctico para obtener un borrador.
    * *Durante el examen:* Usa **Tab 4**, hace captura de pantalla a la pregunta, pega en la app y obtiene la respuesta explicada.

---

## 6. Funciones Internas Clave (`app.py`)

* `run_migration_check()`: Se ejecuta al inicio. Verifica si existen carpetas antiguas en la raíz y las mueve automáticamente a la estructura ordenada por Cursos.
* `get_global_context()`: **Función Crítica.** Recorre recursivamente todas las carpetas de `library/` y `transcripts/`, lee todos los archivos `.txt` y `.md`, y los concatena en un solo string gigante. Esto constituye el "Cerebro" de la IA.
* `clean_markdown(text)`: Elimina negritas, encabezados y listas para permitir copiar texto limpio al portapapeles.
* `copy_to_clipboard(text)`: Usa el comando del sistema `clip` (Windows) para copiar texto directamente.

---

## 7. Procesamiento de Archivos

* **PDFs:** Se procesan con `StudyAssistant.extract_text_from_pdf`, usando a Gemini como OCR inteligente (no usa librerías python de PDF tradicionales, confía en la visión/texto del modelo para mantener layout).
* **Videos:** Se procesan externamente con `ffmpeg`. No se sube el video a Gemini, solo el audio extraído y fragmentado, para ahorrar ancho de banda y tiempos.
* **Imágenes:** Se procesan con `Pillow` y se envían como objetos blob a la API de Vision de Gemini.

---

## 8. Modelos de IA

* **Modelo Principal:** `gemini-2.0-flash`.
* **Justificación:** Se elige por su:
    1. **Ventana de Contexto:** 1 Millón de tokens (permite leer libros enteros o decenas de transcripciones de una sola vez).
    2. **Velocidad:** Esencial para la experiencia de usuario en tiempo real (Chat/Quiz).
    3. **Multimodalidad:** Nativo para audio (videos) e imágenes (quiz).

---

## 9. Dependencias Externas

Estas librerías deben estar en `requirements.txt`:

* `streamlit`: Framework de UI.
* `google-generativeai`: SDK de Gemini.
* `Pillow`: Procesamiento de imágenes.
* `watchdog` (opcional, suele venir con streamlit): Para recarga en caliente.

**Software del Sistema Requerido:**

* **FFmpeg:** Debe estar instalado en el sistema operativo y accesible desde el PATH para que el Transcriptor funcione.

---

## 10. Limitaciones Actuales

1. **Dependencia de FFmpeg:** Si el usuario no tiene FFmpeg instalado, la pestaña 1 fallará.
2. **Escalabilidad de Contexto:** Aunque Gemini soporta 1M tokens, si la biblioteca crece a cientos de libros, el método actual de "concatenar todo en un string" (`get_global_context`) se volverá lento y costoso. En el futuro requeriría una Base de Datos Vectorial (Embeddings).
3. **Bloqueo de UI:** Las operaciones largas (transcripción) bloquean la interfaz hasta que terminan, aunque se mitiga con barras de progreso.
