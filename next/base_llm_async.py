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
        self.messages = []
        self.default_options = {
            "temperature": 0.1,
            "num_predict": 1000,
        }

    async def async_send(self, prompt):
        """
        Asynchronously handles the chat call with streaming responses.
        """
        self.messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": self.messages,
            "stream": True,  
            "options": self.default_options,
        }
        
        full_response = ""

        chat_generator = asyncio.gather(ollama.chat(**payload))
    
        # Iterate over the generator    
        for chunk in chat_generator:
            content_chunk = chunk.get("content", "")
            full_response += content_chunk

            print(content_chunk, end='', flush=True)
            print()  # New line after complete response
            
            self.messages.append({"role": "assistant", "content": full_response})
        return full_response

    def process_command(self, command):
        if command.strip().lower() == "/exit":
            print("Exiting the chat. Goodbye!")
            return False
        elif command.strip().lower() == "/clear":
            print("Clearing conversation history.")
            self.messages = []
        elif command.strip().lower() == "/help":
            print("Available commands:")
            print("  /help  - Show this help message.")
            print("  /clear - Clear the conversation history.")
            print("  /exit  - Exit the chat application.")
        else:
            print("Unknown command. Type '/help' for available commands.")
        return True


async def main():
    from termcolor import colored

    # model = "llama3.2"
    model = "deepseek-r1:7b"
    print(colored(f"Starting chat with Ollama model: {colored(model, 'yellow')}", "cyan", attrs=["underline"]))
    
    _client = OllamaClient(model=model)
    while True:
        # Note: asyncio.to_thread is used here to run the blocking input function in a separate thread.
        # try:
        #     user_input = await asyncio.to_thread(input, "You: ")
        # except (EOFError, KeyboardInterrupt):
        #     print("\nExiting the chat. Goodbye!")
        #     break
        
        user_input = input("YOU: ")
        
        # Check if the input is a command (commands start with "/")
        if user_input.startswith("/"):
            if not _client.process_command(user_input):
                break
            continue

        # Otherwise, handle as a chat prompt.
        # await _client.async_send(user_input)
        await _client.async_send(user_input)
        
if __name__ == "__main__":
    asyncio.run(main())
