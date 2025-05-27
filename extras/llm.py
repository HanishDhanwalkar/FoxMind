import ollama
import termcolor

def color(text, color):
    return termcolor.colored(text, color)

def ollama_chat_with_history(model_name="llama3.2", tools=[]):
    messages = []
    print(f"Starting chat with Ollama model: {model_name}")
    print("Type 'exit' or 'q' to end the chat.")

    while True:
        user_input = input(color("You: ", "yellow"))
        if user_input.lower() == 'exit' or user_input.lower() == 'q':
            print("Chat ended.")
            break

        messages.append({'role': 'user', 'content': user_input})

        try:
            response = ollama.chat(model=model_name, messages=messages, tools=tools)
            assistant_reply = response['message']['content']
            print(f"{color('Ollama:', 'green')} {assistant_reply}")

            messages.append({'role': 'assistant', 'content': assistant_reply})

        except ollama.ResponseError as e:
            print(f"Error communicating with Ollama: {e}")
            print("Please ensure Ollama server is running and the model is available.")
            # messages.pop() # remove the last user message if the request failed
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            # messages.pop() # Remove last user message in case of other errors

if __name__ == "__main__":
    # You can change the model here if you have others pulled, e.g., "mistral"
    ollama_chat_with_history()
