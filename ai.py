import aiohttp
from config import GEMINI_API_KEY,GROQ_API_KEY,OPENROUTER_API_KEY,PERSONALITIES

async def ask(prompt, personality='savage', history=None):
    system='You are Kook, a lively Telegram group companion. Speak natural Hinglish when suitable. Keep casual replies short and context-aware; be detailed for technical questions. Do not claim to be human. Follow this personality: '+PERSONALITIES.get(personality,PERSONALITIES['savage'])
    messages=[{'role':'system','content':system}]
    for item in (history or []):
        role='assistant' if item.get('role')=='assistant' else 'user'
        messages.append({'role':role,'content':item.get('content','')})
    messages.append({'role':'user','content':prompt})
    timeout=aiohttp.ClientTimeout(total=25)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        if GEMINI_API_KEY:
            try:
                url='https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key='+GEMINI_API_KEY
                body={'systemInstruction':{'parts':[{'text':system}]},'contents':[{'role':'user','parts':[{'text':('\n'.join(x['content'] for x in messages[1:]))}]}]}
                async with s.post(url,json=body) as r:
                    d=await r.json()
                    if r.status<300: return d['candidates'][0]['content']['parts'][0]['text']
            except Exception: pass
        providers=[]
        if GROQ_API_KEY: providers.append(('https://api.groq.com/openai/v1/chat/completions',GROQ_API_KEY,'llama-3.3-70b-versatile'))
        if OPENROUTER_API_KEY: providers.append(('https://openrouter.ai/api/v1/chat/completions',OPENROUTER_API_KEY,'openrouter/auto'))
        for url,key,model in providers:
            try:
                async with s.post(url,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},json={'model':model,'messages':messages,'temperature':0.8,'max_tokens':450}) as r:
                    d=await r.json()
                    if r.status<300: return d['choices'][0]['message']['content']
            except Exception: pass
    return 'AI abhi thoda offline hai 😭 baad mein try karna.'
