import re
import json

# import ast
# def extract_json_from_response(text):
#     try:
#         data = ast.literal_eval(text)
#         # print(data)
#         return data
#     except Exception as e:
#         print("Parsing failed:", e)
#     return None

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

# def extract_json_from_response(text):
#     match = re.search(r"```json\s*([\s\S]*?)\s*```", text)
#     if match:
#         json_str = match.group(1).strip('"').strip("'")
#         # print("Extracted JSON string:", json_str)
#         try:
#             json_obj = json.loads(json.dumps(json_str))
#             print(type(json_obj))
#             return json_obj
#         except json.JSONDecodeError as e:
#             print("JSON parse error:", e)
#     else:
#         print("No JSON block found.")
#     return None

def extract_json_from_response(text):
    match = re.search(r"```json\s*([\s\S]*?)\s*```", text)
    if match:
        json_str = match.group(1).strip()

        # Replace Python-style literals with valid JSON
        json_str = json_str.replace("None", "null")
        json_str = json_str.replace("True", "true")
        json_str = json_str.replace("False", "false")

        try:
            json_obj = json.loads(json_str)
            print(type(json_obj))  # Should print <class 'dict'>
            return json_obj
        except json.JSONDecodeError as e:
            print("JSON parse error:", e)
    else:
        print("No JSON block found.")
    return None