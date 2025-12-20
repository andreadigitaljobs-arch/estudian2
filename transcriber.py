
import os
import subprocess
import google.generativeai as genai
import math
import glob

class Transcriber:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        # Updated to 2.0 Flash as per user availability
        self.model = genai.GenerativeModel('gemini-2.0-flash')

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
        """Splits audio into chunks using ffmpeg (segment muxer)."""
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
        """Uploads and transcribes a single file using Gemini API."""
        # Check standard file size limits if needed, but Gemini API usually handles direct upload via File API
        # actually for 1.5 Flash we should use the File API for audio.
        
        audio_file = genai.upload_file(audio_file_path)
        
        # Prompt in Spanish
        # Prompt in Spanish focused on formatting
        prompt = """
        Eres un transcriptor experto. Escucha el audio y genera una transcripción exacta, pero bien formateada.
        
        REGLAS DE FORMATO:
        1. NO crees un solo bloque de texto gigante.
        2. Usa PÁRRAFOS claros para separar ideas. Deja una línea en blanco entre párrafos.
        3. Si detectas cambios de tema claros, usa Títulos (Markdown # o ##) para estructurar el texto.
        4. Usa guiones (-) para listas si se enumeran cosas.
        5. Mantén la fidelidad del contenido pero prioriza la legibilidad.
        """
        
        response = self.model.generate_content([prompt, audio_file])
        
        # Cleanup remote file? usually good practice but let's keep it simple first
        # audio_file.delete() # library might not have delete on object directly depending on version, check docs
        # genai.delete_file(audio_file.name)
        
        return response.text

    def process_video(self, video_path, progress_callback=None, chunk_length_sec=600):
        """
        Orchestrates the entire flow for one video using Parallel Processing.
        """
        import concurrent.futures
        
        video_name = os.path.basename(video_path)
        base_name, _ = os.path.splitext(video_name)
        
        if progress_callback: progress_callback(f"Extrayendo audio de {video_name}...", 0.1)
        
        temp_audio_path = f"temp_{base_name}.wav"
        try:
            self.extract_audio(video_path, temp_audio_path)
        except RuntimeError as e:
            return f"Error: {str(e)}"

        if progress_callback: progress_callback(f"Dividiendo audio de {video_name}...", 0.2)
        
        # Chunking
        chunks = self.chunk_audio(temp_audio_path, chunk_length_sec=chunk_length_sec)
        
        total_chunks = len(chunks)
        results = [None] * total_chunks
        completed_count = 0
        
        # Helper to process single chunk and return index to maintain order
        def process_single_chunk(index, chunk_path):
            try:
                text = self.transcribe_file(chunk_path)
                # Cleanup individual chunk immediately
                if chunk_path != temp_audio_path and os.path.exists(chunk_path):
                    os.remove(chunk_path)
                return index, text
            except Exception as e:
                return index, f"[Error en parte {index+1}: {str(e)}]"

        if progress_callback: progress_callback(f"Transcribiendo {total_chunks} partes en paralelo...", 0.3)

        # Execute in parallel with 3 workers to balance speed vs rate limits
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all tasks
            future_to_chunk = {
                executor.submit(process_single_chunk, i, chunk): i 
                for i, chunk in enumerate(chunks)
            }
            
            for future in concurrent.futures.as_completed(future_to_chunk):
                idx, text = future.result()
                results[idx] = text
                completed_count += 1
                
                # Update progress
                if progress_callback:
                    # Progress from 0.3 to 0.95 based on completion
                    current_prog = 0.3 + (0.65 * (completed_count / total_chunks))
                    progress_callback(f"Completado {completed_count}/{total_chunks}...", current_prog)
            
        # Clean up main temp audio
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
            
        final_text = "\n\n".join(results)
        
        output_txt_path = f"{base_name}_transcripcion.txt"
        with open(output_txt_path, "w", encoding="utf-8") as f:
            f.write(final_text)
            
        if progress_callback: progress_callback("¡Listo!", 1.0)
        
        return output_txt_path

