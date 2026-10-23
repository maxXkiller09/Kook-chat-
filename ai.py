"""Multi-provider chat completion with automatic fallback.

Configure any combination of provider API keys in the Render Environment.
Keys are never included in logs or returned to Telegram.
"""
import logging
import os
import aiohttp

from config import (
    GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, PERSONALITIES,
    OPENAI_API_KEY, ANTHROPIC_API_KEY, DEEPSEEK_API_KEY, GLM_API_KEY, XAI_API_KEY,
)

log = logging.getLogger("kook.ai")


def _messages(prompt, personality, history):
    system = (
        "You are Kook, a lively Telegram group companion. Speak natural Hinglish "
        "when suitable. Keep casual replies short and context-aware; be detailed "
        "for technical questions. Do not claim to be human. Follow this personality: "
        + PERSONALITIES.get(personality, PERSONALITIES["savage"])
    )
    messages = [{"role": "system", "content": system}]
    for item in (history or [])[-12:]:
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        role = "assistant" if item.get("role") == "assistant" else "user"
        messages.append({"role": role, "content": content[:3000]})
    messages.append({"role": "user", "content": str(prompt)[:5000]})
    return system, messages


async def _openai_compatible(session, name, url, key, model, messages):
    if not key:
        return None
    try:
        async with session.post(
            url,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "messages": messages, "temperature": 0.8, "max_tokens": 500},
        ) as response:
            data = await response.json(content_type=None)
            if response.status >= 300:
                log.warning("%s provider returned HTTP %s: %s", name, response.status,
                            str(data.get("error", data.get("message", "request failed")))[:250])
                return None
            answer = data["choices"][0]["message"]["content"]
            if isinstance(answer, list):
                answer = "".join(part.get("text", "") for part in answer if isinstance(part, dict))
            return answer.strip() or None
    except Exception as exc:
        log.warning("%s provider failed (%s)", name, type(exc).__name__)
        return None


async def _gemini(session, key, model, system, messages):
    if not key:
        return None
    try:
        contents = []
        for msg in messages:
            if msg["role"] == "system":
                continue
            contents.append({
                "role": "model" if msg["role"] == "assistant" else "user",
                "parts": [{"text": msg["content"]}],
            })
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.8, "maxOutputTokens": 500},
        }
        async with session.post(url, params={"key": key}, json=body) as response:
            data = await response.json(content_type=None)
            if response.status >= 300:
                err = data.get("error", {})
                log.warning("Gemini provider returned HTTP %s: %s", response.status,
                            str(err.get("message", "request failed"))[:250])
                return None
            return "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"]).strip() or None
    except Exception as exc:
        log.warning("Gemini provider failed (%s)", type(exc).__name__)
        return None


async def _anthropic(session, key, model, system, messages):
    if not key:
        return None
    try:
        payload_messages = [m for m in messages if m["role"] != "system"]
        async with session.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={"model": model, "system": system, "messages": payload_messages,
                  "max_tokens": 500, "temperature": 0.8},
        ) as response:
            data = await response.json(content_type=None)
            if response.status >= 300:
                log.warning("Anthropic provider returned HTTP %s: %s", response.status,
                            str(data.get("error", {}).get("message", "request failed"))[:250])
                return None
            return "".join(x.get("text", "") for x in data.get("content", []) if x.get("type") == "text").strip() or None
    except Exception as exc:
        log.warning("Anthropic provider failed (%s)", type(exc).__name__)
        return None


async def ask(prompt, personality="savage", history=None):
    system, messages = _messages(prompt, personality, history)
    timeout = aiohttp.ClientTimeout(total=22, connect=8)
    providers = [
        ("OpenAI", OPENAI_API_KEY, os.getenv("OPENAI_MODEL", "gpt-4o-mini")),
        ("Claude", ANTHROPIC_API_KEY, os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")),
        ("Gemini", GEMINI_API_KEY, os.getenv("GEMINI_MODEL", "gemini-2.5-flash")),
        ("DeepSeek", DEEPSEEK_API_KEY, os.getenv("DEEPSEEK_MODEL", "deepseek-chat")),
        ("GLM", GLM_API_KEY, os.getenv("GLM_MODEL", "glm-4-flash")),
        ("Grok", XAI_API_KEY, os.getenv("XAI_MODEL", "grok-3-mini")),
        ("Groq", GROQ_API_KEY, os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")),
        ("OpenRouter", OPENROUTER_API_KEY, os.getenv("OPENROUTER_MODEL", "openrouter/auto")),
    ]
    configured = [name for name, key, _ in providers if key]
    if not configured:
        log.error("No AI provider API keys configured")
        return "AI setup nahi hua 😭 Render Environment mein kisi provider ki API key add karo."

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for name, key, model in providers:
            if not key:
                continue
            if name == "Gemini":
                answer = await _gemini(session, key, model, system, messages)
            elif name == "Claude":
                answer = await _anthropic(session, key, model, system, messages)
            else:
                url = {
                    "OpenAI": "https://api.openai.com/v1/chat/completions",
                    "DeepSeek": "https://api.deepseek.com/chat/completions",
                    "GLM": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                    "Grok": "https://api.x.ai/v1/chat/completions",
                    "Groq": "https://api.groq.com/openai/v1/chat/completions",
                    "OpenRouter": "https://openrouter.ai/api/v1/chat/completions",
                }[name]
                answer = await _openai_compatible(session, name, url, key, model, messages)
            if answer:
                log.info("AI response served by %s", name)
                return answer
    log.error("All configured AI providers failed: %s", ", ".join(configured))
    return "Sabhi AI APIs abhi fail ho rahi hain 😭 Keys, credits aur provider limits check karo."
