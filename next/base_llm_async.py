import asyncio
import ollama

class OllamaClient:
    """
    A client for interacting with Ollama AI models asynchronously.
    Features:
    - Asynchronous streaming: Chat method is implemented as asynchronous and streams content.
    - Custom commands:
        /clear - Clears conversation history.
        /help  - Displays help message.
        /exit  - Terminates the chat.
    """
    
    def __init__(self, model="llama3.2"):
        self.model = model
        self.client = ollama.Client(
            host='http://localhost:11434',
            headers={'x-some-header': 'some-value'}
        )
        
        self.default_options = {
            "temperature": 0.1,
            "num_predict": 1000,
        }
        
        self.messages = []
        

    async def async_send(self, prompt):
        """
        Asynchronously handles the chat call with streaming responses.
        """
        # if prompt.startswith("/"):
        #     if self.process_command(prompt):
        #         return
        
        # else:
        self.messages.append({"role": "user", "content": prompt})
            
        payload = {
            "model": self.model,
            "messages": self.messages,
            "stream": True,  
            "options": self.default_options,
        }
        
        full_response = ""

        response = self.client.chat(**payload)

        # Iterate over the generator    
        for chunk in response:
            _chunk = chunk.message.content
            print(_chunk, end="")
            full_response += str(_chunk)
        
        # print("\n")
        self.messages.append({"role": "assistant", "content": full_response})
        return full_response

    def process_command(self, command):
        exit = False
        
        if command.strip().lower() == "/exit" or command.strip().lower() == "/q":
            exit = True
            print("Exiting the chat. Goodbye!")
            return False
        elif command.strip().lower() == "/clear":
            print("Clearing conversation history.")
            self.messages = []
        elif command.strip().lower() == "/help":
            print("""Available commands:)
    /help  - Show this help message.")
    /clear - Clear the conversation history.") [NOT IMPLEMENTED YET]
    /exit  - Exit the chat application.""")
        else:
            print("Unknown command. Type '/help' for available commands.")
        return exit


async def main():
    from termcolor import colored

    model = "llama3.2"
    # model = "deepseek-r1:7b"
    print(colored(f"Starting chat with Ollama model: {colored(model, 'yellow')}", "cyan", attrs=["underline"]))
    
    _client = OllamaClient(model=model)
    while True:
        # Note: asyncio.to_thread is used here to run the blocking input function in a separate thread.
        try:
            user_input = await asyncio.to_thread(input, "You: ")
        except (EOFError, KeyboardInterrupt):
            print(colored("\nExiting the chat. Goodbye!", "green"))
            break
          
       

        await _client.async_send(user_input)
        print("\n")
        
if __name__ == "__main__":
    asyncio.run(main())
