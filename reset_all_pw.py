import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('egocrypto.db')
c = conn.cursor()

new_pass = 'admin123'
hashed = generate_password_hash(new_pass)

try:
    c.execute("SELECT id, username FROM users")
    users = c.fetchall()
    print(f"--- User စုစုပေါင်း ({len(users)}) ယောက် ---")
    
    c.execute("UPDATE users SET password_hash=?", (hashed,))
    conn.commit()
    print(f"\n✅ User အားလုံးရဲ့ Password ကို '{new_pass}' လို့ ပြောင်းပြီးပါပြီ။")
except Exception as e:
    print("Error:", e)

conn.close()
