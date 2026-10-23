import sqlite3
from config import DATABASE_PATH

def connect():
    con=sqlite3.connect(DATABASE_PATH, timeout=20)
    con.row_factory=sqlite3.Row
    return con

def init_db():
    with connect() as c:
        c.executescript('''CREATE TABLE IF NOT EXISTS settings(chat_id INTEGER PRIMARY KEY, personality TEXT DEFAULT 'savage', welcome_on INTEGER DEFAULT 1, welcome_text TEXT DEFAULT 'AYOOO 👀 welcome {first_name} 😭 gc mein bakchodi allowed hai, rules padh lena tho 🫡', flood_limit INTEGER DEFAULT 5); CREATE TABLE IF NOT EXISTS memory(chat_id INTEGER, user_id INTEGER, role TEXT, content TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP); CREATE TABLE IF NOT EXISTS warns(chat_id INTEGER, user_id INTEGER, reason TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);''')

def get_settings(chat_id):
    with connect() as c:
        row=c.execute('SELECT * FROM settings WHERE chat_id=?',(chat_id,)).fetchone()
        if not row:
            c.execute('INSERT OR IGNORE INTO settings(chat_id) VALUES(?)',(chat_id,))
            row=c.execute('SELECT * FROM settings WHERE chat_id=?',(chat_id,)).fetchone()
        return dict(row)

def set_setting(chat_id,key,value):
    allowed={'personality','welcome_on','welcome_text','flood_limit'}
    if key not in allowed: raise ValueError('invalid setting')
    with connect() as c:
        c.execute('INSERT OR IGNORE INTO settings(chat_id) VALUES(?)',(chat_id,))
        c.execute(f'UPDATE settings SET {key}=? WHERE chat_id=?',(value,chat_id))

def remember(chat_id,user_id,role,content):
    with connect() as c:
        c.execute('INSERT INTO memory(chat_id,user_id,role,content) VALUES(?,?,?,?)',(chat_id,user_id,role,content[:2000]))
        c.execute('DELETE FROM memory WHERE rowid IN (SELECT rowid FROM memory WHERE chat_id=? ORDER BY rowid DESC LIMIT -1 OFFSET 40)',(chat_id,))

def recent_memory(chat_id,limit=12):
    with connect() as c:
        rows=c.execute('SELECT role,content FROM memory WHERE chat_id=? ORDER BY rowid DESC LIMIT ?',(chat_id,limit)).fetchall()
        return list(reversed([dict(r) for r in rows]))
