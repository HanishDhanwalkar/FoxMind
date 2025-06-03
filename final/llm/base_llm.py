import ollama

class OllamaClient:
    """
    A client for interacting with Ollama AI models.

    The following actions are supported:
    - `chat`: Engage in a conversation with the model.
    - `generate`: Generate text based on a prompt.
    """
    def __init__(self):
        self.client = ollama.Client(
            host='http://localhost:11434',
            headers={'x-some-header': 'some-value'}
        )
        
        self.messages = []

    def chat(self, prompt):
        self.messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": "llama3.2",
            "messages": self.messages,
            # "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 1000,
            }
        }
        response = self.client.chat(
            **payload
        )
        
        self.messages.append({"role": "assistant", "content": response.message.content})
        return response.message.content

if __name__ == "__main__":
    client = OllamaClient()
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit' or user_input.lower() == 'q':
            break
        res = client.chat(user_input)
        print(res)
