import os
import ollama

model = "llama3.2"

def search_text_files(keyword: str) -> str:
  
  directory = os.listdir("./files/")
  for fname in directory:
    
    # look through all the files in our directory that aren't hidden files
    if os.path.isfile("./files/" + fname) and not fname.startswith('.'):

        if(fname.endswith(".pdf")):
           
           document_text = ""
        #    doc = pymupdf.open("./files/" + fname)
            with open("./files/" + fname, 'rb') as f:
               document_text += f.read() # get plain text (is in UTF-8)

           prompt = "Respond only 'yes' or 'no', do not add any additional information. Is the following text about " + keyword + "? " + document_text 

           res = ollama.chat(
                model="granite3.2:8b",
                messages=[{'role': 'user', 'content': prompt}]
            )

           if 'Yes' in res['message']['content']:
                return "./files/" + fname

        elif(fname.endswith(".txt")):
            f = open("./files/" + fname, 'r')
            file_content = f.read()
            
            prompt = "Respond only 'yes' or 'no', do not add any additional information. Is the following text about " + keyword + "? " + file_content 

            res = ollama.chat(
                model="granite3.2:8b",
                messages=[{'role': 'user', 'content': prompt}]
            )
           
            if 'Yes' in res['message']['content']:
                f.close()
                return "./files/" + fname

  return "None"
