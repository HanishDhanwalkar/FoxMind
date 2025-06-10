# ollama_client.py

import aiohttp
import asyncio
import json

class OllamaClient:
    """
    An asynchronous client for interacting with the Ollama API.
    """

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.session = None  # aiohttp ClientSession will be created on first use

    async def _get_session(self):
        """
        Lazily creates and returns an aiohttp ClientSession.
        """
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def generate(self, model: str, prompt: str, stream: bool = False) -> dict:
        """
        Sends a generate request to the Ollama API.

        Args:
            model (str): The name of the model to use (e.g., "llama2").
            prompt (str): The input prompt for the model.
            stream (bool): Whether to stream the response. Defaults to False.

        Returns:
            dict: The JSON response from the Ollama API.

        Raises:
            aiohttp.ClientError: If there's an HTTP client error.
            ValueError: If the API returns an error or an unexpected status code.
        """
        endpoint = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
        }

        session = await self._get_session()
        try:
            async with session.post(endpoint, json=payload) as response:
                if response.status == 200:
                    if stream:
                        # For streaming, we'd typically process each chunk
                        # but for simplicity, this example collects all and returns
                        # This part would need more sophisticated handling for real streaming
                        full_response_text = ""
                        async for chunk in response.content.iter_any():
                            try:
                                # Each chunk might be a partial JSON line
                                # assuming ndjson format from Ollama for streaming
                                for line in chunk.decode('utf-8').splitlines():
                                    if line.strip():
                                        data = json.loads(line)
                                        if "response" in data:
                                            full_response_text += data["response"]
                                        if data.get("done"):
                                            return {"response": full_response_text, "done": True}
                            except json.JSONDecodeError:
                                print(f"Warning: Could not decode JSON chunk: {line}")
                        return {"response": full_response_text, "done": True}
                    else:
                        return await response.json()
                else:
                    error_detail = await response.text()
                    raise ValueError(
                        f"Ollama API request failed with status {response.status}: {error_detail}"
                    )
        except aiohttp.ClientConnectorError as e:
            raise aiohttp.ClientError(
                f"Could not connect to Ollama server at {self.base_url}. Is it running? Error: {e}"
            )
        except aiohttp.ClientError as e:
            raise aiohttp.ClientError(f"An HTTP client error occurred: {e}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred: {e}")

    async def chat(self, model: str, messages: list, stream: bool = False) -> dict:
        """
        Sends a chat request to the Ollama API.

        Args:
            model (str): The name of the model to use (e.g., "llama2").
            messages (list): A list of message objects for the chat history.
                             Each message should be a dict with "role" and "content".
                             Example: [{"role": "user", "content": "Hello!"}]
            stream (bool): Whether to stream the response. Defaults to False.

        Returns:
            dict: The JSON response from the Ollama API.

        Raises:
            aiohttp.ClientError: If there's an HTTP client error.
            ValueError: If the API returns an error or an unexpected status code.
        """
        endpoint = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

        session = await self._get_session()
        try:
            async with session.post(endpoint, json=payload) as response:
                if response.status == 200:
                    if stream:
                        # Similar to generate, this would need more robust handling
                        # for real-time streaming of chat responses.
                        full_content = ""
                        async for chunk in response.content.iter_any():
                            try:
                                for line in chunk.decode('utf-8').splitlines():
                                    if line.strip():
                                        data = json.loads(line)
                                        if "message" in data and "content" in data["message"]:
                                            full_content += data["message"]["content"]
                                        if data.get("done"):
                                            # Return a structure similar to non-streamed response
                                            return {"message": {"role": "assistant", "content": full_content}, "done": True}
                            except json.JSONDecodeError:
                                print(f"Warning: Could not decode JSON chunk: {line}")
                        return {"message": {"role": "assistant", "content": full_content}, "done": True}
                    else:
                        return await response.json()
                else:
                    error_detail = await response.text()
                    raise ValueError(
                        f"Ollama chat API request failed with status {response.status}: {error_detail}"
                    )
        except aiohttp.ClientConnectorError as e:
            raise aiohttp.ClientError(
                f"Could not connect to Ollama server at {self.base_url}. Is it running? Error: {e}"
            )
        except aiohttp.ClientError as e:
            raise aiohttp.ClientError(f"An HTTP client error occurred: {e}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred: {e}")

    async def close(self):
        """
        Closes the aiohttp ClientSession.
        It's important to call this when the client is no longer needed
        to clean up resources.
        """
        if self.session:
            await self.session.close()
            self.session = None

    async def __aenter__(self):
        """Allows the client to be used as an asynchronous context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Ensures the session is closed when exiting the context manager."""
        await self.close()

