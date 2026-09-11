import subprocess
import json

class LocalLlama:
    """
    Универсален LLM wrapper за локални модели:
    - Ollama
    - llama.cpp
    - HF Transformers (чрез ollama serve)
    """

    def __init__(self, model_name="gemma:9b"):
        self.model_name = model_name

    def ask(self, prompt: str) -> str:
        """
        Изпраща промпт към локален LLM чрез Ollama.
        Връща чист текстов отговор.
        """

        try:
            result = subprocess.run(
                ["ollama", "run", self.model_name],
                input=prompt.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            output = result.stdout.decode("utf-8").strip()
            return output

        except Exception as e:
            print("LLM error:", e)
            return "{}"  # fallback JSON
