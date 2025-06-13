import re
import json
import ast


# def extract_json_from_response(text):
#     match = re.search(r'\{(?:[^{}]|(?R))*\}', text, re.DOTALL)
#     if match:
#         try:
#             return json.loads(match.group())
#         except json.JSONDecodeError:
#             print("Found JSON-like content but couldn't parse it.")
#     else:
#         print("No JSON object found.")
#     return None


def extract_json_from_response(text):
    try:
        data = ast.literal_eval(text)
        # print(data)
        return data
    except Exception as e:
        print("Parsing failed:", e)
        
if __name__ == "__main__":
    # text = "{'key': 'value'}"
    text = """Execute action: Based on the current browser state, I will perform the following actions:

1. Navigate to DuckDuckGo and search for supercars:
   - action: navigate
   - value: https://duckduckgo.com/?q=supercars

2. Wait for the page to load before proceeding.

Here is the JSON object representing these actions:

```
[
  {
    "action": "navigate",
    "value": "https://duckduckgo.com/?q=supercars"
  },
  {
    "action": "wait"
  }
]
```
"""
    print(extract_json_from_response(text))