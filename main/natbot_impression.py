import time
from sys import argv, exit, platform
import os
from natbot.prompt_template import get_prompt_template

from base_llm import OllamaClient
from crawler import Crawler

uiet = False
if len(argv) >= 2:
	if argv[1] == '-q' or argv[1] == '--quiet':
		quiet = True
		print(
			"Running in quiet mode (HTML and other content hidden); \n"
			+ "exercise caution when running suggested commands."
		)

prompt_template = get_prompt_template()

def print_help():
    print(
        "(g) to visit url\n(u) scroll up\n(d) scroll down\n(c) to click\n(t) to type\n" +
        "(h) to view commands again\n(r/enter) to run suggested command\n(o) change objective"
    )
    
def get_gpt_command(llm_client ,objective, url, previous_command, browser_content):
    prompt = prompt_template
    prompt = prompt.replace("$objective", objective)
    prompt = prompt.replace("$url", url[:100])
    prompt = prompt.replace("$previous_command", previous_command)
    prompt = prompt.replace("$browser_content", browser_content[:4500])
    response = llm_client.chat(prompt=prompt)
    return response

def run_cmd(cmd):
    cmd = cmd.split("\n")[0]

    if cmd.startswith("SCROLL UP"):
        _crawler.scroll("up")
    elif cmd.startswith("SCROLL DOWN"):
        _crawler.scroll("down")
    elif cmd.startswith("CLICK"):
        commasplit = cmd.split(",")
        id = commasplit[0].split(" ")[1]
        _crawler.click(id)
    elif cmd.startswith("TYPE"):
        spacesplit = cmd.split(" ")
        id = spacesplit[1]
        text = spacesplit[2:]
        text = " ".join(text)
        # Strip leading and trailing double quotes
        text = text[1:-1]

        if cmd.startswith("TYPESUBMIT"):
            text += '\n'
        _crawler.type(id, text)

    time.sleep(2)


if __name__ == "__main__":
    _client = OllamaClient()
    _crawler = Crawler()
    
    objective = "Make a reservation for 2 at 7pm at bistro vida in menlo park"
    print("\nWelcome to natbot! What is your objective?")
    i = input()
    if len(i) > 0:
        objective = i

    gpt_cmd = ""
    prev_cmd = ""
    _crawler.go_to_page("duckduckgo.com")
    try:
        # while True:
        #     browser_content = "\n".join(_crawler.crawl())
        #     prev_cmd = gpt_cmd
        #     gpt_cmd = get_gpt_command(objective, _crawler.page.url, prev_cmd, browser_content)
        #     gpt_cmd = gpt_cmd.strip()

        #     if not quiet:
        #         print("URL: " + _crawler.page.url)
        #         print("Objective: " + objective)
        #         print("----------------\n" + browser_content + "\n----------------\n")
        #     if len(gpt_cmd) > 0:
        #         print("Suggested command: " + gpt_cmd)


        #     command = input()
        #     if command == "r" or command == "":
        #         run_cmd(gpt_cmd)
        #     elif command == "g":
        #         url = input("URL:")
        #         _crawler.go_to_page(url)
        #     elif command == "u":
        #         _crawler.scroll("up")
        #         time.sleep(1)
        #     elif command == "d":
        #         _crawler.scroll("down")
        #         time.sleep(1)
        #     elif command == "c":
        #         id = input("id:")
        #         _crawler.click(id)
        #         time.sleep(1)
        #     elif command == "t":
        #         id = input("id:")
        #         text = input("text:")
        #         _crawler.type(id, text)
        #         time.sleep(1)
        #     elif command == "o":
        #         objective = input("Objective:")
        #     else:
        #         print_help()
        
        print("TEST TEXTS")
    except KeyboardInterrupt:
        print("\n[!] Ctrl+C detected, exiting gracefully.")
        exit(0)


