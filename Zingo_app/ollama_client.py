import ollama

class OllamaClient:
    def __init__(self, model_name="Zingo"):  # Changed model name to "jingo"
        self.model = model_name
        # Map "Zingo" to the actual model on Hugging Face
        self.actual_model = "hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:Q4_K_M"
        # Pull the model if not already downloaded
        try:
            ollama.pull(self.actual_model)
        except Exception as e:
            print(f"Error pulling model: {e}")

    def chat(self, message):
        try:
            response = ollama.chat(
                model=self.actual_model,  # Use the actual model name internally
                messages=[
                    {
                        "role": "system",
                        "content": "You are Zingo, a helpful AI agent that can chat and navigate to URLs based on "
                                   "user requests."
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ]
            )
            return response['message']['content']
        except Exception as e:
            return f"Error: {str(e)}"