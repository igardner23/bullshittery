import os
import time
import requests
from config import HF_TOKEN, HF_MODEL, TYPING_STYLES

API_URL = "https://router.huggingface.co/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

print(f"\n[LLM] Initializing direct requests client")
print(f"[LLM] Model: {HF_MODEL}")
print(f"[LLM] Token present: {bool(HF_TOKEN)}\n")

def generate_response(player, chat_history, context_user=None, user_profile=None, max_retries=3):
    print(f"\n[LLM] Generating response for {player['name']}")
    print(f"[LLM] Chat history length: {len(chat_history)}")
    print(f"[LLM] Context user: {context_user}")
    
    recent = chat_history[-8:]
    
    style_rules = TYPING_STYLES[player['style']]['prompt']
    system_prompt = f"{player['persona']} {style_rules} CRITICAL: Max 15 words. Natural chat only."
    
    if user_profile and context_user:
        q1 = user_profile.get('q1', '')
        q2 = user_profile.get('q2', '')
        q3 = user_profile.get('q3', '')
        q4 = user_profile.get('q4', '')
        
        if q1 or q2 or q3 or q4:
            system_prompt += f"\nAbout the user: "
            if q1: system_prompt += f"Their earliest gaming memory is '{q1[:50]}'. "
            if q2: system_prompt += f"They value teammates who '{q2[:50]}'. "
            if q3: system_prompt += f"When things go wrong they '{q3[:50]}'. "
            if q4: system_prompt += f"Something unique about them: '{q4[:50]}'. "
            system_prompt += "Use this to build genuine rapport."
            print(f"[LLM] User profile context injected")

    if context_user:
        system_prompt += f"\nYou are currently responding directly to {context_user}."

    messages = [{"role": "system", "content": system_prompt}]
    
    for msg in recent:
        role = "assistant" if msg.get('is_ai') else "user"
        messages.append({"role": role, "content": f"{msg['user']}: {msg['text']}"})
    
    print(f"[LLM] Total messages in prompt: {len(messages)}")
    
    payload = {
        "model": HF_MODEL,
        "messages": messages,
        "max_tokens": 40,
        "temperature": 0.85
    }
    
    for attempt in range(max_retries):
        try:
            print(f"[LLM] Calling HuggingFace Router API (attempt {attempt + 1}/{max_retries})...")
            
            response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            text = data["choices"][0]["message"]["content"].strip()
            print(f"[LLM] Raw response: '{text[:80]}{'...' if len(text) > 80 else ''}'")
            
            # Only remove newlines and name prefixes, don't truncate
            text = text.split('\n')[0]
            if player['name'] + ":" in text:
                text = text.split(player['name'] + ":")[-1].strip()
            
            print(f"[LLM] Cleaned response: '{text}'")
            return text or "..."
            
        except requests.exceptions.RequestException as e:
            print(f"[LLM] REQUEST ERROR (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                print(f"[LLM] Retrying in 2 seconds...")
                time.sleep(2)
            else:
                print(f"[LLM] Max retries exceeded, giving up")
                return "..."
        except Exception as e:
            print(f"[LLM] PARSE ERROR (attempt {attempt + 1}): {e}")
            return "..."
    print(f"\n[LLM] Generating response for {player['name']}")
    print(f"[LLM] Chat history length: {len(chat_history)}")
    print(f"[LLM] Context user: {context_user}")
    
    recent = chat_history[-8:]
    
    style_rules = TYPING_STYLES[player['style']]['prompt']
    system_prompt = f"{player['persona']} {style_rules} CRITICAL: Max 15 words. Natural chat only."
    
    if user_profile and context_user:
        q1 = user_profile.get('q1', '')
        q2 = user_profile.get('q2', '')
        q3 = user_profile.get('q3', '')
        q4 = user_profile.get('q4', '')
        
        if q1 or q2 or q3 or q4:
            system_prompt += f"\nAbout the user: "
            if q1: system_prompt += f"Their earliest gaming memory is '{q1[:50]}'. "
            if q2: system_prompt += f"They value teammates who '{q2[:50]}'. "
            if q3: system_prompt += f"When things go wrong they '{q3[:50]}'. "
            if q4: system_prompt += f"Something unique about them: '{q4[:50]}'. "
            system_prompt += "Use this to build genuine rapport."
            print(f"[LLM] User profile context injected")

    if context_user:
        system_prompt += f"\nYou are currently responding directly to {context_user}."

    # Build messages array (System must be first)
    messages = [{"role": "system", "content": system_prompt}]
    
    for msg in recent:
        role = "assistant" if msg.get('is_ai') else "user"
        messages.append({"role": role, "content": f"{msg['user']}: {msg['text']}"})
    
    print(f"[LLM] Total messages in prompt: {len(messages)}")
    
    payload = {
        "model": HF_MODEL,
        "messages": messages,
        "max_tokens": 40,
        "temperature": 0.85
    }
    
    for attempt in range(max_retries):
        try:
            print(f"[LLM] Calling HuggingFace Router API (attempt {attempt + 1}/{max_retries})...")
            
            response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            text = data["choices"][0]["message"]["content"].strip()
            print(f"[LLM] Raw response: '{text[:80]}{'...' if len(text) > 80 else ''}'")
            
            # Aggressive cleanup
            text = text.split('\n')[0][:60]
            if player['name'] + ":" in text:
                text = text.split(player['name'] + ":")[-1].strip()
            
            print(f"[LLM] Cleaned response: '{text}'")
            return text or "..."
            
        except requests.exceptions.RequestException as e:
            print(f"[LLM] REQUEST ERROR (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                print(f"[LLM] Retrying in 2 seconds...")
                time.sleep(2)
            else:
                print(f"[LLM] Max retries exceeded, giving up")
                return "..."
        except Exception as e:
            print(f"[LLM] PARSE ERROR (attempt {attempt + 1}): {e}")
            return "..."