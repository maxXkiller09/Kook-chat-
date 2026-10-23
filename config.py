import os
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()
OWNER_ID = int(os.getenv('OWNER_ID', '0') or 0)
DATABASE_PATH = os.getenv('DATABASE_PATH', 'kook.db')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '').strip()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '').strip()
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '').strip()
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '').strip()
GLM_API_KEY = os.getenv('GLM_API_KEY', '').strip()
XAI_API_KEY = os.getenv('XAI_API_KEY', '').strip()
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '').strip()
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '').strip()
DEFAULT_PERSONALITY = 'savage'
PERSONALITIES = {'savage':'Savage, witty, playful Hinglish; tease lightly, never be cruel.', 'sweet':'Warm, caring and sweet Hinglish.', 'flirty':'Playful and charming, keep it respectful.', 'dark':'Mysterious, dramatic and poetic.', 'funny':'Funny, meme-aware and chaotic Hinglish.', 'gangster':'Confident street-style Hinglish, no threats.', 'formal':'Clear, respectful and professional.'}
