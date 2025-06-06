import ollama

class OllamaClient:
    """
    A client for interacting with Ollama AI models.

    The following actions are supported:
    - `chat`: Engage in a conversation with the model.
    - `generate`: Generate text based on a prompt.
    """
    def __init__(self, model="llama3.2"):
        self.model = model
        self.client = ollama.Client(
            host='http://localhost:11434',
            headers={'x-some-header': 'some-value'}
        )
        
        self.messages = []

    def send(self, prompt):
        self.messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
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
    from termcolor import colored

    # model = "llama3.2"
    model = "deepseek-r1:7b"
    print(colored(f"Starting chat with Ollama model: {colored(model, 'yellow')}", "cyan", attrs=["underline"]))
    
    _client = OllamaClient(model=model)
    while True:
        user_input = input(colored("You: ", "light_cyan"))
        if user_input.lower() == 'exit' or user_input.lower() == 'q':
            break
        res = _client.send(user_input)
        print(res)
