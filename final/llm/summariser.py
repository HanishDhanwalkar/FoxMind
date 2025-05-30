import base_llm as base_llm

class Summariser(base_llm.OllamaClient):
    def __init__(self):
        super().__init__()

    def summarise(self, text):
        prompt = f""" You are an helpful AI summariser agent.
Please extract the main topic, key arguments or information presented, and any significant conclusions or takeaways. 

Here is the webpage content:

{text}

Your output should be structured as follows:

Summary:
[A concise summary of the webpage, covering main topic, key points, and conclusions in bullet points.]

Please ensure the summary is objective and accurately reflects the content, avoiding any personal opinions or interpretations. Prioritize informative and actionable links.".
"""
        return self.chat(prompt)
    
if __name__ == "__main__":
    summariser = Summariser()
    
    with open("viewport.txt", "r", encoding="utf-8") as f:
        text = f.read()
    print(summariser.summarise(f"text: {text}"))