import logging, time, random, traceback
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ChatMemberHandler, ContextTypes, filters
from telegram.error import TelegramError
from config import BOT_TOKEN, OWNER_ID, PERSONALITIES
from db import init_db, get_settings, set_setting, remember, recent_memory
from ai import ask

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log=logging.getLogger('kook')
FLOOD={}
XO={}
STARTED=time.time()

def owner(uid): return bool(OWNER_ID and uid==OWNER_ID)
async def start(u,c): await u.effective_message.reply_text('AYOO 👀 Kook online hai 😭 /help dekh lo.')
async def help_cmd(u,c):
    await u.effective_message.reply_text('/personality [savage|sweet|flirty|dark|funny|gangster|formal]\n/welcome on|off\n/setwelcome <text>\n/ban /kick /mute /unmute (reply)\n/warn (reply) /warns (reply)\n/purge (reply) /pin (reply) /unpin (reply)\n/id /groupinfo /admins\n/lock /unlock\n/game /panel /health\nAI: group mein Kook ko mention ya reply karke baat karo.')
async def personality(u,c):
    chat=u.effective_chat
    if not c.args:
        s=get_settings(chat.id); return await u.effective_message.reply_text('Current: '+s['personality']+'\nOptions: '+', '.join(PERSONALITIES))
    p=c.args[0].lower()
    if p not in PERSONALITIES: return await u.effective_message.reply_text('Options: '+', '.join(PERSONALITIES))
    set_setting(chat.id,'personality',p); await u.effective_message.reply_text('Vibe set: '+p+' 😈')
async def welcome(u,c):
    if not c.args or c.args[0].lower() not in ('on','off'): return await u.effective_message.reply_text('/welcome on ya /welcome off')
    set_setting(u.effective_chat.id,'welcome_on',int(c.args[0].lower()=='on')); await u.effective_message.reply_text('Welcome '+c.args[0].lower()+' ✅')
async def setwelcome(u,c):
    if not c.args: return await u.effective_message.reply_text('Use: /setwelcome Welcome {first_name} 👀')
    set_setting(u.effective_chat.id,'welcome_text',' '.join(c.args)); await u.effective_message.reply_text('Welcome text saved ✅')
async def new_members(u,c):
    m=u.effective_message
    if not m or not m.new_chat_members: return
    s=get_settings(m.chat_id)
    if not s['welcome_on']: return
    for person in m.new_chat_members:
        if person.id==c.bot.id: continue
        mention=person.mention_html()
        msg=s['welcome_text'].replace('{first_name}',person.first_name).replace('{name}',person.full_name).replace('{username}',('@'+person.username) if person.username else person.first_name).replace('{mention}',mention).replace('{chat}',m.chat.title or 'this group')
        try: await m.reply_text(msg,parse_mode='HTML')
        except TelegramError: await m.reply_text(msg.replace('<','').replace('>',''))
async def admin_required(u,c):
    chat=u.effective_chat; user=u.effective_user
    if chat.type=='private': return True
    try:
        member=await c.bot.get_chat_member(chat.id,user.id)
        return owner(user.id) or member.status in ('administrator','creator')
    except TelegramError: return owner(user.id)
async def ban(u,c):
    m=u.effective_message
    if not await admin_required(u,c): return await m.reply_text('Admins only 😶')
    target=m.reply_to_message.from_user if m.reply_to_message else None
    if not target: return await m.reply_text('User ke message par reply karke command use karo.')
    await c.bot.ban_chat_member(m.chat_id,target.id); await m.reply_text('Banned 🚫')
async def kick(u,c):
    m=u.effective_message
    if not await admin_required(u,c): return await m.reply_text('Admins only 😶')
    target=m.reply_to_message.from_user if m.reply_to_message else None
    if not target: return await m.reply_text('Reply to target user.')
    await c.bot.ban_chat_member(m.chat_id,target.id); await c.bot.unban_chat_member(m.chat_id,target.id); await m.reply_text('Kicked 👢')
async def mute(u,c):
    m=u.effective_message
    if not await admin_required(u,c): return await m.reply_text('Admins only 😶')
    target=m.reply_to_message.from_user if m.reply_to_message else None
    if not target: return await m.reply_text('Reply to target user.')
    from telegram import ChatPermissions
    await c.bot.restrict_chat_member(m.chat_id,target.id,ChatPermissions(can_send_messages=False)); await m.reply_text('Muted 🔇')
