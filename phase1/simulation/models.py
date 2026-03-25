import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Callable, Dict
from openai import OpenAI
import anthropic


env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


# -----------------------
# GPT (OpenAI)
# -----------------------
def gpt_model_fn(model, system_prompt, user_prompt, temperature):

    api_key = os.getenv("PERSONAL_OPENAI_KEY")
    if not api_key:
        raise ValueError(
            "PERSONAL_OPENAI_KEY not set. Either:\n"
            "  1. Set: export PERSONAL_OPENAI_KEY='your-key'\n"
            "  2. Create .env file with PERSONAL_OPENAI_KEY=sk-...\n"
            "  3. Or switch to a local model (qwen, llama, mistral)"
        )

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content.strip()


# ----------------------------------------------------
# LLaMA / Mistral / Qwen / DeepSeek (via local server)
# ----------------------------------------------------
def open_model_fn(model, system_prompt, user_prompt, temperature):
    api_base = os.getenv("VLLM_API_BASE", "http://localhost:7474")
    
    client = OpenAI(
        base_url=f"{api_base}/v1",
        api_key="not-needed"
    )

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=512,
        )

        content = response.choices[0].message.content.strip()
        if not content:
            raise ValueError(f"Empty response from model {model} at {api_base}")
        return content
    except Exception as e:
        raise RuntimeError(
            f"Failed to call {model} at {api_base}. "
            f"Make sure vLLM is running: bash /playpen-ssd/wokwen/local_models/serve_model.sh -m Llama3 -p 7474\n"
            f"Error: {e}"
        )


# -----------------------
# Claude (Anthropic)
# -----------------------
def claude_model_fn(model, system_prompt, user_prompt, temperature):
    client = anthropic.Anthropic()

    response = client.messages.create(
        model=model,
        temperature=temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
        max_tokens=512,
    )

    return response.content[0].text.strip()


# -----------------------
# Registry (IMPORTANT)
# -----------------------
MODEL_REGISTRY: Dict[str, Callable] = {
    "gpt": gpt_model_fn,
    "llama": open_model_fn,
    "mistral": open_model_fn,
    "qwen": open_model_fn,
    "deepseek": open_model_fn,
    "claude": claude_model_fn,
}