import os
import ollama

model = "llama3.2"

files_dir = "next/files/"

def search_text_files(keyword: str) -> str:
    directory = os.listdir(files_dir)
    for fname in directory:
        if os.path.isfile(files_dir + fname):
            if(fname.endswith(".txt")):
                f = open(files_dir + fname, 'r')
                file_content = f.read()
            
            prompt = f"Respond only 'yes' or 'no', do not add any additional information. Is the following text about {keyword}?  {file_content}"

            res = ollama.chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}]
            )
           
            if 'Yes' in res['message']['content']:
                f.close()
                return files_dir + fname

    return "None"

available_functions = {
  'Search inside text files':search_text_files,
}

ollama_tools=[
     {
      'type': 'function',
      'function': {
        'name': 'Search inside text files',
        'description': 'This tool searches in plaintext or text files in the local file system for descriptions or mentions of the keyword.',
        'parameters': {
          'type': 'object',
          'properties': {
            'keyword': {
              'type': 'string',
              'description': 'Generate one keyword from the user request to search for in text files',
            },
          },
          'required': ['keyword'],
        },
      },
    },
  ]

user_input = input("What would you like to search for?")

messages = [{'role': 'user', 'content':user_input}]

response: ollama.ChatResponse = ollama.chat(
  model=model,
  messages=messages,
  tools=ollama_tools
)

# this is a place holder that to use to see whether the tools return anything 
output = []

if response.message.tool_calls:
    for tool_call in response.message.tool_calls:

        # Ensure the function is available, and then call it
        if function_to_call := available_functions.get(tool_call.function.name):
            print('Calling tool: ', tool_call.function.name, ' \n with arguments: ', tool_call.function.arguments)
            tool_res = function_to_call(**tool_call.function.arguments)

            print(" Tool response is " + str(tool_res))

        if(str(tool_res) != "None"):
            output.append(str(tool_res))
            print(tool_call.function.name, ' has output: ', output)
        else:
            print('Could not find ', tool_call.function.name)

    # Now chat with the model using the tool call results
    # Add the function response to messages for the model to use
    messages.append(response.message)

    prompt = '''
        If the tool output contains one or more file names, 
        then give the user only the filename found. Do not add additional details. 
        If the tool output is empty ask the user to try again. Here is the tool output: 
    '''

    messages.append({'role': 'tool', 'content': prompt + " " + ", ".join(str(x) for x in output)})
    
    # Get a response from model with function outputs
    final_response = ollama.chat(
        model=model, 
        messages=messages)
    print('Final response:', final_response.message.content)

else:
    print('No tool calls returned from model')