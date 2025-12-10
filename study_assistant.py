
import os
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable
from PIL import Image

class StudyAssistant:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        # Using 2.0 Flash as verified available
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def generate_notes(self, transcript_text, global_context=""):
        """Generates progressive notes (3 levels) in JSON format."""
        import json
        
        # --- MOCK ERROR TRIGGER (For User Testing) ---
        if "SIMULAR_ERROR" in transcript_text:
            raise ResourceExhausted("Simulated Quota Error for Testing")
            
        prompt = f"""
        Actúa como un profesor experto. Tu objetivo es crear apuntes en 3 niveles de profundidad (Progresivos) basados en la transcripción.
        
        CONTEXTO GLOBAL (DEFINICIONES OFICIALES):
        {global_context}
        
        INSTRUCCIONES:
        Genera un objeto JSON estricto con las siguientes claves:
        1. "ultracorto": 5 bullets points con lo esencial (Key takeaways).
        2. "intermedio": 10-12 bullets con los conceptos clave explicados brevemente.
        3. "profundo": Un resumen detallado (aprox 1 página) con ejemplos, estructura clara, y conectando conceptos con el Contexto Global si aplica.
        
        FORMATO DE SALIDA (JSON ÚNICAMENTE):
        {{
            "ultracorto": "Markdown string...",
            "intermedio": "Markdown string...",
            "profundo": "Markdown string..."
        }}

        TRANSCRIPCIÓN:
        {transcript_text} 
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Clean response to ensure valid JSON parsing
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
            
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

    def solve_quiz(self, image_path=None, question_text=None, global_context=""):
        """Solves a quiz question from an image or text."""
        
        prompt = f"""
        Analiza esta pregunta de examen.
        
        CONTEXTO OFICIAL (DEFINICIONES):
        {global_context}
        (Si la pregunta se refiere a algo definido aquí, ÚSALO como verdad absoluta).

        1. Identifica la pregunta y las opciones.
        2. Indica cuál es la respuesta correcta usando primero el Contexto Oficial.
        3. Si la respuesta NO está en el contexto, usa tu CONOCIMIENTO GENERAL de experto para deducirla.
        4. Explica brevemente POR QUÉ es la correcta.
        
        Salida:
        **Pregunta:** [Texto detectado/ingresado]
        **Respuesta Correcta:** [Opción]
        **Explicación:** [Razonamiento]
        """
        
        content_parts = [prompt]
        
        if question_text:
            content_parts.append(f"\nTEXTO DE LA PREGUNTA:\n{question_text}")
            
        if image_path:
            img = Image.open(image_path)
            content_parts.append(img)
            
        if len(content_parts) == 1: # Only prompt
            return "Error: Por favor proporciona una imagen o escribe el texto de la pregunta."

        response = self.model.generate_content(content_parts)
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
        
        response = self.model.generate_content(content_parts)
        return response.text

    def extract_text_from_pdf(self, pdf_data, mime_type="application/pdf"):
        """Extracts text from a PDF using Gemini (High Quality OCR/Layout analysis)."""
        prompt = """
        Extract ALL text from this document verbatim. 
        Preserve the structure (headers, lists) using Markdown.
        Do not summarize. Just output the full content.
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
            Da una definición DIRECTA y CONCISA.
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
            Explica la relación entre conceptos si es necesario.
            Sintetiza la respuesta como un experto.
            
            FORMATO:
            **Análisis Sintetizado:**
            [Respuesta detallada y explicada]
            
            **Fuentes Consultadas:**
            - [Archivo 1]
            - [Archivo 2]
            """

        response = self.model.generate_content(prompt)
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
            response = self.model.generate_content(prompt)
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
        Actúa como un PROFESOR UNIVERSITARIO PROACTIVO Y SAPIENTE.
        Tu nombre es "Profe. IA".
        
        CONTEXTO DE CONOCIMIENTO (BIBLIOTECA):
        {context_str}
        (Usa esta información para responder, corregir o proponer ejemplos).
        
        INSTRUCCIONES:
        1. Mantén un tono académico pero cercano.
        2. Si el alumno te saluda, saluda y pregunta qué está estudiando hoy.
        3. Si te envía una tarea, CORRÍGELA con rigor y explica los errores.
        4. Si te hace una pregunta, respóndela conectando conceptos de la biblioteca.
        5. SIEMPRE termina fomentando el pensamiento crítico con una pregunta de vuelta.
        
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
        
        SALIDA ESPERADA (Solo texto, tono amable y servicial):
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
             response = self.model.generate_content(prompt)
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


