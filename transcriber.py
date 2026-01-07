
import os
import subprocess
import google.generativeai as genai
import math
import glob

class Transcriber:
    def __init__(self, api_key, model_name="gemini-2.0-flash", cache_breaker="V6"):
        genai.configure(api_key=api_key)
        self.sync_id = f"TRANS_V6_PRECISION_{cache_breaker}"
        
        system_instruction = """
        ERES UN TRANSCRIPTOR EDITORIAL EXPERTO.
        REGLA ABSOLUTA: TU SALIDA DEBE SER EXCLUSIVAMENTE EN ESPAÑOL.
        Incluso si el audio contiene palabras en inglés, tradúcelas o adapta el texto para que el resultado final sea 100% en español con ortografía perfecta.
        Prohibido generar texto en inglés.
        """
        
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction
        )

    def check_ffmpeg(self):
        """Checks if ffmpeg is available."""
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def extract_audio(self, video_path, output_audio_path):
        """Extracts audio from video using ffmpeg."""
        if not self.check_ffmpeg():
            raise RuntimeError("ffmpeg not found. Please install ffmpeg and add it to your PATH.")
        
        # Extract audio to wav (pcm_s16le is standard)
        command = [
            "ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", "-y", output_audio_path
        ]
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_audio_path

    def chunk_audio(self, audio_path, chunk_length_sec=600): # 10 minutes default
        """Splits audio into chunks."""
        base_name, _ = os.path.splitext(audio_path)
        chunk_pattern = f"{base_name}_part%03d.wav"
        
        # Check duration first just to see if splitting is actually needed? 
        # Actually ffmpeg segment handles it gracefully (produces 1 file if short).
        # But to be consistent with previous logic, let's just run the segment command.
        
        command = [
            "ffmpeg", "-i", audio_path, 
            "-f", "segment", 
            "-segment_time", str(chunk_length_sec), 
            "-c", "copy", 
            "-reset_timestamps", "1",
            "-y", 
            chunk_pattern
        ]
        
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Find the generated files
        # The pattern has %03d, so glob looks like base_name + "_part*.wav"
        search_pattern = f"{base_name}_part*.wav"
        chunks = sorted(glob.glob(search_pattern))
        return chunks

    def transcribe_file(self, audio_file_path):
        """Transcribes using Gemini 2.0 Flash."""
        # Check standard file size limits if needed, but Gemini API usually handles direct upload via File API
        # actually for 2.0 Flash we should use the File API for audio.
        
        audio_file = genai.upload_file(audio_file_path)
        
        
        prompt = """
        TRANSCRIPCIÓN EDITORIAL EXPERTA (OBLIGATORIO: SOLAMENTE ESPAÑOL):
        Tu tarea es transcribir el audio a ESPAÑOL con ortografía PERFECTA (tildes, signos ¿ ¡, puntuación). Está PROHIBIDO generar texto en Inglés.

        SISTEMA DE RESALTADO DE UNIDADES MENTALES (MODO ESTUDIO V9.0):
        REGLA PLATINO: NO GRITES VISUALMENTE.

        🧠 1. CONCEPTO DE "UNIDAD MENTAL" (Mental Units):
           - PROHIBIDO resaltar palabras huérfanas ("estrategia", "online").
           - Resalta bloques de significado: "<span class="sc-key">estrategia enfocada a resultados</span>".

        🎨 2. JERARQUÍA ESTRICTA:
        🔴 ROJO (<span class="sc-base">...</span>) -> SOLO DEFINICIONES TIPO EXAMEN ("¿Qué es?").
        🟣 PÚRPURA (<span class="sc-key">...</span>) -> IDEA ANCLA / CONCLUSIÓN (Resumen mental).
        🟡 AMARILLO (<span class="sc-data">...</span>) -> ESTRUCTURA (Paso 1, Fase 2) y DATOS.
        🔵 AZUL (<span class="sc-example">...</span>) -> EJEMPLOS (Marcas, casos).
        🟢 VERDE (<span class="sc-note">...</span>) -> MATICES (Ojo con...).

        TEST DE CALIDAD V9:
        - ¿Hay rojos que no son definiciones? -> BÓRRALOS.
        - ¿Está "Paso 1" en Amarillo? -> SI NO, CORRIGE.



        [ETIQUETA DE CONTROL: (Lógica Semántica V6.0)]

        ESTRUCTURA: Usa títulos Markdown (##, ###) y listas (-).
        """
        
        response = self.model.generate_content([prompt, audio_file])
        
        # Cleanup remote file? usually good practice but let's keep it simple first
        # audio_file.delete() # library might not have delete on object directly depending on version, check docs
        # genai.delete_file(audio_file.name)
        
        return response.text

    def process_video(self, video_path, visual_mode=False, progress_callback=None):
        """Orchestrates the conversion and transcription process."""
        self.visual_mode = visual_mode # Store for prompt usage
        
        # LOGIC FOR VISUAL MODE:
        if visual_mode:
            if progress_callback: progress_callback("🚀 Subiendo video a la Nube de IA (Esto depende de tu internet)...", 0.05)
            print(f"👁️ Procesando VIDEO MULTIMODAL: {video_path}")
            
            # DIRECT VIDEO UPLOAD
            video_file = genai.upload_file(video_path)
            
            # Wait for processing
            import time
            dots = 0
            while video_file.state.name == "PROCESSING":
                dots = (dots + 1) % 4
                if progress_callback: progress_callback(f"🧠 La IA está analizando el video{'.' * dots}", 0.15)
                time.sleep(2)
                video_file = genai.get_file(video_file.name)
                
            if video_file.state.name == "FAILED":
                if progress_callback: progress_callback("❌ Error: Falló el procesamiento del video.", 0.0)
                raise ValueError("Video processing failed in Gemini.")
                
            # Generate
            if progress_callback: progress_callback("👁️ Generando Análisis Visual y Transcripción... (Paciencia)", 0.4)
            
            # Use the specialized prompt directly here to be safe
            prompt_visual = """
            ERES UN ANALISTA VISUAL Y EDITOR. (SOLO ESPAÑOL).
            
            TU MISION: Transcribir el audio Y DESCRIBIR LO QUE SE VE EN PANTALLA.
            
            REGLAS DE FORMATO (HTML):
            Usa las clases <span class="sc-key">...</span> ideas clave, <span class="sc-note">...</span> notas, etc.
            
            👁️ INSTRUCCIONES VISUALES (CRÍTICAS):
            1. DETECTA TAREAS: Si se ve un documento/Word con preguntas/respuestas, TRANSCRIBE EL TEXTO VISUAL EXACTO.
               - Formato: `[👁️ PANTALLA: Se ve la pregunta "X"... Respuesta visible: "Y"]`
            2. SITES WEB: "Entrando a Canva...", "Clic en botón Crear".
            3. SLIDES: Resume el texto de la diapositiva si no se lee en voz alta.
            
            Sincroniza esto con la transcripción del audio.
            """
            
            response = self.model.generate_content([prompt_visual, video_file], request_options={"timeout": 600})
            
            if progress_callback: progress_callback("✅ ¡Análisis Completado!", 1.0)
            return response.text
            
        else:
            # ORIGINAL AUDIO FLOW (Simplified V170)
            # Use a unique temp name to avoid collisions
            safe_name = "".join([c for c in os.path.basename(video_path) if c.isalnum()])
            audio_path = f"temp_audio_{safe_name}.wav"
            try:
                print(f"🔊 Procesando AUDIO Standard: {video_path}")
                self.extract_audio(video_path, audio_path)
                
                # Gemini 2.0 Flash / 1.5 Pro handles large files via File API.
                # No need to chunk unless > 11 hours.
                return self.transcribe_file(audio_path)
            except Exception as e:
                print(f"Audio Flow Error: {e}")
                return f"[ERROR] No se pudo procesar el audio: {e}"
            finally:
                if os.path.exists(audio_path):
                    try: os.remove(audio_path)
                    except: pass

