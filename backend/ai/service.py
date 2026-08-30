import logging
import os

from litellm import completion

from .prompt import SYSTEM_PROMPT

logger = logging.getLogger(__name__)
FALLBACK_REPLY = "I’m sorry, I’m having trouble responding right now. I can still help connect you with the Maehan Solutions team."


class AIService:
    def response(self, messages, transition_prompt=None):
        configured_models = [model for model in (os.getenv("LLM_PRIMARY_MODEL"), os.getenv("LLM_FALLBACK_MODEL")) if model]
        if not configured_models:
            return FALLBACK_REPLY
        request_messages = [{"role": "system", "content": SYSTEM_PROMPT}, *messages[-12:]]
        if transition_prompt:
            request_messages.append({"role": "system", "content": f"Address the user's most recent message using context, then naturally transition to the following goal: {transition_prompt}"})
        for model in configured_models:
            try:
                # `groq/openai/gpt-oss-120b` is resolved by LiteLLM with
                # GROQ_API_KEY. The browser never receives this credential.
                completion_args = {"model": model, "messages": request_messages, "max_tokens": 350}
                # Gemini 3.x rejects deprecated sampling parameters such as
                # temperature; let the provider use its default behavior.
                if not model.startswith("gemini/"):
                    completion_args["temperature"] = 0.3
                result = completion(**completion_args)
                content = result.choices[0].message.content
                if content:
                    return content.strip()
            except Exception:
                logger.warning("LLM provider call failed; trying fallback", extra={"model": model})
        return FALLBACK_REPLY
