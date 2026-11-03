import asyncio
import os
import time
from contextvars import ContextVar

from dotenv import load_dotenv
from openai import OpenAI

# FOUNDRY SPECIFIC IMPORTS

from foundry_sdk.v2.language_models.utils import get_openai_base_url, get_anthropic_base_url, get_http_client
from foundry_sdk._core.context_and_environment_vars import HOSTNAME_VAR, TOKEN_VAR

load_dotenv()

_loop_semaphore: ContextVar[asyncio.Semaphore] = ContextVar("_loop_semaphore", default=None)

# FOUNDRY SPECIFIC FUNCTIONS


def _is_anthropic_model(model: str) -> bool:
    return "anthropic" in model


def _is_responses_model(model: str) -> bool:
    return "oss" in model.lower()


def _call_llm_responses(prompt, model, temp, max_attempts, chat_history, system_message):
    HOSTNAME_VAR.set(os.getenv("FOUNDRY_HOSTNAME"))
    token = os.getenv("TOKEN") or os.getenv("FOUNDRY_TOKEN")
    TOKEN_VAR.set(token)
    client = OpenAI(
        api_key=token,
        base_url=get_openai_base_url(preview=True),
        http_client=get_http_client(preview=True),
    )

    parts = []
    if system_message:
        parts.append({"role": "system", "content": system_message})
    if chat_history:
        for i, content in enumerate(chat_history):
            parts.append({"role": "user" if i % 2 == 0 else "assistant", "content": content})
    parts.append({"role": "user", "content": prompt})

    for attempt in range(max_attempts):
        try:
            response = client.responses.create(
                model=model,
                input=parts,
                temperature=temp,
            )
            return response.output_text
        except Exception as e:
            print(f"LLM call failed with error: {e} on attempt {attempt + 1}/{max_attempts}. Retrying...")
            time.sleep(2**attempt + 10)
    print(f"Failed after {max_attempts} attempts.")


def _call_llm_anthropic(prompt, model, temp, max_attempts, chat_history, system_message):
    HOSTNAME_VAR.set(os.getenv("FOUNDRY_HOSTNAME"))
    TOKEN_VAR.set(os.getenv("TOKEN") or os.getenv("FOUNDRY_TOKEN"))
    client = get_http_client(preview=True)
    base_url = get_anthropic_base_url(preview=True)

    messages = []
    if chat_history:
        for i, content in enumerate(chat_history):
            messages.append({"role": "user" if i % 2 == 0 else "assistant", "content": content})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": model,
        "max_tokens": 4096,
        "messages": messages,
        "temperature": temp,
    }
    if system_message:
        body["system"] = system_message

    for attempt in range(max_attempts):
        try:
            resp = client.post(
                f"{base_url}/v1/messages",
                json=body,
                headers={"anthropic-version": "2023-06-01"},
                timeout=120,
            )
            resp.raise_for_status()
            return resp.json()["content"][0]["text"]
        except Exception as e:
            print(f"LLM call failed with error: {e} on attempt {attempt + 1}/{max_attempts}. Retrying...")
            time.sleep(2**attempt + 10)
    print(f"Failed after {max_attempts} attempts.")


def _call_llm_openai(prompt, model, temp, max_attempts, chat_history, system_message):
    HOSTNAME_VAR.set(os.getenv("FOUNDRY_HOSTNAME"))
    token = os.getenv("TOKEN") or os.getenv("FOUNDRY_TOKEN")
    TOKEN_VAR.set(token)
    client = OpenAI(
        api_key=token,
        base_url=get_openai_base_url(preview=True),
        http_client=get_http_client(preview=True),
    )

    if not chat_history:
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
    else:
        history = [{"role": "user" if i % 2 == 0 else "assistant", "content": chat_history[i]} for i in range(len(chat_history))]
        if system_message:
            history = [{"role": "system", "content": system_message}] + history
        messages = history + [{"role": "user", "content": prompt}]

    for attempt in range(max_attempts):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temp,
            )
            raw_content = response.choices[0].message.content
        except Exception as e:
            print(f"LLM call failed with error: {e} on attempt {attempt + 1}/{max_attempts}. Retrying...")
            time.sleep(2**attempt + 10)
        else:
            return raw_content
    print(f"Failed after {max_attempts} attempts.")


# 1 - call_llm

def call_llm(prompt: str, model="ri.language-model-service..language-model.gpt-5-1", temp: float = 0.7, max_attempts: int = 5, chat_history = None, verbose = None, system_message: str | None = None) -> str:
    """
    Calls the LLM with the given prompt and returns the raw text output.
    Routes to the Anthropic-compatible or OpenAI-compatible Foundry proxy
    based on the model identifier.
    """
    if _is_anthropic_model(model):
        return _call_llm_anthropic(prompt, model, temp, max_attempts, chat_history, system_message)
    if _is_responses_model(model):
        return _call_llm_responses(prompt, model, temp, max_attempts, chat_history, system_message)
    return _call_llm_openai(prompt, model, temp, max_attempts, chat_history, system_message)

async def call_llm_async(prompt: str, model="ri.language-model-service..language-model.gpt-5-1", temp: float = 0.7, max_attempts: int = 5, chat_history=None, verbose: bool = False, system_message: str | None = None):
    """
    Async wrapper for the synchronous LLM call, limited to 'llm_semaphore' concurrent calls.
    """
    sem = _loop_semaphore.get()
    if sem is None:
        sem = asyncio.Semaphore(1)
        _loop_semaphore.set(sem)

    async with sem:
        return await asyncio.to_thread(
            call_llm, prompt, model, temp, max_attempts, chat_history, verbose, system_message
        )

def get_embeddings(prompts, model="ri.language-model-service..language-model.text-embedding-3-large_azure"):
    HOSTNAME_VAR.set(os.getenv("FOUNDRY_HOSTNAME"))
    token = os.getenv("TOKEN") or os.getenv("FOUNDRY_TOKEN")
    TOKEN_VAR.set(token)
    client = OpenAI(
        api_key=token,
        base_url=get_openai_base_url(preview=True),
        http_client=get_http_client(preview=True),
    )
    response = client.embeddings.create(model=model, input=prompts)
    return [item.embedding for item in response.data]