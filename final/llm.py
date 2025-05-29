import ollama

class OllamaClient:
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
            # "options": {
            #     "temperature": 0.1,
            #     "num_predict": 1000,
            # }
        }
        response = self.client.chat(
            **payload
        )
        
        self.messages.append({"role": "assistant", "content": response.message.content})
        return response.message.content

# while True:
#     messages = []

#     user_input = input("You: ")
#     if user_input.lower() == 'exit' or user_input.lower() == 'q':
#         break
#     res = client.chat(
#         model="llama3.2",
#         messages=[
#             {"role": "user", "content": user_input}
#         ],
#     )
#     print(res.message.content)

if __name__ == "__main__":
    client = OllamaClient()
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit' or user_input.lower() == 'q':
            break
        res = client.chat(user_input)
        print(res)




# res = ollama_chat_with_history(model_name="llama3.2", prompt=get_prompt_template())
# print(res)

#########
# OPENAI
#########

# import openai

# import dotenv
# import os

# dotenv.load_dotenv("agents/.env")

# openai.api_key = os.getenv("OPENAI_API_KEY")
# print(openai.api_key)