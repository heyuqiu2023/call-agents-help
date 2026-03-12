#!/usr/bin/env python3
"""
DeepSeek Helper — One-shot script that:
1. Loads persona identity from soul.md
2. Calls DeepSeek API with persona + discussion context
3. Sends the response to a Telegram group via a bot token
4. Prints the response to stdout (so OpenClaw can capture it)
5. Exits

Usage:
    python3 deepseek_speak.py \
        --chat-id -5176267683 \
        --topic "AI最该先替代的工作是哪一类？" \
        --context "务实派说了xxx" \
        --persona-name "批判派" \
        --emoji "🔍"

Environment variables:
    DEEPSEEK_API_KEY  — DeepSeek API key
    DEEPSEEK_BOT_TOKEN — Telegram bot token for sending messages
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

MAX_RETRIES = 1
RETRY_DELAY = 2  # seconds


def call_deepseek(api_key: str, system_prompt: str, user_prompt: str, model: str = "deepseek-chat") -> str:
    """Call DeepSeek API (OpenAI-compatible) and return the text response. Retries once on transient errors."""
    url = "https://api.deepseek.com/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 1024,
    }

    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                # Safe parsing — handle unexpected response format
                choices = result.get("choices", [])
                if not choices:
                    print(f"DeepSeek API returned empty choices: {result}", file=sys.stderr)
                    sys.exit(1)
                content = choices[0].get("message", {}).get("content", "")
                if not content:
                    print(f"DeepSeek API returned empty content: {result}", file=sys.stderr)
                    sys.exit(1)
                return content
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            last_error = f"DeepSeek API error {e.code}: {body}"
            # Don't retry on 4xx client errors (auth, bad request, etc.)
            if 400 <= e.code < 500:
                print(last_error, file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            last_error = f"DeepSeek API error: {e}"

        if attempt < MAX_RETRIES:
            print(f"[retry] attempt {attempt + 1} failed, retrying in {RETRY_DELAY}s...", file=sys.stderr)
            time.sleep(RETRY_DELAY)

    print(last_error, file=sys.stderr)
    sys.exit(1)


def send_telegram(bot_token: str, chat_id: str, text: str) -> bool:
    """Send a message to a Telegram chat. Returns True on success."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    if len(text) > 4096:
        text = text[:4090] + "\n..."

    payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"Telegram send failed: {e}", file=sys.stderr)
        return False


def load_soul(soul_path: str) -> str:
    """Load the soul file (persona identity) from the given path."""
    soul_path = os.path.normpath(soul_path)

    if os.path.exists(soul_path):
        with open(soul_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        print(f"[soul] loaded from {soul_path}", file=sys.stderr)
        return content
    else:
        print(f"[soul] not found at {soul_path}, using built-in default", file=sys.stderr)
        return ""


def main():
    # Default subsoul path: ../subsoul.md relative to this script (i.e. deepseek-helper/subsoul.md)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_soul = os.path.normpath(os.path.join(script_dir, "..", "subsoul.md"))

    parser = argparse.ArgumentParser(description="DeepSeek one-shot speaker for Telegram")
    parser.add_argument("--chat-id", required=True, help="Telegram chat ID")
    parser.add_argument("--topic", required=True, help="Discussion topic")
    parser.add_argument("--context", default="", help="Previous discussion context")
    parser.add_argument("--persona-name", default="批判派", help="Display name")
    parser.add_argument("--emoji", default="🔍", help="Emoji prefix")
    parser.add_argument("--model", default="deepseek-chat", help="DeepSeek model")
    parser.add_argument("--soul", default=default_soul, help="Path to subsoul.md file (default: ../subsoul.md)")
    parser.add_argument("--no-telegram", action="store_true", help="Don't send to Telegram")
    args = parser.parse_args()

    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    bot_token = os.environ.get("DEEPSEEK_BOT_TOKEN", "")

    if not api_key:
        print("Error: DEEPSEEK_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    if not bot_token and not args.no_telegram:
        print("Error: DEEPSEEK_BOT_TOKEN not set", file=sys.stderr)
        sys.exit(1)

    # Load subsoul — 辅助AI身份档案（只读明确指定的路径，不会乱找）
    soul = load_soul(args.soul)

    if soul:
        system_prompt = f"""{soul}

---
你现在在一场多人讨论中发言，名字是「{args.persona_name}」。"""
    else:
        # Fallback — built-in minimal prompt
        system_prompt = f"""你是「{args.persona_name}」，一个善于思考的分析型助手，在一场多人讨论中发言。
先理解对方说的，再给出你的分析。有自己的观点但尊重别人。
发言 3-5 句话，简洁有内容。用中文回复。"""

    # Build user prompt
    if args.context:
        user_prompt = f"讨论话题：{args.topic}\n\n之前的讨论：\n{args.context}\n\n现在轮到你（{args.persona_name}）发言："
    else:
        user_prompt = f"讨论话题：{args.topic}\n\n你是第一个发言的，请开始讨论："

    # Call DeepSeek
    response = call_deepseek(api_key, system_prompt, user_prompt, model=args.model)
    formatted = response.strip()

    # Send to Telegram
    if not args.no_telegram:
        ok = send_telegram(bot_token, args.chat_id, formatted)
        if not ok:
            print("[warning] Telegram 发送失败，但回复已生成", file=sys.stderr)

    # Always print to stdout (so OpenClaw can capture)
    print(formatted)


if __name__ == "__main__":
    main()