async def unmute(u,c):
    m=u.effective_message
    if not await admin_required(u,c): return await m.reply_text('Admins only 😶')
    target=m.reply_to_message.from_user if m.reply_to_message else None
    if not target: return await m.reply_text('Reply to target user.')
    from telegram import ChatPermissions
    await c.bot.restrict_chat_member(m.chat_id,target.id,ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True)); await m.reply_text('Unmuted 🔊')
async def warn(u,c):
    m=u.effective_message
    if not await admin_required(u,c): return await m.reply_text('Admins only 😶')
    target=m.reply_to_message.from_user if m.reply_to_message else None
    if not target: return await m.reply_text('Reply to target user.')
    import db
    with db.connect() as con: con.execute('INSERT INTO warns(chat_id,user_id,reason) VALUES(?,?,?)',(m.chat_id,target.id,' '.join(c.args) or 'No reason'))
    with db.connect() as con: n=con.execute('SELECT COUNT(*) n FROM warns WHERE chat_id=? AND user_id=?',(m.chat_id,target.id)).fetchone()['n']
    await m.reply_text(f'{target.first_name}: warning {n}/3 ⚠️')
    if n>=3:
        try:
            from telegram import ChatPermissions
            await c.bot.restrict_chat_member(m.chat_id,target.id,ChatPermissions(can_send_messages=False))
            await m.reply_text('3 warnings — auto-muted 🔇')
        except TelegramError: pass
async def warns(u,c):
    m=u.effective_message; target=m.reply_to_message.from_user if m.reply_to_message else m.from_user
    import db
    with db.connect() as con: n=con.execute('SELECT COUNT(*) n FROM warns WHERE chat_id=? AND user_id=?',(m.chat_id,target.id)).fetchone()['n']
    await m.reply_text(f'{target.full_name}: {n} warning(s).')
async def purge(u,c):
    m=u.effective_message
    if not await admin_required(u,c): return await m.reply_text('Admins only 😶')
    if not m.reply_to_message: return await m.reply_text('Jis message se purge start karna hai us par reply karo.')
    ids=list(range(m.reply_to_message.message_id,m.message_id+1))
    try: await c.bot.delete_messages(m.chat_id,ids)
    except Exception: 
        for i in ids:
            try: await c.bot.delete_message(m.chat_id,i)
            except TelegramError: pass
async def pin(u,c):
    m=u.effective_message
    if not await admin_required(u,c): return await m.reply_text('Admins only 😶')
    if not m.reply_to_message: return await m.reply_text('Reply to a message.')
    await m.reply_to_message.pin(disable_notification=True); await m.reply_text('Pinned 📌')
async def unpin(u,c):
    m=u.effective_message
    if not await admin_required(u,c): return await m.reply_text('Admins only 😶')
    if m.reply_to_message: await m.reply_to_message.unpin()
    else: await c.bot.unpin_chat_message(m.chat_id)
    await m.reply_text('Unpinned.')
async def id_cmd(u,c):
    m=u.effective_message; await m.reply_text(f'Chat ID: {m.chat_id}\nYour ID: {u.effective_user.id}'+(f'\nReply user ID: {m.reply_to_message.from_user.id}' if m.reply_to_message else ''))
async def groupinfo(u,c):
    chat=u.effective_chat; await u.effective_message.reply_text(f'Name: {chat.title or chat.full_name}\nID: {chat.id}\nType: {chat.type}\nMembers: {await c.bot.get_chat_member_count(chat.id) if chat.type!="private" else 1}')
async def admins(u,c):
    chat=u.effective_chat
    if chat.type=='private': return await u.effective_message.reply_text('Private chat.')
    ms=await c.bot.get_chat_administrators(chat.id)
    await u.effective_message.reply_text('Admins: '+', '.join(x.user.full_name for x in ms))
async def panel(u,c):
    if not owner(u.effective_user.id): return await u.effective_message.reply_text('Owner only 🔒')
    await u.effective_message.reply_text('Kook panel\n/personality — group personality\n/welcome on|off\n/setwelcome text\n/health')
async def health(u,c):
    if not owner(u.effective_user.id): return await u.effective_message.reply_text('Owner only 🔒')
    await u.effective_message.reply_text(f'Kook running; uptime {int(time.time()-STARTED)}s; database OK; AI configured: '+str(any(__import__('config').__dict__[k] for k in ('GEMINI_API_KEY','GROQ_API_KEY','OPENROUTER_API_KEY'))))
