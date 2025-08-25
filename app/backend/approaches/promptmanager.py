import json
import pathlib
import asyncio
import openai
from fastapi import HTTPException

import prompty
from openai.types.chat import ChatCompletionMessageParam


class PromptManager:

    def load_prompt(self, path: str):
        raise NotImplementedError

    def load_tools(self, path: str):
        raise NotImplementedError

    def render_prompt(self, prompt, data) -> list[ChatCompletionMessageParam]:
        raise NotImplementedError

    def messages_to_readable(self, messages: list[ChatCompletionMessageParam]) -> str:
        """Convert messages to human-readable format for UI display"""
        raise NotImplementedError


class PromptyManager(PromptManager):

    PROMPTS_DIRECTORY = pathlib.Path(__file__).parent / "prompts"

    def load_prompt(self, path: str):
        return prompty.load(self.PROMPTS_DIRECTORY / path)

    def load_tools(self, path: str):
        return json.loads(open(self.PROMPTS_DIRECTORY / path).read())

    def render_prompt(self, prompt, data) -> list[ChatCompletionMessageParam]:
        return prompty.prepare(prompt, data)

    def messages_to_readable(self, messages: list[ChatCompletionMessageParam]) -> str:
        """Convert messages to human-readable format for UI display"""
        if not messages:
            return "No messages"
        
        readable_parts = []
        for msg in messages:
            if isinstance(msg, dict):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
            else:
                role = getattr(msg, "role", "unknown")
                content = getattr(msg, "content", "")
            
            # Format content nicely
            if isinstance(content, str):
                formatted_content = content
            elif isinstance(content, list):
                # Handle content arrays (multimodal messages)
                formatted_content = json.dumps(content, indent=2)
            else:
                formatted_content = str(content)
            
            readable_parts.append(f"{role.upper()}:\n{formatted_content}")
        
        return "\n\n".join(readable_parts)

    async def execute_with_timeout(self, client, model, messages, temperature=0.2, **kwargs):
        """Execute OpenAI call with timeout and error handling."""
        try:
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    **kwargs
                ),
                timeout=60
            )
            return response
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Upstream model timeout")
        except openai.APIError as e:
            raise HTTPException(status_code=502, detail=f"OpenAI API error: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Generation failed: {e}")
