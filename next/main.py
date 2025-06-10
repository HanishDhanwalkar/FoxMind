# main.py

import asyncio
from ollama_client import OllamaClient # Import the client class from the other file

async def main():
    """
    Main asynchronous function to demonstrate the OllamaClient.
    """
    # Create an instance of the OllamaClient
    # If your Ollama server is on a different address/port, change base_url
    client = OllamaClient(base_url="http://localhost:11434")
    model = "llama3.2" # e.g., "llama2", "gemma:2b", "phi3"

    try:
        # --- Example 1: Basic text generation ---
        print("--- Example 1: Generating text ---")
        prompt_gen = "Why is the sky blue?"
        print(f"Prompt: '{prompt_gen}' (Model: {model})")

        # Using the generate method
        response_gen = await client.generate(model=model, prompt=prompt_gen)
        if response_gen and "response" in response_gen:
            print("Response:", response_gen["response"].strip())
        elif response_gen and "message" in response_gen and "content" in response_gen["message"]:
             print("Response (from message):", response_gen["message"]["content"].strip())
        else:
            print("No valid response received.")

        print("\n" + "="*40 + "\n")

        # --- Example 2: Chat completion ---
        print("--- Example 2: Chat conversation ---")
        messages_chat = [
            {"role": "user", "content": "What is the capital of France?"},
            {"role": "assistant", "content": "The capital of France is Paris."},
            {"role": "user", "content": "And what about Italy?"}
        ]
        print(f"Chat History: {messages_chat} (Model: {model})")

        # Using the chat method
        response_chat = await client.chat(model=model, messages=messages_chat)
        if response_chat and "message" in response_chat and "content" in response_chat["message"]:
            print("Assistant's reply:", response_chat["message"]["content"].strip())
        else:
            print("No valid chat response received.")

        print("\n" + "="*40 + "\n")

        # --- Example 3: Using the client as an async context manager (recommended) ---
        print("--- Example 3: Using client as an async context manager ---")
        async with OllamaClient() as ctx_client:
            prompt_ctx = "Tell me a short story about a brave mouse."
            print(f"Prompt: '{prompt_ctx}' (Model: {model})")
            response_ctx = await ctx_client.generate(model=model, prompt=prompt_ctx)
            if response_ctx and "response" in response_ctx:
                print("Story:", response_ctx["response"].strip())
            else:
                print("No story received.")


    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Ensure the client session is closed when done
        await client.close()
        print("\nClient session closed.")

if __name__ == "__main__":
    # Run the main asynchronous function
    asyncio.run(main())

