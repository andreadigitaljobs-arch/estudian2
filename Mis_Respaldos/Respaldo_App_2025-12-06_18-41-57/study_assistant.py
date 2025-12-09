
import os
import google.generativeai as genai
from PIL import Image

class StudyAssistant:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        # Using 2.0 Flash as verified available
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def generate_notes(self, transcript_text):
        """Generates simple, clear notes from transcript."""
        prompt = f"""
        Actúa como un profesor experto y amable. Tu objetivo es transformar la siguiente transcripción en unos "Apuntes Simples" de la unidad.
        
        INSTRUCCIONES:
        1. Lee todo el texto y extráelo en conceptos clave.
        2. Usa un lenguaje muy sencillo, apto para principiantes. Nada de jerga técnica sin explicar.
        3. SIEMPRE incluye ejemplos de la vida real para aclarar conceptos difíciles.
        4. Estructura el contenido con Títulos, Subtítulos y Viñetas.
        
        FORMATO DE SALIDA:
        # Apuntes de la Unidad: [Título Inferido]
        ## Descripción Breve
        [Resumen de 2 lineas]
        
        ## Contenido Principal
        [Secciones explicadas claramente con ejemplos]
        
        ## Glosario Rápido
        [Lista de 3-5 términos clave definidos simplemente]

        TRANSCRIPCIÓN:
        {transcript_text[:30000]} 
        (Nota: El texto puede estar truncado si es excesivamente largo, prioriza lo enviado)
        """
        # Note: Sending up to 30k chars context for speed/limit safety, though Flash handles much more.
        # We pass the full text usually if the model supports it. 2.0 Flash has huge context.
        # Let's pass full text actually.
        
        full_prompt = prompt.replace(f"{transcript_text[:30000]}", transcript_text)
        
        response = self.model.generate_content(full_prompt)
        return response.text

    def generate_study_guide(self, transcript_text):
        """Generates a structured study guide."""
        prompt = f"""
        Actúa como un estratega de estudio. Crea una "Guía de Estudio" basada en esta transcripción.
        Tu objetivo es que el estudiante apruebe el examen estudiando de forma eficiente.

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

    def solve_quiz(self, image_path):
        """Solves a quiz question from an image."""
        img = Image.open(image_path)
        
        prompt = """
        Analiza esta imagen de una pregunta de examen.
        1. Identifica la pregunta y las opciones.
        2. Indica cuál es la respuesta correcta.
        3. Explica brevemente POR QUÉ es la correcta.
        
        Salida:
        **Pregunta:** [Texto detectado]
        **Respuesta Correcta:** [Opción]
        **Explicación:** [Razonamiento]
        """
        
        response = self.model.generate_content([prompt, img])
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
