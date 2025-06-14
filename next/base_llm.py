import ollama
from termcolor import colored


class OllamaClient:
    """
    A client for interacting with Ollama AI models.

    The following actions are supported:
    - `chat`: Engage in a conversation with the model.
    - `generate`: Generate text based on a prompt.
    """
    def __init__(self, model="llama3.2", stream=True, verbose=True):
        print(colored(f"Starting chat with Ollama model: {colored(model, 'yellow')}", "cyan", attrs=["underline"]))
        self.model = model
        self.client = ollama.Client(
            host='http://localhost:11434',
            headers={'x-some-header': 'some-value'}
        )
        self.stream = stream
        self.system_msg = {"role": "system", "content": ""}
        self.messages = []
        
        if self.system_msg["content"] != "":
            self.messages.append(self.system_msg)
            print("System message set to:", self.system_msg["content"])
        
        self.verbose = verbose

    def send_to_llm(self, prompt):           
        self.messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": self.messages,
            "stream": self.stream,
            "options": {
                "temperature": 0.1,
                "num_predict": 1000,
            }
        }
        response = self.client.chat(
            **payload
        )
        
        full_response = ""
        if self.stream:
            for chunk in response:
                full_response += str(chunk.message.content)
                if self.verbose:
                    print(chunk.message.content, end="")
        
        self.messages.append({"role": "assistant", "content": full_response})
    
    def generate(self, prompt):
        self.send_to_llm(prompt)
        return self.messages[-1]["content"]


if __name__ == "__main__":

    model = "llama3.2"
    # model = "deepseek-r1:7b"
    print(colored(f"Starting chat with Ollama model: {colored(model, 'yellow')}", "cyan", attrs=["underline"]))
    
    _client = OllamaClient(model=model)
    while True:
        user_input = input(colored("You: ", "light_cyan"))
        if user_input.lower() == 'exit' or user_input.lower() == 'q':
            break
        res = _client.generate(user_input)
        print(res)
