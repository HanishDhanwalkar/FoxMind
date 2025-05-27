import openai

import dotenv
import os
from termcolor import colored

env_path = "agents/.env"
if os.path.exists(env_path):
    dotenv.load_dotenv(env_path)
else:
    print(colored("No .env file found in 'agents/.env'. Please create one.", "red"))

openai.api_key = os.getenv("OPENAI_API_KEY")
print(openai.api_key)