
    def refine_quiz_results(self, original_results, chat_history):
        """
        Consolidates the original quiz results with corrections agreed upon in the chat.
        Returns a NEW list of results with updated answers.
        """
        import json
        
        # Serialize inputs
        # JSON dump might fail on images, so we strip them for the prompt
        safe_results = []
        for r in original_results:
            safe_results.append({k:v for k,v in r.items() if k != 'img_obj'})
            
        results_str = json.dumps(safe_results, ensure_ascii=False, indent=2)
        
        history_str = ""
        for msg in chat_history:
            role = "ESTUDIANTE" if msg['role'] == "user" else "PROFESOR (TÚ)"
            history_str += f"{role}: {msg['content']}\n"
            
        prompt = f"""
        ACTÚA COMO UN AUDITOR DE EXÁMENES.
        Tu trabajo es actualizar la "Hoja de Respuestas" oficial basándote en un debate posterior entre el Profesor y el Estudiante.
        
        HOJA DE RESPUESTAS ORIGINAL:
        {results_str}
        
        DEBATE DE CORRECCIÓN:
        {history_str}
        
        INSTRUCCIONES CLAVE:
        1. Tu única misión es GENERAR LA VERSIÓN FINAL Y CORRECTA de los resultados.
        2. Analiza el Chat.
           - Si el Profesor (Tú) ADMITIÓ un error, CAMBIA esa respuesta en la lista.
           - Si el Profesor explicó que la respuesta original estaba bien, MANTÉN la original.
           - Si no se habló de una preguntas, MANTÉN la original intacta.
        3. Cuando cambies una respuesta:
           - Actualiza el campo "full" con la nueva explicación correcta.
           - Actualiza el campo "short" con la nueva respuesta corta (ej: "Verdadero" -> "Falso").
           - Añade una nota "(Corregido en Debate)" para que se sepa.
        
        FORMATO DE SALIDA (JSON ÚNICAMENTE):
        Devuelve la lista exacta de objetos JSON actualizada PROHIBIDO INVENTAR PREGUNTAS. Solo las originales.
        [
            {{
                "name": "...",
                "full": "...",
                "short": "..."
            }}
        ]
        """
        
        try:
            response = self.model.generate_content(
                prompt + "\nRESPONDE SOLO CON EL JSON VÁLIDO.",
                generation_config={"response_mime_type": "application/json"}
            )
            text = response.text
            
            # Clean and parse
            clean_text = text.replace("```json", "").replace("```", "").strip()
            
            new_results_stripped = json.loads(clean_text)
            
            # Merge back with original images
            # Access original_results by index (assuming order preserved)
            final_results = []
            if len(new_results_stripped) == len(original_results):
                for i, stripped in enumerate(new_results_stripped):
                    merged = stripped.copy()
                    if "img_obj" in original_results[i]:
                        merged["img_obj"] = original_results[i]["img_obj"]
                    final_results.append(merged)
                return final_results
            else:
                 # If lengths differ, try to match by name, else fail safe
                 return original_results
            
        except Exception as e:
            print(f"Error refining results: {e}")
            return original_results
