from ollama import chat

def promt_for_summarisation(webpage):
    prompt = f"""
Summarise this scraped webpage: 
{webpage}

In the format:

Title: <title>
Summary: \n
<text><link(if any)>
<text><link(if any)>
<text><link(if any)>....

INCLUDE ALL the links in same order as they apppear in the weebpage with samll description if any as they are important for downstream tasks.
"""

    return prompt

def summarise_web(webpage):
    result = chat(
                    "llama3.2", 
                    messages=[
                        {"role": "user", "content": promt_for_summarisation(webpage=webpage)}
                    ]
                )
    
    return result.message.content

if __name__ == "__main__":
    with open("example.txt", "r", encoding="utf-8") as f:
        webpage = f.read()

    print(summarise_web(webpage=webpage))