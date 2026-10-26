import sqlite3
import pg8000.dbapi as pg
import sys

NEON_HOST = 'ep-crimson-term-b8rsm466-pooler.c-14.us-east-1.aws.neon.tech'

if len(sys.argv) < 2:
    print("❌ Error: Password မပါလာပါ။")
    print("ဥပမာ - python3 migrate_egocrypto.py သင့်Password")
    sys.exit(1)

NEON_PASSWORD = sys.argv[1]

print("Connecting to SQLite...")
sq_conn = sqlite3.connect('egocrypto.db')
sq_c = sq_conn.cursor()
sq_c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in sq_c.fetchall() if t[0] != 'sqlite_sequence']
print(f"Found {len(tables)} tables.")

print("Connecting to Neon Postgres...")
pg_conn = pg.connect(
    host=NEON_HOST,
    database='neondb',
    user='neondb_owner',
    password=NEON_PASSWORD,
    ssl_context=True
)
pg_c = pg_conn.cursor()
print("✅ Connected to Neon.")

for table in tables:
    try:
        print(f"\n--- Processing {table} ---")
        # 1. Table Schema ကို ဖတ်မယ်
        sq_c.execute(f"PRAGMA table_info({table})")
        columns = sq_c.fetchall()
        
        # 2. Postgres အတွက် CREATE TABLE စာသား ဖန်တီးမယ်
        col_defs = []
        for col in columns:
            name = col[1]
            type_ = col[2].upper()
            is_pk = col[5] > 0
            
            pg_type = "TEXT"
            if "INT" in type_:
                pg_type = "INTEGER"
                if is_pk and name == "id":
                    pg_type = "SERIAL PRIMARY KEY"
            elif "CHAR" in type_ or "TEXT" in type_ or "CLOB" in type_:
                pg_type = "TEXT"
            elif "REAL" in type_ or "DOUB" in type_ or "FLOA" in type_:
                pg_type = "DOUBLE PRECISION"
            elif "NUM" in type_ or "DEC" in type_:
                pg_type = "NUMERIC"
                
            if is_pk and name != "id":
                pg_type += " PRIMARY KEY"
                
            col_defs.append(f'"{name}" {pg_type}')

        create_sql = f'CREATE TABLE IF NOT EXISTS "{table}" ({", ".join(col_defs)});'
        pg_c.execute(create_sql)
        pg_conn.commit()
        print(f"✅ Table {table} created/verified.")
        
        # 3. Data တွေ ထည့်မယ်
        sq_c.execute(f"SELECT * FROM {table}")
        rows = sq_c.fetchall()
        if rows:
            cols_str = ','.join([f'"{c[1]}"' for c in columns])
            placeholders = ','.join(['%s'] * len(columns))
            insert_sql = f'INSERT INTO "{table}" ({cols_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'
            
            success = 0
            for row in rows:
                try:
                    pg_c.execute(insert_sql, row)
                    success += 1
                except Exception as e:
                    pg_conn.rollback() # Error တက်ရင် ပြန် Rollback လုပ်မယ်
            pg_conn.commit()
            print(f"✅ {table}: {success}/{len(rows)} rows migrated.")
        else:
            print(f"⚠️ {table}: No data to migrate.")
            
    except Exception as e:
        pg_conn.rollback()
        print(f"❌ Error on {table}: {e}")

sq_conn.close()
pg_conn.close()
print("\n🎉 DONE! Data migration completed.")
