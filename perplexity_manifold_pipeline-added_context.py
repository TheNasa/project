from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
import os
import requests

class Pipeline:
    class Valves(BaseModel):
        PERPLEXITY_API_BASE_URL: str = "https://api.perplexity.ai"
        PERPLEXITY_API_KEY: str = ""
        pass

    def __init__(self):
        self.type = "manifold"
        self.name = "Perplexity: "

        self.valves = self.Valves(
            **{
                "PERPLEXITY_API_KEY": os.getenv(
                    "PERPLEXITY_API_KEY", "your-perplexity-api-key-here"
                )
            }
        )

        # Debugging: print the API key to ensure it's loaded
        print(f"Loaded API Key: {self.valves.PERPLEXITY_API_KEY}")

        # List of models
        self.pipelines = [
            {"id": "llama-3-sonar-large-32k-online", "name": "Llama 3 Sonar Large 32K Online"},
            {"id": "llama-3-sonar-small-32k-online", "name": "Llama 3 Sonar Small 32K Online"},
            {"id": "llama-3-sonar-large-32k-chat", "name": "Llama 3 Sonar Large 32K Chat"},
            {"id": "llama-3-sonar-small-32k-chat", "name": "Llama 3 Sonar Small 32K Chat"},
            {"id": "llama-3-8b-instruct", "name": "Llama 3 8B Instruct"},
            {"id": "llama-3-70b-instruct", "name": "Llama 3 70B Instruct"},
            {"id": "mixtral-8x7b-instruct", "name": "Mixtral 8x7B Instruct"},
            {"id": "related", "name": "Related"}
        ]
        pass

    async def on_startup(self):
        # This function is called when the server is started.
        print(f"on_startup:{__name__}")
        pass

    async def on_shutdown(self):
        # This function is called when the server is stopped.
        print(f"on_shutdown:{__name__}")
        pass

    async def on_valves_updated(self):
        # This function is called when the valves are updated.
        print(f"on_valves_updated:{__name__}")
        # No models to fetch, static setup
        pass

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        print(f"pipe:{__name__}")

        print(messages)
        print(user_message)

        headers = {
            "Authorization": f"Bearer {self.valves.PERPLEXITY_API_KEY}",
            "Content-Type": "application/json",
            "accept": "application/json"
        }

        # Check if the last message in the messages list is from the user
        if not messages or messages[-1]["role"] != "user":
            # Append the user's message to the messages list
            messages.append({"role": "user", "content": user_message})

        payload = {
            "model": model_id,
            "messages": messages,
            "stream": body.get("stream", True),
            "return_citations": True,
            "return_images": True
        }

        print(payload)

        try:
            r = requests.post(
                url=f"{self.valves.PERPLEXITY_API_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
                stream=True,
            )

            r.raise_for_status()

            if body.get("stream", False):
                return r.iter_lines()
            else:
                response = r.json()
                formatted_response = {
                    "id": response["id"],
                    "model": response["model"],
                    "created": response["created"],
                    "usage": response["usage"],
                    "object": response["object"],
                    "choices": [
                        {
                            "index": choice["index"],
                            "finish_reason": choice["finish_reason"],
                            "message": {
                                "role": choice["message"]["role"],
                                "content": choice["message"]["content"]
                            },
                            "delta": {"role": "assistant", "content": ""}
                        } for choice in response["choices"]
                    ]
                }
                
                # Append the assistant's response to the messages list
                messages.append({"role": "assistant", "content": formatted_response["choices"][0]["message"]["content"]})
                
                return formatted_response
        except requests.exceptions.RequestException as e:
            error_message = f"Error: {e}"
            print(error_message)
            print("Response:", e.response.text)
            return error_message

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Perplexity API Client")
    parser.add_argument("--api-key", type=str, required=True, help="API key for Perplexity")

    args = parser.parse_args()

    pipeline = Pipeline()
    pipeline.valves.PERPLEXITY_API_KEY = args.api_key
    
    # Initialize the messages list with a system message
    messages = [{"role": "system", "content": "Be precise and concise."}]
    
    # Simulate a conversation
    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            break
        response = pipeline.pipe(user_message=user_input, model_id="llama-3-sonar-large-32k-chat", messages=messages, body={"stream": False})
        print("Assistant:", response["choices"][0]["message"]["content"])

