
import os
import subprocess
import google.generativeai as genai
import math
import glob
try:
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FFMPEG_EXE = "ffmpeg"

class Transcriber:
    def __init__(self, api_key, model_name="gemini-1.5-flash", cache_breaker="V7"):
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
            subprocess.run([FFMPEG_EXE, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            return False

    def extract_audio(self, video_path, output_audio_path):
        """Extracts audio from video using ffmpeg."""
        if not self.check_ffmpeg():
             # Last ditch effort: try "ffmpeg" literally
             try:
                 subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                 # If we are here, system ffmpeg exists but imageio failed?
                 exe_to_use = "ffmpeg"
             except:
                 raise RuntimeError(f"FFmpeg not found at {FFMPEG_EXE} nor in PATH. System error.")
        else:
             exe_to_use = FFMPEG_EXE
        
        # Audio to MP3
        if not output_audio_path.endswith(".mp3"):
            output_audio_path = os.path.splitext(output_audio_path)[0] + ".mp3"
            
        command = [
            exe_to_use, "-i", video_path, "-vn", 
            "-acodec", "libmp3lame", "-q:a", "4", 
            "-y", output_audio_path
        ]
        
        # Use shell=False for security, but ensure path with spaces works
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_audio_path

    def chunk_audio(self, audio_path, chunk_length_sec=2400): # 40 minutes (Safe for 8k token output)
        """Splits audio into chunks."""
        base_name, ext = os.path.splitext(audio_path)
        if not ext: ext = ".mp3"
        
        # Output pattern matching input extension
        chunk_pattern = f"{base_name}_part%03d{ext}"
        
        # Use our robust FFmpeg path
        if not self.check_ffmpeg():
             # Try system fallback if check failed (unlikely if extract worked)
             exe = "ffmpeg"
        else:
             # We need to re-import or use the global/class var. 
             # Since FFMPEG_EXE is global in this file (see top), just use it.
             exe = FFMPEG_EXE

        command = [
            exe, "-i", audio_path, 
            "-f", "segment", 
            "-segment_time", str(chunk_length_sec), 
            "-c", "copy", 
            "-reset_timestamps", "1",
            "-y", 
            chunk_pattern
        ]
        
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Find the generated files
        # The pattern has %03d, so glob looks like base_name + "_part*" + ext
        search_pattern = f"{base_name}_part*{ext}"
        chunks = sorted(glob.glob(search_pattern))
        
        # V290: Robust Fallback
        if not chunks:
             if os.path.exists(audio_path):
                 return [audio_path]
             raise RuntimeError("Error crítico: FFmpeg no generó fragmentos de audio.")
             
        return chunks

    def transcribe_file(self, audio_file_path, progress_callback=None, is_continuation=False):
        """Transcribes using Gemini 2.0 Flash."""
        # Check standard file size limits if needed, but Gemini API usually handles direct upload via File API
        # actually for 2.0 Flash we should use the File API for audio.
        
        audio_file = genai.upload_file(audio_file_path)
        
        
        if not is_continuation:
            # --- STANDARD HEADER PROMPT (Starts the conversation/text) ---
            prompt = """
            TRANSCRIPCIÓN EDITORIAL EXPERTA (OBLIGATORIO: SOLAMENTE ESPAÑOL):
            Tu tarea es transcribir el audio a ESPAÑOL con ortografía PERFECTA.
            
            👥 DIARIZACIÓN INTELIGENTE (IMPORTANTE):
            - SI ES UN MONÓLOGO: Usa párrafos normales.
            - SI HAY CONVERSACIÓN: Identifica y separa a los hablantes.
              - Usa formato de guión: **Hablante 1:** "..."
              - Si puedes inferir el rol (ej: "Profesor", "Estudiante", "Entrevistador"), USALO como nombre.

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

            ESTRUCTURA OBLIGATORIA (IMPORTANTE):
            1. USA TÍTULOS MARKDOWN (## Título, ### Subtítulo) para separar temas.
            2. Aplica los COLORES HTML solicitados.
            3. Separa párrafos claramente.
            """
        else:
            # --- CONTINUATION PROMPT (Seamless flow) ---
            prompt = """
            TRANSCRIPCIÓN DE CONTINUIDAD (MANTÉN EL FLUJO):
            Esta es la continuación de una grabación larga.
            
            REGLAS DE ORO (V200):
            1. ⛔ PROHIBIDO PONER TÍTULOS o ENCABEZADOS (Ni "Parte 2", ni "## Título").
            2. ✅ EMPIEZA DIRECTAMENTE con la siguiente frase del diálogo.
            3. ✅ MANTÉN LOS PÁRRAFOS Y SALTOS DE LÍNEA: El texto NO debe verse como un bloque gigante.
            4. ✅ RESPETA LA DIARIZACIÓN (**Hablante X:**).
            
            Tu objetivo es continuar la transcripción de manera natural, legible y ordenada.
            """
        
        # STREAMING MODE (V180)
        # response = self.model.generate_content([prompt, audio_file])
        response_stream = self.model.generate_content([prompt, audio_file], stream=True)
        
        final_text = []
        chk = 0
        for chunk in response_stream:
            try:
                # Accessing .text can raise generic errors if blocked
                txt = chunk.text
                
                final_text.append(txt)
                chk += 1
                if progress_callback and chk % 5 == 0:
                     progress_callback(f"📝 Escribiendo Parte {chk}...", 0.5)
            except Exception as e:
                # Safety filter or other error on this chunk
                print(f"Stream chunk error: {e}")
                continue

        full_text = "".join(final_text)
        
        # V205 Fix: Auto-close tags LINE-BY-LINE (Robust Anti-Bleed)
        # Prevents a single unclosed tag from coloring the next 20 minutes.
        lines = full_text.split('\n')
        repaired_lines = []
        for line in lines:
            open_c = line.count("<span")
            close_c = line.count("</span>")
            if open_c > close_c:
                line += "</span>" * (open_c - close_c)
            repaired_lines.append(line)
            
        return "\n".join(repaired_lines)
        
        # Cleanup remote file? usually good practice but let's keep it simple first
        # audio_file.delete() # library might not have delete on object directly depending on version, check docs
        # genai.delete_file(audio_file.name)
        
        return response.text

    def process_video(self, video_path, visual_mode=False, progress_callback=None):
        """V305: Hybrid Cloud Strategy - Chunking with Aggressive Cleanup"""
        
        if visual_mode:
            # Visual mode: Direct upload (no chunking needed, output is structured)
            if progress_callback: progress_callback("🚀 Subiendo video para análisis visual...", 0.1)
            print(f"👁️ Procesando VIDEO MULTIMODAL: {video_path}")
            
            try:
                remote_file = genai.upload_file(video_path)
                
                import time
                dots = 0
                while remote_file.state.name == "PROCESSING":
                    dots = (dots + 1) % 4
                    if progress_callback: progress_callback(f"☁️ Procesando en Nube{'.' * dots}", 0.2)
                    time.sleep(2)
                    remote_file = genai.get_file(remote_file.name)
                
                if remote_file.state.name == "FAILED":
                    raise ValueError(f"Google Cloud Error: {remote_file.state.name}")
                
                if progress_callback: progress_callback("👁️ Generando Análisis Visual...", 0.4)
                
                prompt_visual = """
                ERES UN ANALISTA VISUAL Y EDITOR. (SOLO ESPAÑOL).
                SECCIÓN 1: 🎙️ TRANSCRIPCIÓN DEL AUDIO (FORMATO EDITORIAL)
                - Transcribe el audio con Títulos Markdown (##) y Párrafos.
                - USA CÓDIGO DE COLORES (MODO ESTUDIO):
                  🔴 <span class="sc-base">...</span> -> DEFINICIONES.
                  🟣 <span class="sc-key">...</span> -> IDEAS CLAVE.
                  🟡 <span class="sc-data">...</span> -> DATOS/ESTRUCTURA.
                  🔵 <span class="sc-example">...</span> -> EJEMPLOS.
                  🟢 <span class="sc-note">...</span> -> MATICES.
                
                SECCIÓN 2: 👁️ REGISTRO VISUAL (TIMELINE)
                - [MM:SS] Describe lo que se ve en pantalla (OCR, Diapositivas).
                """
                
                response = self.model.generate_content([prompt_visual, remote_file], request_options={"timeout": 900})
                
                if progress_callback: progress_callback("✅ ¡Listo!", 1.0)
                return response.text
                
            except Exception as e:
                return f"[ERROR VISUAL] {str(e)}"
        
        else:
            # Audio mode: Chunked processing for long videos
            safe_name = "".join([c for c in os.path.basename(video_path) if c.isalnum()])
            audio_path = f"temp_audio_{safe_name}.mp3"
            
            try:
                if progress_callback: progress_callback("🔊 Extrayendo audio...", 0.05)
                print(f"🔊 Procesando AUDIO (Chunked): {video_path}")
                self.extract_audio(video_path, audio_path)
                
                if progress_callback: progress_callback("✂️ Segmentando en partes de 20 min...", 0.1)
                chunks = self.chunk_audio(audio_path, chunk_length_sec=1200)  # 20 mins
                
                full_transcript = []
                total_chunks = len(chunks)
                
                for i, chunk_path in enumerate(chunks):
                    try:
                        if progress_callback:
                            progress_callback(f"🤖 Transcribiendo Parte {i+1} de {total_chunks}...", 0.15 + (0.7 * (i / total_chunks)))
                        
                        # Upload chunk to Gemini
                        chunk_file = genai.upload_file(chunk_path)
                        
                        # Wait for processing
                        import time
                        while chunk_file.state.name == "PROCESSING":
                            time.sleep(1)
                            chunk_file = genai.get_file(chunk_file.name)
                        
                        if chunk_file.state.name == "FAILED":
                            raise ValueError(f"Chunk {i+1} failed to process")
                        
                        # Transcribe with continuation prompt
                        chunk_text = self.transcribe_file_direct(chunk_file, is_continuation=(i > 0))
                        full_transcript.append(chunk_text)
                        
                        # V305: AGGRESSIVE CLEANUP
                        os.remove(chunk_path)
                        import gc
                        gc.collect()
                        
                    except Exception as e:
                        print(f"Error in chunk {i+1}: {e}")
                        full_transcript.append(f"\n\n[ERROR: Parte {i+1} falló - {e}]\n\n")
                        if os.path.exists(chunk_path):
                            os.remove(chunk_path)
                
                if progress_callback: progress_callback("✅ ¡Listo!", 1.0)
                return "\n\n".join(full_transcript)
                
            except Exception as e:
                print(f"Audio Flow Error: {e}")
                return f"[ERROR] {e}"
            finally:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
    
    def transcribe_file_direct(self, remote_file, is_continuation=False):
        """Transcribe an already-uploaded Gemini file"""
        if not is_continuation:
            prompt = """
            TRANSCRIPCIÓN EDITORIAL EXPERTA (OBLIGATORIO: SOLAMENTE ESPAÑOL).
            Tu tarea es transcribir el contenido del archivo a ESPAÑOL con ortografía PERFECTA.
            
            👥 DIARIZACIÓN:
            - Identifica hablantes: **Hablante 1:** "..."
            
            SISTEMA DE RESALTADO (MODO ESTUDIO):
            🔴 <span class="sc-base">...</span> -> DEFINICIONES TIPO EXAMEN.
            🟣 <span class="sc-key">...</span> -> IDEAS ANCLA / CONCLUSIONES.
            🟡 <span class="sc-data">...</span> -> ESTRUCTURA (Pasos) y DATOS.
            🔵 <span class="sc-example">...</span> -> EJEMPLOS.
            🟢 <span class="sc-note">...</span> -> Advertencias/Notas.
            
            ESTRUCTURA:
            - Usa Títulos Markdown (##).
            - Separa párrafos claramente.
            """
        else:
            prompt = """
            TRANSCRIPCIÓN DE CONTINUIDAD (MANTÉN EL FLUJO):
            Esta es la continuación de una grabación larga.
            
            REGLAS:
            1. ⛔ PROHIBIDO PONER TÍTULOS o ENCABEZADOS.
            2. ✅ EMPIEZA DIRECTAMENTE con la siguiente frase del diálogo.
            3. ✅ MANTÉN LOS PÁRRAFOS Y SALTOS DE LÍNEA.
            4. ✅ RESPETA LA DIARIZACIÓN (**Hablante X:**).
            """
        
        response = self.model.generate_content([prompt, remote_file], request_options={"timeout": 600})
        
        # V205 Fix: Auto-close tags
        full_text = response.text
        lines = full_text.split('\n')
        repaired_lines = []
        for line in lines:
            open_c = line.count("<span")
            close_c = line.count("</span>")
            if open_c > close_c:
                line += "</span>" * (open_c - close_c)
            repaired_lines.append(line)
        
        return "\n".join(repaired_lines)


