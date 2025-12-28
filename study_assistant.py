
import os
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable
from PIL import Image

class StudyAssistant:
    def __init__(self, api_key, model_name="gemini-2.0-flash", cache_breaker="V6"):
        genai.configure(api_key=api_key)
        self.sync_id = f"STUDY_V6_PRECISION_{cache_breaker}"
        
        system_instruction = """
        ERES UN TUTOR ACADÉMICO DE ALTO NIVEL.
        REGLA ABSOLUTA: RESPONDE SIEMPRE EN ESPAÑOL.
        No importa si el texto de entrada está en inglés o en otro idioma, tu salida DEBE ser en español elegante, profesional y con ortografía perfecta.
        Está TERMINANTEMENTE PROHIBIDO hablar o escribir en inglés.
        """
        
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction
        )

    def generate_notes(self, transcript_text, global_context=""):
        """Generates progressive notes (3 levels) in JSON format."""
        import json
        
        prompt = f"""
        Actúa como un profesor experto. Tu objetivo es crear apuntes en 3 niveles de profundidad (Progresivos) basados en la transcripción.
        
        *** REGLA DE ORO: TODA LA RESPUESTA DEBE SER EN ESPAÑOL ***
        
        CONTEXTO GLOBAL (DEFINICIONES OFICIALES):
        {global_context}
        
        INSTRUCCIONES:
        Genera un objeto JSON estricto con las siguientes claves:
        1. "ultracorto": 5 bullets points con lo esencial (Key takeaways).
        2. "intermedio": 10-12 bullets con los conceptos clave explicados brevemente.
        3. "profundo": Un resumen detallado (aprox 1 página).
        
        SISTEMA DE RESALTADO DE UNIDADES MENTALES (MODO ESTUDIO V9.0):
        REGLA PLATINO: NO GRITES VISUALMENTE. Un buen apunte es elegante, no un árbol de navidad.

        🧠 1. CONCEPTO DE "UNIDAD MENTAL" (Mental Units):
           - PROHIBIDO resaltar palabras huérfanas como "estrategia", "online", "marca", "digital" (ruido visual).
           - DEBES resaltar el bloque de significado completo:
             ❌ Mal: "<span class="sc-key">estrategia</span> enfocada a resultados"
             ✅ Bien: "<span class="sc-key">estrategia enfocada a resultados</span>"

        🎨 2. JERARQUÍA ESTRICTA DE COLORES:
        
        🔴 ROJO (<span class="sc-base">...</span>) -> SOLO DEFINICIONES TIPO EXAMEN:
           - Úsalo SOLO si responde a "¿Qué es X?".
           - RESTRICCIÓN: Si es una mención contextual (ej: "usaremos la marca"), NO uses rojo.
        
        🟣 PÚRPURA (<span class="sc-key">...</span>) -> IDEA ANCLA / CONCLUSIÓN:
           - La frase que resume todo el párrafo. Lo que subrayarías para estudiar rápido.
        
        🟡 AMARILLO (<span class="sc-data">...</span>) -> ESTRUCTURA Y DATOS (GPS):
           - OBLIGATORIO para: "Paso 1", "Fase 2", "Primero", "Segundo", "A", "B".
           - También para: Fechas, Nombres propios, Cifras.
        
        🔵 AZUL (<span class="sc-example">...</span>) -> ATERRIZAJE A TIERRA:
           - Ejemplos concretos: "Nike", "Cocacola", "ahorro de dinero".
        
        🟢 VERDE (<span class="sc-note">...</span>) -> MATICES:
           - "No confundir con...", "Importante:".
        
        TEST DE CALIDAD V9:
        - ¿Hay palabras rojas sueltas que no son definiciones? -> ELIMÍNALAS.
        - ¿He resaltado "Paso 1" en amarillo? -> SI NO, ERROR.
        
        FORMATO DE SALIDA (JSON ÚNICAMENTE):
        {
            "ultracorto": "Texto breve con resaltados...",
            "intermedio": "Texto medio con resaltados...",
            "profundo": "Texto largo con resaltados..."
        }
        (IMPORTANTE: Usa comillas dobles para las claves y valores. Escapa las comillas internas con \". NO uses triple comilla \"\"\")

        TRANSCRIPCIÓN:
        {transcript_text} 
        """
        
        try:
            response = self.model.generate_content(
                prompt, 
                generation_config={"response_mime_type": "application/json"}
            )
            text = response.text
            
            # 1. Cleaning
            clean_text = text.replace("```json", "").replace("```", "").strip()
            
            # 2. Extract JSON block if surrounded by text
            import re
            match = re.search(r'\{.*\}', clean_text, re.DOTALL)
            if match:
                clean_text = match.group(0)
            
            # 3. Parsing Strategy
            try:
                return json.loads(clean_text)
            except:
                # Fallback: Try parsing as Python Dictionary (handles triple quotes)
                import ast
                return ast.literal_eval(clean_text)
            
        except ResourceExhausted:
            return {
                "ultracorto": "⚠️ **Límite de IA Excedido**",
                "intermedio": "**¿Por qué veo esto?**\nHas alcanzado el límite gratuito diario de Google Gemini (Quota Exceeded).",
                "profundo": """### 🛑 Límite de Tokens Alcanzado
Google ofrece una capa gratuita generosa, pero limitada.

**Soluciones:**
1.  🕒 **Esperar:** El cupo se reinicia diariamente. Intenta mañana.
2.  💳 **Upgrade:** Configura una tarjeta en Google Cloud Console para permitir "Pay-as-you-go" si necesitas uso intensivo profesional.

*Este mensaje es automático del sistema de protección de costos.*"""
            }
            
        except Exception as e:
            # Fallback for error handling
            return {
                "ultracorto": "Error generando",
                "intermedio": str(e),
                "profundo": response.text if 'response' in locals() else "Error crítico"
            }

    def generate_study_guide(self, transcript_text, global_context=""):
        """Generates a structured study guide."""
        prompt = f"""
        Actúa como un estratega de estudio. Crea una "Guía de Estudio" basada en esta transcripción.
        Tu objetivo es que el estudiante apruebe el examen estudiando de forma eficiente.
        
        *** REGLA DE ORO: RESPONDER ÚNICAMENTE EN ESPAÑOL ***

        CONTEXTO GLOBAL (DEFINICIONES OFICIALES):
        {global_context}
        (Asegúrate de que la estrategia se alinee con estas reglas/definiciones).

        INSTRUCCIONES:
        1. Crea un Mapa de la Unidad (Índice estructurado).
        2. Lista los Conceptos Clave que seguramente saldrán en el examen.
        3. Identifica "Trampas comunes" o errores frecuentes sobre este tema.
        4. Crea un resumen final "En 5 minutos".

        FORMATO DE SALIDA:
        # Guía de Estudio Estratégica
        ## 1. Mapa de la Unidad
        [Esquema jerárquico]
        
        ## 2. Conceptos de Examen
        [Conceptos clave y por qué son importantes]
        
        ## 3. Resumen "Si solo tienes 5 minutos"
        [Puntos bala memorables]

        TRANSCRIPCIÓN:
        {transcript_text}
        """
        response = self.model.generate_content(prompt)
        return response.text

    def generate_didactic_explanation(self, transcript_text, global_context=""):
        """
        Generates a Hybrid Professional explanation using Dynamic Modules.
        Personas: Strategic Analyst, Academic Mentor, Critical Investigator.
        """
        import json
        
        prompt = f"""
        Actúa como un CONSULTOR SÉNIOR y MENTOR ACADÉMICO DE ÉLITE.
        
        TU MISIÓN:
        Analiza la transcripción y genera una explicación "Modular" que combine profundidad técnica con utilidad práctica.
        NO sigas una plantilla fija. Elige los módulos que mejor se adapten al contenido.
        
        TUS 3 PERSONALIDADES (ÚSALAS SEGÚN EL BLOQUE):
        1. 💼 EL ANALISTA: Va al grano. Resume el valor estratégico. (Estilo: Harvard Business Review).
        2. 🎓 EL MENTOR: Explica la estructura y define conceptos. (Estilo: Libro de texto moderno).
        3. 🕵🏻 EL INVESTIGADOR: Cuestiona, compara y advierte. (Estilo: Periodismo de datos).

        CATÁLOGO DE MÓDULOS DISPONIBLES (Elige 3 a 5 según el contenido):
        
        A. 🎯 STRATEGIC_BRIEF (El Analista)
           - Úsalo AL INICIO para la "Gran Idea".
           - Contenido: "La Tesis Central" (1 frase) + "Por qué importa" (Impacto real).
        
        B. 🧠 DEEP_DIVE (El Mentor)
           - Úsalo para CONCEPTOS COMPLEJOS.
           - Contenido: Definición clara + Estructura/Pasos + Ejemplo técnico (SIN analogías infantiles).
        
        C. 🕵🏻 REALITY_CHECK (El Investigador)
           - Úsalo para desmentir mitos, advertir errores o comparar pros/contras.
           - Contenido: "¿Qué suelen hacer mal?" o "Verdad vs Mito".
        
        D. 🛠️ TOOLKIT (Acción)
           - Úsalo para procesos, listas de verificación o pasos a seguir.
           - Contenido: Lista de items accionables.

        CONTEXTO GLOBAL:
        {global_context}
        
        FORMATO JSON ESTRICTO:
        {{
            "modules": [
                {{
                    "type": "STRATEGIC_BRIEF",
                    "title": "Título de Impacto",
                    "content": {{
                        "thesis": "La idea central en una frase potente.",
                        "impact": "Cómo esto cambia el resultado o mejora el negocio/estudio."
                    }}
                }},
                {{
                    "type": "DEEP_DIVE",
                    "title": "Nombre del Concepto Técnico",
                    "content": {{
                        "definition": "Definición formal pero clara.",
                        "explanation": "Explicación estructural del funcionamiento.",
                        "example": "Un caso de uso real (profesional, no infantil)."
                    }}
                }},
                {{
                    "type": "REALITY_CHECK",
                    "title": "Análisis Crítico / Advertencia",
                    "content": {{
                        "question": "¿Cuál es el error común o la duda frecuente?",
                        "insight": "La respuesta contraintuitiva o la advertencia."
                    }}
                }},
                {{
                    "type": "TOOLKIT",
                    "title": "Herramientas / Pasos",
                    "content": {{
                        "intro": "Para aplicar esto, sigue estos pasos:",
                        "steps": ["Paso 1...", "Paso 2...", "Paso 3..."]
                    }}
                }}
            ]
        }}

        TRANSCRIPCIÓN ORIGINAL:
        {transcript_text}
        """
        
        import json
        import time
        from google.api_core.exceptions import ResourceExhausted

        # ... (Prompt is unchanged) ...

        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                return json.loads(response.text)
            
            except ResourceExhausted:
                if attempt < max_retries - 1:
                    time.sleep(2 ** (attempt + 1)) # Backoff: 2s, 4s, 8s
                    continue
                else:
                    return {
                        "modules": [{
                            "type": "REALITY_CHECK",
                            "title": "Tráfico Alto (Error 429)",
                            "content": {"question": "¿Qué pasó?", "insight": "Los servidores de IA están saturados. Intenta de nuevo en 30 segundos."}
                        }]
                    }
                    
            except Exception as e:
                return {
                    "modules": [{
                        "type": "REALITY_CHECK",
                        "title": "Error de Generación",
                        "content": {"question": "¿Qué pasó?", "insight": str(e)}
                    }]
                }

    def generate_micro_guide(self, step_text):
        """Generates a quick how-to guide for a specific checklist step."""
        prompt = f"""
        ACTÚA COMO: Un Consultor de Operaciones Experto.
        TAREA: El usuario debe ejecutar este paso: "{step_text}".
        
        OBJETIVO: Dale una guía ULTRA-RÁPIDA (Micro-Guide) de cómo hacerlo ahora mismo.
        
        FORMATO:
        1. 🛠️ **Herramienta recomendada:** (Nombre de 1 herramienta gratis o común).
        2. 🪜 **3 Pasos de Ejecución:**
           - [Imperativo] ...
           - [Imperativo] ...
           - [Imperativo] ...
        3. 💡 **Pro-Tip:** (Un truco de experto en 1 frase).
        
        TONO: Directo, técnico y accionable. Sin introducciones ni saludos.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception:
            return "No pude generar la guía en este momento. Inténtalo de nuevo."

    def solve_quiz(self, images=None, question_text=None, global_context=""):
        """Solves a quiz question from images (list) or text."""
        
        prompt = f"""
        Analiza esta pregunta de examen con el rigor de un CATEDRÁTICO UNIVERSITARIO.
        
        CONTEXTO DE LA BIBLIOTECA:
        {global_context}
        
        INSTRUCCIONES SUPREMAS:
        1. **RESOLUCIÓN DIRECTA**: Identifica la respuesta correcta de inmediato.
        2. **FUENTE DE VERDAD**: 
           - Busca primero en la Biblioteca.
           - Si NO está ahí, AUTOMÁTICAMENTE usa tu conocimiento enciclopédico mundial.
           - **PROHIBIDO** decir "El texto no lo dice" o "No tengo información".
           - **PROHIBIDO** ser vago (ej: "épocas tempranas"). Sé preciso (ej: "Año 1732").
        3. **EXPLICACIÓN MAGISTRAL (El valor real)**:
           - Tu explicación NO debe ser una simple justificación. Debe ser una **mini-clase**.
           - Aporta contexto histórico, define conceptos clave, menciona autores o fechas si aplica.
           - El estudiante debe aprender el "POR QUÉ" profundo, no solo cuál es la opción correcta.
           - Sé asertivo, profesional y detallista.

        Salida Estructurada:
        **Pregunta:** [Texto completo]
        **Respuesta Correcta:** [Opción exacta]
        **Explicación:** [Párrafo robusto, educativo y detallado que demuestre dominio total del tema]
        """
        
        content_parts = [prompt]
        
        if question_text:
            content_parts.append(f"\nTEXTO DE LA PREGUNTA:\n{question_text}")
            
        if images:
            for img in images:
                content_parts.append(img)
            
        if len(content_parts) == 1: # Only prompt
            return "Error: Por favor proporciona una imagen o escribe el texto de la pregunta."

        
        # Safety catch for None images
        valid_parts = [p for p in content_parts if p is not None]
        
        response = self.model.generate_content(valid_parts + ["\nRecordatorio: Responde siempre en ESPAÑOL."])
        return response.text

    def debate_quiz(self, history, latest_input, quiz_context="", images=None):
        """Interacts with user to debate quiz results, seeing the images."""
        
        # Build conversation string
        conv_str = ""
        for msg in history:
            role = "Estudiante" if msg['role'] == "user" else "Profesor"
            conv_str += f"{role}: {msg['content']}\n"
            
        prompt = f"""
        Actúa como el Profesor del Diplomado. Estás debatiendo los resultados de un examen con el estudiante.
        
        CONTEXTO DEL QUIZ RECIENTE:
        {quiz_context}
        
        HISTORIAL DE CHAT:
        {conv_str}
        
        ESTUDIANTE AHORA: {latest_input}
        
        INSTRUCCIONES:
        1. Tienes acceso visual a las preguntas (Imágenes) si se adjuntaron. Úsalas para verificar tus respuestas.
        2. Sé amable pero riguroso.
        3. Si el estudiante reclama que una respuesta es incorrecta, ANALIZA su argumento vs la Imagen/Texto.
        4. Si tiene razón, ADMÍTELO, discúlpate y explica por qué la confusión (quizás ambigüedad).
        5. Si no tiene razón, explica con pedagogía por qué la respuesta original es la correcta.
        6. Tu objetivo es que APRENDA, no ganar la discusión.
        """
        
        content_parts = [prompt]
        
        # Add Images if available to Provide Context
        if images:
            for img in images:
                content_parts.append(img)
                
        # Safety catch
        valid_parts = [p for p in content_parts if p is not None]
        
        response = self.model.generate_content(valid_parts + ["\nPor favor, responde en ESPAÑOL."])
        return response.text

    def solve_homework(self, task_prompt, context_texts, task_attachment=None):
        """Solves a homework task using specific library context and optional attachment."""
        
        # Merge all context into one block
        full_context = "\n\n".join(context_texts)
        
        text_prompt = f"""
        Actúa como un Asistente Experto del Diplomado.
        Tu misión es ayudar al estudiante a realizar su tarea PERFECTAMENTE, basándote en la metodología oficial del curso.
        
        CONTEXTO OFICIAL (BIBLIOTECA):
        A continuación tienes la información extraída directamente de las clases. USALA COMO TU PRIMERA FUENTE DE VERDAD.
        ------------------------------------------------------------
        {full_context}
        ------------------------------------------------------------
        
        TAREA DEL USUARIO:
        {task_prompt}
        
        (Si hay un archivo adjunto, contiene los detalles específicos o el PDF de la consigna. Úsalo como guía principal para la estructura de la tarea).
        
        INSTRUCCIONES:
        1. Analiza la tarea y busca relaciones directas en el Contexto Oficial.
        2. Si el contexto menciona un método paso a paso, ÚSALO.
        3. No inventes metodologías externas si el curso ya provee una.
        4. Si falta información en el contexto, usa tu conocimiento general pero advierte: "Nota: Esto no estaba en tus apuntes, así que uso conocimiento general".
        5. Se práctico, directo y organizado.
        
        RESPUESTA SOLICITADA:
        [Desarrolla la tarea o da la guía paso a paso basada en el material]
        
        IMPORTANTE:
        - Si la respuesta está en el CONTEXTO OFICIAL, úsalo obligatoriamente.
        - Si el usuario te pide algo que contradice el contexto oficial, explica la discrepancia.
        - No digas "necesito más contexto" si el usuario ya te dio archivos adjuntos o si hay texto en la biblioteca. Haz tu mejor esfuerzo con lo que hay.
        """
        
        content_parts = [text_prompt]
        
        if task_attachment:
            # task_attachment is expected to be a dict: {"mime_type": str, "data": bytes}
            # OR a PIL Image if strictly image.
            # But for PDF/General support via Gemini API, we pass the blob.
            import io
             # If it's a PIL Image (legacy flow), convert to blob? 
             # Let's assume input is raw bytes and mime_type from streamlit.
            
            # Helper to create the part object for google-generativeai
            blob = {
                "mime_type": task_attachment['mime_type'],
                "data": task_attachment['data']
            }
            content_parts.append(blob)
        
        response = self.model.generate_content(content_parts + ["\nIMPORTANTE: Redacta la tarea en ESPAÑOL."])
        return response.text

    def extract_text_from_pdf(self, pdf_data, mime_type="application/pdf"):
        """Extracts text from a PDF using Gemini (High Quality OCR/Layout analysis)."""
        prompt = """
        Extrae TODO el texto de este documento palabra por palabra.
        Preserva la estructura (encabezados, listas) usando Markdown.
        NO resumas. Simplemente entrega el contenido completo en ESPAÑOL.
        """
        
        blob = {"mime_type": mime_type, "data": pdf_data}
        try:
            response = self.model.generate_content([prompt, blob])
            return response.text
        except Exception as e:
            return f"Error reading PDF: {e}"

    def search_knowledge_base(self, query, context, mode="Concepto Rápido"):
        """Searches the knowledge base with specific mode."""
        
        if "Rápido" in mode:
            prompt = f"""
            Actúa como un Buscador Académico de Alta Precisión (Tipo Spotlight).
            
            CONSULTA: "{query}"
            
            CONTEXTO GENERAL (Toda la Bibliografía):
            --------------------------------------------------
            {context}
            --------------------------------------------------
            
            OBJETIVO:
            Da una definición DIRECTA y CONCISA en ESPAÑOL.
            Cita explícitamente el archivo o video de donde sale la información.
            Si no está en el contexto, dilo claramente.
            
            FORMATO:
            **Definición:** [Explicación breve]
            **Fuente:** [Nombre del archivo/video exacto]
            """
        else:
            prompt = f"""
            Actúa como un Investigador Académico Senior.
            
            CONSULTA: "{query}"
            
            CONTEXTO GENERAL (Toda la Bibliografía):
            --------------------------------------------------
            {context}
            --------------------------------------------------
            
            OBJETIVO:
            Realiza un análisis profundo conectando puntos entre diferentes clases/archivos.
            Responde ÚNICAMENTE en ESPAÑOL.
            Explica la relación entre conceptos si es necesario.
            Sintetiza la respuesta como un experto.
            
            FORMATO:
            **Análisis Sintetizado:**
            [Respuesta detallada y explicada]
            
            **Fuentes Consultadas:**
            - [Archivo 1]
            - [Archivo 2]
            """

        response = self.model.generate_content(prompt + "\n\nRespuesta en ESPAÑOL:")
        return response.text

    def solve_argumentative_task(self, task_prompt, context_files=[], global_context=""):
        """Solves complex tasks with a structured 4-part response (JSON)."""
        import json
        
        # Build Context
        context_str = global_context
        if context_files:
            context_str += "\n\n--- DOCUMENTOS ADJUNTOS ---\n"
            for f in context_files:
                context_str += f"[NOMBRE: {f['name']}]\n{f['content']}\n\n"
        
        prompt = f"""
        Actúa como un CONSULTOR EXPERTO y ABOGADO DEL DIABLO. Tu misión es resolver la siguiente tarea académica compleja con un nivel de análisis profundo.
        
        CONTEXTO / FUENTES:
        {context_str}
        
        TAREA DEL USUARIO:
        {task_prompt}
        
        INSTRUCCIONES CLAVE:
        1. Analiza el problema desde múltiples ángulos.
        2. Usa las fuentes proporcionadas explícitamente SI EXISTEN.
        3. Si NO hay fuentes o faltan datos, usa tu CONOCIMIENTO GENERAL EXPERTO para resolverlo, pero aclara que es información externa.
        4. Anticipa críticas o fallos en tu propio razonamiento (Contra-argumento).
        
        FORMATO DE SALIDA (JSON ESTRICTO):
        Debes devolver un JSON con estas 4 claves exactas:
        1. "direct_response": La respuesta final pulida, lista para entregar. (Markdown).
        2. "sources": Lista de archivos/conceptos específicos de la biblioteca que usaste. (Markdown).
        3. "step_by_step": Tu proceso lógico de deducción para llegar a la respuesta. (Markdown).
        4. "counter_argument": Objeciones sólidas a tu propia respuesta (Abogado del diablo). (Markdown).
        
        JSON:
        {{
            "direct_response": "...",
            "sources": "...",
            "step_by_step": "...",
            "counter_argument": "..."
        }}
        """
        
        try:
            # Enforce Spanish in complex tasks
            response = self.model.generate_content(
                prompt + "\nNOTA: El JSON debe estar en ESPAÑOL.",
                generation_config={"response_mime_type": "application/json"}
            )
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except Exception as e:
            return {
                "direct_response": "Error generando respuesta estructurada.",
                "sources": "N/A",
                "step_by_step": str(e),
                "counter_argument": "No se pudo generar."
            }

    def chat_tutor(self, current_user_msg, chat_history=[], context_files=[], global_context=""):
        """
        Conversational Tutor that remembers history and uses context.
        chat_history: List of dicts {'role': 'user'/'model', 'content': '...'}
        """
        
        # Build Context String
        context_str = global_context
        if context_files:
            context_str += "\n\n--- ARCHIVOS ADJUNTOS EN ESTE MENSAJE ---\n"
            for f in context_files:
                context_str += f"[NOMBRE: {f['name']}]\n{f['content']}\n\n"
        
        # Construct System Prompt / History for Gemini
        # We can use the chat API or a single prompt with history injection.
        # For simplicity and control over context, prompt injection is often more robust for "persona" maintenance.
        
        system_instruction = f"""
        ACTÚA COMO UN MENTOR ACADÉMICO DE ÉLITE (NIVEL UNIVERSITARIO/POSTGRADO).
        Tu nombre es "Profe. IA".
        
        CONTEXTO DE CONOCIMIENTO (BIBLIOTECA):
        {context_str}
        
        OBJETIVO:
        No eres un simple asistente que responde preguntas. Eres un CONSULTOR ESTRATÉGICO.
        Tu misión es elevar el nivel del estudiante, estructurar sus ideas y asegurar la excelencia académica.
        
        INSTRUCCIONES "SAGRADAS" DE FORMATO Y ESTILO:
        1. **ESTRUCTURA VISUAL OBLIGATORIA**:
           - Usa `## Títulos de Sección` para organizar tu respuesta.
           - Usa **Negritas** para conceptos clave.
           - Usa "Bullets" para listas. NO hagas párrafos infinitos.
        
        2. **EMOJIS SEMÁNTICOS (Úsalos para guiar la lectura)**:
           - 📌 **Contexto/Definición**: Cuando expliques un concepto.
           - ✅ **Acierto**: Cuando valides algo que el alumno hizo bien.
           - ⚠️ **Crítica/Ojo**: Cuando detectes un error, hueco argumental o mejora necesaria.
           - 💡 **Sugerencia Pro**: Ideas avanzadas que suman valor.
           - 🚀 **Siguiente Paso**: Al final, para mover la acción.

        3. **PENSAMIENTO CRÍTICO (TU VALOR AGREGADO)**:
           - Nunca digas solo "Está bien". Di "Es correcto PORQUE [Razón]".
           - Si el alumno te da un texto pobre, CRITÍCALO constructivamente: "Esto es muy básico. Para nivel diplomado, deberías mencionar [X] y [Y]".
           - Retálo: "¿Estás seguro de que esta Visión es realista?".
        
        4. **PROACTIVIDAD**:
           - SIEMPRE termina tu mensaje con una PROPUESTA CONCRETA.
           - *Ejemplo*: "¿Quieres que redacte 3 ejemplos de Misión basados en esto?", "¿Revisamos la ortografía ahora?".
           - No esperes a que el alumno pregunte qué hacer. Guíalo.

        5. **USO DE FUENTES**:
           - Si usas la biblioteca, cita: "Según el archivo [Nombre]...".
           - Si no hay info, usa tu criterio experto mundial.
            
        6. **IDIOMA OBLIGATORIO**:
           - Responde SIEMPRE en ESPAÑOL DE ESPAÑA/LATAM. Está terminantemente prohibido usar Inglés.
        
        HISTORIAL DE CONVERSACIÓN:
        """
        
        # simple history flattener
        history_str = ""
        for msg in chat_history[-10:]: # Keep last 10 turns context window for efficiency
             role = "ALUMNO" if msg['role'] == "user" else "PROFESOR"
             history_str += f"{role}: {msg['content']}\n"
             
        final_prompt = f"{system_instruction}\n{history_str}\nALUMNO: {current_user_msg}\nPROFESOR:"
        
        try:
            response = self.model.generate_content(final_prompt)
            return response.text
        except Exception as e:
            return f"Error en la clase: {str(e)}"

    def process_bulk_chat(self, raw_text, user_instructions=""):
        # ... (Existing logic kept for fallback or specific manual triggers if needed) ...
        # (Actually, we might repurpose this heavily, but for now lets add the NEW flexible methods)
        pass

    def analyze_import_file(self, raw_text):
        """
        Generates a high-level summary of the file to start the conversation.
        """
        snippet = raw_text[:10000] # Analyze first 10k chars for speed + random sample if needed
        prompt = f"""
        Actúa como un Asistente de Archivos Inteligente.
        Acabas de recibir este archivo de texto (Chat exportado o apuntes).
        
        Tu misión: Dar un resumen brevísimo de qué contiene para preguntarle al usuario qué hacer.
        
        FRAGMENTO (Primeros caracteres):
        {snippet}
        ...
        
        SALIDA ESPERADA (Solo texto en ESPAÑOL, tono amable y servicial):
        "Hola! He leído tu archivo. Parece contener [X, Y, Z]. Veo fechas de [Tema] y apuntes sobre [Tema]. ¿Cómo quieres que lo organice?"
        """
        response = self.model.generate_content(prompt)
        return response.text

    def chat_with_import_file(self, raw_text, user_message, chat_history, available_folders=[]):
        """
        The core logic for the Import Assistant.
        Decides whether to reply to the user OR generate a JSON Action to modify the DB.
        """
        import json
        
        # Build prompt
        folders_str = ", ".join([f['name'] for f in available_folders])
        
        history_text = ""
        for msg in chat_history[-6:]:
            role = "USUARIO" if msg['role'] == "user" else "ASISTENTE"
            history_text += f"{role}: {msg['content']}\n"
        
        snippet = raw_text[:20000] # Context window limit
        
        prompt = f"""
        ERES UN GESTOR DE ARCHIVOS INTELIGENTE (IMPORT ASSISTANT) - MODO SOCRÁTICO Y PROFUNDO.
        Estás conversando con el usuario para organizar este archivo en su Biblioteca.
        
        TU PERSONALIDAD:
        1.  **PROFUNDO Y EXTENSO**: Odias las respuestas cortas. Cuando expliques algo, hazlo con detalle, ejemplos y matices.
        2.  **SOCRÁTICO**: No solo obedezcas. **Haz preguntas** si algo es ambiguo. Ayuda al usuario a pensar mejor.
        3.  **EXPLÍCITO**: Si resumes, no digas "aquí hay datos". Di "El documento detalla X, Y, Z, con énfasis en A y B".
        4.  **ESTRUCTURADO**: Siempre busca la mejor manera de dividir la información en múltiples archivos lógicos.
        
        INSTRUCCIONES CLAVE (MODO EXPERTO):
        1. Eres un arquitecto de información. Tu objetivo es ESTRUCTURAR el contenido.
        2. Puedes ejecutar MÚLTIPLES acciones en una sola respuesta.
        3. SIEMPRE usa formato JSON para acciones (guardar, crear carpetas).
        4. Si el usuario pide "Saca el resumen y las fechas", crea DOS archivos separados en el mismo turno.
        5. **NUNCA seas superficial.** Si generas un resumen, que sea ROBUSTO.
        
        FORMATO DE ACCIÓN (JSON OBLIGATORIO PARA COMANDOS):
        {{
            "thoughts": "Breve razonamiento de qué vas a hacer...",
            "actions": [
                {{
                    "action_type": "save_file",
                    "target_folder": "Nombre Carpeta",
                    "file_name": "Resumen.md",
                    "content": "..."
                }},
                {{
                    "action_type": "save_file",
                    "target_folder": "Nombre Carpeta",
                    "file_name": "Fechas.md",
                    "content": "..."
                }}
            ]
        }}
        
        SI ES SOLO CONVERSACIÓN:
        Simplemente responde con texto plano.
        
        ARCHIVO (Contexto):
        {snippet}
        ...
        
        HISTORIAL:
        {history_text}
        USUARIO: {user_message}
        ASISTENTE (JSON 'actions' o Texto):
        """
        
        try:
             response = self.model.generate_content(prompt + "\nIMPORTANTE: Todo el contenido (texto y JSON) DEBE estar en ESPAÑOL.")
             txt = response.text.strip()
             
             # Robust Parsing: Find first { and last }
             import re
             json_match = re.search(r"\{.*\}", txt, re.DOTALL)
             
             if json_match:
                 try:
                     clean_json = json_match.group(0)
                     return json.loads(clean_json)
                 except:
                     pass # Fallback to text if malformed
             
             return txt
        except Exception as e:
            return f"Error pensando: {e}"


