import re

with open('pg_sqlite_shim.py', 'r') as f:
    content = f.read()

# Egocrypto အတွက် အသစ်တွေ
new_host = 'ep-crimson-term-b8rsm466-pooler.c-14.us-east-1.aws.neon.tech'
new_pass = 'npg_UNM4lncbXf0k'

# Host ကို အစားထိုးမယ်
content = re.sub(r"'host':\s*os\.environ\.get\('PG_HOST',\s*'[^']*'\)", f"'host': os.environ.get('PG_HOST', '{new_host}')", content)

# Password ကို အစားထိုးမယ်
content = re.sub(r"'password':\s*os\.environ\.get\('PG_PASSWORD',\s*'[^']*'\)", f"'password': os.environ.get('PG_PASSWORD', '{new_pass}')", content)

with open('pg_sqlite_shim.py', 'w') as f:
    f.write(content)

print("✅ ဖိုင်ကို အောင်မြင်စွာ ပြင်ဆင်ပြီးပါပြီ။")