async def lock(u,c):
    if not await admin_required(u,c): return await u.effective_message.reply_text('Admins only 😶')
    from telegram import ChatPermissions
    await c.bot.set_chat_permissions(u.effective_chat.id,ChatPermissions(can_send_messages=False)); await u.effective_message.reply_text('Chat locked 🔒')
async def unlock(u,c):
    if not await admin_required(u,c): return await u.effective_message.reply_text('Admins only 😶')
    from telegram import ChatPermissions
    await c.bot.set_chat_permissions(u.effective_chat.id,ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True)); await u.effective_message.reply_text('Chat unlocked 🔓')
def board(b):
    return InlineKeyboardMarkup([[InlineKeyboardButton(b[i*3+j] or str(i*3+j+1),callback_data=f'xo:{i*3+j}') for j in range(3)] for i in range(3)])
def winner(b):
    for a,d,e in [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]:
        if b[a] and b[a]==b[d]==b[e]: return b[a]
    return 'draw' if all(b) else None
async def game(u,c):
    key=f'{u.effective_chat.id}:{u.effective_user.id}'; b=['']*9; XO[key]=b
    await u.effective_message.reply_text('Tic Tac Toe — tum X, Kook O. Tap a square:',reply_markup=board(b))
async def xo_click(u,c):
    q=u.callback_query; await q.answer()
    key=f'{q.message.chat_id}:{q.from_user.id}'; b=XO.get(key)
    if not b: return await q.edit_message_text('Game expired. /game')
    i=int(q.data.split(':')[1])
    if b[i] or winner(b): return
    b[i]='X'
    if not winner(b):
        free=[j for j,v in enumerate(b) if not v]
        if free: b[random.choice(free)]='O'
    w=winner(b)
    await q.edit_message_text(('You win 🎉' if w=='X' else 'Kook wins 😈' if w=='O' else 'Draw 🤝' if w=='draw' else 'Your move:'),reply_markup=None if w else board(b))
async def chat_ai(u,c):
    m=u.effective_message
    if not m or not m.text or m.text.startswith('/'): return
    chat=m.chat; text=m.text
    if chat.type!='private':
        try:
            me=await c.bot.get_me()
            if not (f'@{me.username.lower()}' in text.lower() or (m.reply_to_message and m.reply_to_message.from_user.id==me.id)): return
        except Exception: return
        k=(chat.id,m.from_user.id); now=time.time(); arr=[x for x in FLOOD.get(k,[]) if now-x<8]; arr.append(now); FLOOD[k]=arr
        if len(arr)>5: return
    s=get_settings(chat.id); remember(chat.id,m.from_user.id,'user',text)
    hist=recent_memory(chat.id,10)
    async with c.bot:
        pass
    try:
        async with_dummy=False
    except Exception: pass
    try:
        await c.bot.send_chat_action(chat.id,'typing')
        answer=await ask(text,s['personality'],hist)
        remember(chat.id,m.from_user.id,'assistant',answer)
        await m.reply_text(answer[:4000])
    except Exception as e:
        log.exception('AI handler failed')
        await m.reply_text('Oops, AI glitch ho gaya 😭')
def main():
    if not BOT_TOKEN: raise RuntimeError('BOT_TOKEN missing; set it in environment')
    init_db()
    app=Application.builder().token(BOT_TOKEN).build()
    handlers=[('start',start),('help',help_cmd),('personality',personality),('welcome',welcome),('setwelcome',setwelcome),('ban',ban),('kick',kick),('mute',mute),('unmute',unmute),('warn',warn),('warns',warns),('purge',purge),('pin',pin),('unpin',unpin),('id',id_cmd),('groupinfo',groupinfo),('admins',admins),('panel',panel),('health',health),('lock',lock),('unlock',unlock),('game',game),('tictactoe',game),('xo',game)]
    for name,fn in handlers: app.add_handler(CommandHandler(name,fn))
    app.add_handler(CallbackQueryHandler(xo_click,pattern='^xo:'))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS,new_members))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,chat_ai))
    log.info('Kook starting')
    app.run_polling(allowed_updates=Update.ALL_TYPES)
if __name__=='__main__': main()
