import re
import os

def remove_img_tags(file_path):
    # Read the contents of the file
    with open(file_path, 'r', encoding="utf-8") as file:
        html = file.read()

    # Use regex to find and replace all img tags
    cleaned_html = re.sub(r'<img.*?>', '', html)
    cleaned_html = re.sub(r'<svg.*?>', '', cleaned_html)
    cleaned_html = re.sub(r'</svg.*?>', '', cleaned_html)
    
    return cleaned_html

if __name__ == "__main__":
    v2 = True
    
    
    
    
    
    if v2 == True:
        file_path = "limited-v2.html"
    else:
        file_path = "limited.html"
    if os.path.exists(file_path):
        print("File exists")
        cleaned_html = remove_img_tags(file_path)
    # print(cleaned_html)
    
    to_save = "no_image_limited.html"
    if v2:
        to_save = "no_image_limited-v2.html"
    with open(to_save, "w", encoding="utf-8") as f:
        f.write(cleaned_html)