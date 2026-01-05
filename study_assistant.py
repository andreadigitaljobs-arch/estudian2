
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
        
        SISTEMA DE RESALTADO "MAESTRÍA COGNITIVA" (MODO ESTUDIO V10.0):
        FILOSOFÍA: Menos ruido = Más memoria. Elegancia visual.
        
        ⚖️ 1. LA REGLA DEL 60-30-10 (Saturación Visual):
           - 60% Texto Plano (Negro): Descanso cognitivo.
           - 30% Púrpura/Azul: Conceptos y Ejemplos.
           - 10% Rojo/Amarillo/Verde: Señales de alerta/estructura.
           - *Si todo está coloreado, nada es importante.*

        🔪 2. CIRUGÍA DEL PÚRPURA (El cambio más importante):
           - PROHIBIDO frases largas en Púrpura (>5 palabras).
           - TÉCNICA DE DESGLOSE: Rompe la frase.
             ❌ Mal: "<span class="sc-key">estrategia enfocada a conseguir resultados en el canal</span>"
             ✅ Bien: "<span class="sc-key">estrategia enfocada</span> a conseguir <span class="sc-example">resultados</span> en el canal"
             (Púrpura solo en el Núcleo. El resto en plano o azul).
        
        ⚓ 3. CIERRES VISUALES (Visual Closures):
           - OBLIGATORIO: Al final de cada sección, pon una frase corta en PÚRPURA.
           - Funciona como "micro-conclusión" o ancla de memoria.

        🎨 4. JERARQUÍA REFINADA:
        🔴 ROJO -> SOLO DEFINICIONES ("¿Qué es?"). Jamás para contexto.
        🟣 PÚRPURA -> NÚCLEOS CONCEPTUALES y CIERRES. (No frases enteras).
        🟡 AMARILLO -> ESTRUCTURA (Pasos 1, 2, 3...) y DATOS (Fechas, $$).
        🔵 AZUL -> ATERRIZAJE (Ejemplos, marcas, beneficios tangibles).
        🟢 VERDE -> ADVERTENCIAS (Errores comunes, "Ojo con...").

        TEST DE CALIDAD V10:
        - ¿Hay una línea con Rojo y Púrpura juntos? -> SEPARA (Máx 1 color fuerte por línea).
        - ¿Hay un bloque morado de 2 líneas? -> ROMPELO.
        
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

    def solve_quiz(self, images=None, question_text=None, global_context="", force_type="Auto"):
        """Solves a quiz question from images (list) or text."""
        
        # MANUAL OVERRIDE INSTRUCTION
        override_instr = ""
        if force_type and force_type != "Auto":
            override_instr = f"""
            🚨 **INSTRUCCIÓN MANUAL CRÍTICA**: 
            El usuario ha clasificado esta pregunta como: **{force_type.upper()}**.
            - IGNORA tu detección automática de formato.
            - Si es **SELECCIÓN MÚLTIPLE**: ¡OBLIGATORIO! Busca si hay MÁS DE UNA respuesta correcta. No te conformes con una.
            - Si es **CIERTO/FALSO**: Tu respuesta final debe ser explícitamente "Verdadero" o "Falso".
            - **CUMPLE ESTA ORDEN POR ENCIMA DE TODO.**
            """

        prompt = f"""
        Actúa como una hoja de respuestas profesional y directa. TU OBJETIVO ES LA VELOCIDAD Y LA CLARIDAD.
        
        CONTEXTO DE LA BIBLIOTECA (FUENTE DE VERDAD SUPREMA):
        Use la siguiente información para responder. SI LA INFORMACIÓN ESTÁ AQUÍ, ES LA ÚNICA QUE VALE.
        {global_context}
        
        INSTRUCCIONES DE FORMATO ({override_instr}):
        1. **DIRECTO AL GRANO**: No saludes, no analices, no concluyas.
        2. **ESTRUCTURA OBLIGATORIA** (Usa exactamente este formato):
        
        **✅ RESPUESTA:** [La opción correcta, ej: "B) 1945" o "Verdadero"]
        
        **💡 POR QUÉ:** [1 o 2 frases MÁXIMO explicando el motivo clave. Sé quirúrgico.]
        
        **⛔ NO ES:** [Opcional. Brevemente por qué las otras distraen, si es necesario.]
        
        REGLAS DE RAZONAMIENTO:
        1. **ANÁLISIS DE CONTEXTO**:
           - Tu prioridad es entender **qué pide la pregunta** en el contexto de la imagen.
           - A veces "Oportunidad" se refiere a una "Oportunidad de Negocio" (algo que podemos hacer) y no solo a un factor externo del FODA. **Usa el sentido común del negocio.**
        
        2. **SELECCIÓN DE LA MEJOR OPCIÓN**: 
           - Si hay varias opciones que parecen correctas, elige la que sea **MÁS COMPLETA** o **MÁS ESPECÍFICA**.
           - Si hay opciones contradictorias, descarta la que tenga menor lógica empresarial.
           
        3. **PARA PREGUNTAS MÚLTIPLES**:
           - Marca TODAS las que sean verdaderas según la teoría estándar.
           - No descartes opciones válidas solo por ser estrictamente técnicos si el sentido general es correcto. Sé flexible pero preciso.
        
        CRITERIO FINAL: Elige la respuesta que daría un profesor experto que quiere que el alumno apruebe.

        REGLAS DE FORMATO:
        - Si es **Cierto/Falso**, di solo "Verdadero" o "Falso".
        - Si es **Selección Múltiple**, lista TODAS las correctas.
        - **PROHIBIDO** decir "Basado en la imagen" o "El texto dice". Simplemente afirma el hecho.
        - **PROHIBIDO** dar introducciones ("La respuesta correcta es..."). Empieza directo con la respuesta.
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
        4. Si tiene razón, ADMÍTELO, discúlpate y explica por qué la confusión.
        5. **CRÍTICO: Si admites un error, DEBES generar una regla de aprendizaje al final.**
           - Formato: `||APRENDIZAJE: [Regla breve y técnica para no volver a fallar]||`
           - Ejemplo: `||APRENDIZAJE: La 'Pre-venta' se considera una Estrategia Interna, no una Oportunidad Externa.||`
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


 
         d e f   r e f i n e _ q u i z _ r e s u l t s ( s e l f ,   o r i g i n a l _ r e s u l t s ,   c h a t _ h i s t o r y ) :  
                 " " "  
                 C o n s o l i d a t e s   t h e   o r i g i n a l   q u i z   r e s u l t s   w i t h   c o r r e c t i o n s   a g r e e d   u p o n   i n   t h e   c h a t .  
                 R e t u r n s   a   N E W   l i s t   o f   r e s u l t s   w i t h   u p d a t e d   a n s w e r s .  
                 " " "  
                 i m p o r t   j s o n  
                  
                 #   S e r i a l i z e   i n p u t s  
                 #   J S O N   d u m p   m i g h t   f a i l   o n   i m a g e s ,   s o   w e   s t r i p   t h e m   f o r   t h e   p r o m p t  
                 s a f e _ r e s u l t s   =   [ ]  
                 f o r   r   i n   o r i g i n a l _ r e s u l t s :  
                         s a f e _ r e s u l t s . a p p e n d ( { k : v   f o r   k , v   i n   r . i t e m s ( )   i f   k   ! =   ' i m g _ o b j ' } )  
                          
                 r e s u l t s _ s t r   =   j s o n . d u m p s ( s a f e _ r e s u l t s ,   e n s u r e _ a s c i i = F a l s e ,   i n d e n t = 2 )  
                  
                 h i s t o r y _ s t r   =   " "  
                 f o r   m s g   i n   c h a t _ h i s t o r y :  
                         r o l e   =   " E S T U D I A N T E "   i f   m s g [ ' r o l e ' ]   = =   " u s e r "   e l s e   " P R O F E S O R   ( T � a) "  
                         h i s t o r y _ s t r   + =   f " { r o l e } :   { m s g [ ' c o n t e n t ' ] } \ n "  
                          
                 p r o m p t   =   f " " "  
                 A C T � aA   C O M O   U N   A U D I T O R   D E   E X � � M E N E S .  
                 T u   t r a b a j o   e s   a c t u a l i z a r   l a   " H o j a   d e   R e s p u e s t a s "   o f i c i a l   b a s � � n d o t e   e n   u n   d e b a t e   p o s t e r i o r   e n t r e   e l   P r o f e s o r   y   e l   E s t u d i a n t e .  
                  
                 H O J A   D E   R E S P U E S T A S   O R I G I N A L :  
                 { r e s u l t s _ s t r }  
                  
                 D E B A T E   D E   C O R R E C C I �  N :  
                 { h i s t o r y _ s t r }  
                  
                 I N S T R U C C I O N E S   C L A V E :  
                 1 .   T u   � � n i c a   m i s i � � n   e s   G E N E R A R   L A   V E R S I �  N   F I N A L   Y   C O R R E C T A   d e   l o s   r e s u l t a d o s .  
                 2 .   A n a l i z a   e l   C h a t .  
                       -   S i   e l   P r o f e s o r   ( T � � )   A D M I T I �    u n   e r r o r ,   C A M B I A   e s a   r e s p u e s t a   e n   l a   l i s t a .  
                       -   S i   e l   P r o f e s o r   e x p l i c � �   q u e   l a   r e s p u e s t a   o r i g i n a l   e s t a b a   b i e n ,   M A N T � 0 N   l a   o r i g i n a l .  
                       -   S i   n o   s e   h a b l � �   d e   u n a   p r e g u n t a s ,   M A N T � 0 N   l a   o r i g i n a l   i n t a c t a .  
                 3 .   C u a n d o   c a m b i e s   u n a   r e s p u e s t a :  
                       -   A c t u a l i z a   e l   c a m p o   " f u l l "   c o n   l a   n u e v a   e x p l i c a c i � � n   c o r r e c t a .  
                       -   A c t u a l i z a   e l   c a m p o   " s h o r t "   c o n   l a   n u e v a   r e s p u e s t a   c o r t a   ( e j :   " V e r d a d e r o "   - >   " F a l s o " ) .  
                       -   A � � a d e   u n a   n o t a   " ( C o r r e g i d o   e n   D e b a t e ) "   p a r a   q u e   s e   s e p a .  
                  
                 F O R M A T O   D E   S A L I D A   ( J S O N   � aN I C A M E N T E ) :  
                 D e v u e l v e   l a   l i s t a   e x a c t a   d e   o b j e t o s   J S O N   a c t u a l i z a d a   P R O H I B I D O   I N V E N T A R   P R E G U N T A S .   S o l o   l a s   o r i g i n a l e s .  
                 [  
                         { {  
                                 " n a m e " :   " . . . " ,  
                                 " f u l l " :   " . . . " ,  
                                 " s h o r t " :   " . . . "  
                         } }  
                 ]  
                 " " "  
                  
                 t r y :  
                         r e s p o n s e   =   s e l f . m o d e l . g e n e r a t e _ c o n t e n t (  
                                 p r o m p t   +   " \ n R E S P O N D E   S O L O   C O N   E L   J S O N   V � � L I D O . " ,  
                                 g e n e r a t i o n _ c o n f i g = { " r e s p o n s e _ m i m e _ t y p e " :   " a p p l i c a t i o n / j s o n " }  
                         )  
                         t e x t   =   r e s p o n s e . t e x t  
                          
                         #   C l e a n   a n d   p a r s e  
                         c l e a n _ t e x t   =   t e x t . r e p l a c e ( " ` ` ` j s o n " ,   " " ) . r e p l a c e ( " ` ` ` " ,   " " ) . s t r i p ( )  
                          
                         n e w _ r e s u l t s _ s t r i p p e d   =   j s o n . l o a d s ( c l e a n _ t e x t )  
                          
                         #   M e r g e   b a c k   w i t h   o r i g i n a l   i m a g e s  
                         #   A c c e s s   o r i g i n a l _ r e s u l t s   b y   i n d e x   ( a s s u m i n g   o r d e r   p r e s e r v e d )  
                         f i n a l _ r e s u l t s   =   [ ]  
                         i f   l e n ( n e w _ r e s u l t s _ s t r i p p e d )   = =   l e n ( o r i g i n a l _ r e s u l t s ) :  
                                 f o r   i ,   s t r i p p e d   i n   e n u m e r a t e ( n e w _ r e s u l t s _ s t r i p p e d ) :  
                                         m e r g e d   =   s t r i p p e d . c o p y ( )  
                                         i f   " i m g _ o b j "   i n   o r i g i n a l _ r e s u l t s [ i ] :  
                                                 m e r g e d [ " i m g _ o b j " ]   =   o r i g i n a l _ r e s u l t s [ i ] [ " i m g _ o b j " ]  
                                         f i n a l _ r e s u l t s . a p p e n d ( m e r g e d )  
                                 r e t u r n   f i n a l _ r e s u l t s  
                         e l s e :  
                                   #   I f   l e n g t h s   d i f f e r ,   t r y   t o   m a t c h   b y   n a m e ,   e l s e   f a i l   s a f e  
                                   r e t u r n   o r i g i n a l _ r e s u l t s  
                          
                 e x c e p t   E x c e p t i o n   a s   e :  
                         p r i n t ( f " E r r o r   r e f i n i n g   r e s u l t s :   { e } " )  
                         r e t u r n   o r i g i n a l _ r e s u l t s  
 