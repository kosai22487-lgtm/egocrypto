import os
import sqlite3
import datetime
import random
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import time
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random as random_module

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'my-super-secret-key-12345')

import os
DATABASE_URL = os.environ.get('DATABASE_URL', '')
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras
    print(f"✅ PostgreSQL mode: {DATABASE_URL.split('@')[-1]}")
else:
    DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'egocrypto.db')
    print(f"✅ SQLite mode: {DB_NAME}")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Predefined list of supported coins (symbol, name)
SUPPORTED_COINS = [
    ('BTC', 'Bitcoin'), ('ETH', 'Ethereum'), ('USDT', 'Tether'), ('SOL', 'Solana'),
    ('BNB', 'BNB'), ('XRP', 'XRP'), ('ADA', 'Cardano'), ('DOGE', 'Dogecoin'),
    ('DOT', 'Polkadot'), ('MATIC', 'Polygon')
]

# AI Arbitrage Plans
PLAN_DATA = {
    '1': {'name': 'Smart Plan A', 'days': '1 Day', 'quantity': '$500-2000', 'income': '1.60-1.70%', 'limit': 2},
    '3': {'name': 'Smart Plan B', 'days': '3 Day', 'quantity': '$2001-10000', 'income': '1.90-2.10%', 'limit': 2},
    '5': {'name': 'Smart Plan C', 'days': '5 Day', 'quantity': '$10001-50000', 'income': '2.20-2.70%', 'limit': 2},
    '7': {'name': 'Smart Plan D', 'days': '7 Day', 'quantity': '$50001-200000', 'income': '2.80-3.30%', 'limit': 3},
    '10': {'name': 'Smart Plan E', 'days': '10 Day', 'quantity': '$200001-500000', 'income': '3.50-5.50%', 'limit': 5},
    '15': {'name': 'Smart Plan VIP', 'days': '15 Day', 'quantity': '$500001-3000000', 'income': '5.50-8.50%', 'limit': 7},
    '20': {'name': 'Crypto pulse Max', 'days': '20 Day', 'quantity': '$3000001-10000000', 'income': '6.50-10.00%', 'limit': 9}
}


def sync_balance(user_id):
    """Sync all balance fields to match wallet_balances"""
    try:
        conn = get_db()
        conn.execute('PRAGMA busy_timeout = 10000;')
        cur = conn.cursor()
        
        wallet = cur.execute("SELECT balance FROM wallet_balances WHERE user_id=? AND coin='USDT'", (user_id,)).fetchone()
        wallet_bal = wallet['balance'] if wallet else 0
        
        cur.execute('UPDATE users SET usdt_balance=?, balance=? WHERE id=?', (wallet_bal, wallet_bal, user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Sync error: {e}")


def get_db():
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        conn.cursor_factory = psycopg2.extras.DictCursor
        return conn
    else:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA busy_timeout = 30000;')
        return conn




def is_assigned_to_admin(conn, user_id, admin_id, admin_role):
    if admin_role == 'admin':
        return True
    row = conn.execute('SELECT assigned_admin_id FROM users WHERE id=?', (user_id,)).fetchone()
    return row and row['assigned_admin_id'] == admin_id

def get_forced_result(user_id):
    conn = get_db()
    row = conn.execute('SELECT forced_result FROM admin_settings WHERE user_id=?', (user_id,)).fetchone()
    conn.close()
    return row['forced_result'] if row else 'auto'


def send_verification_email(to_email, code):
    sender_email = "egocryptosupport@gmail.com"
    sender_password = "mjwftmdvwrcfbjwm"
    
    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = "Egocrypto - Verification Code"
    
    html_body = f'<h2>Your verification code: {code}</h2>'
    msg.attach(MIMEText(html_body, "html"))
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


def init_db():
    conn = get_db()
    cur = conn.cursor()
    

    
    cur.execute('''CREATE TABLE IF NOT EXISTS active_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        plan_name TEXT,
        escrow_amount REAL,
        daily_income_percent REAL,
        total_days INTEGER,
        start_time TEXT,
        end_time TEXT,
        status TEXT DEFAULT 'active',
        total_income REAL DEFAULT 0.0,
        created_at TEXT
    )''')


    # Add professional profile fields if not exist
    try:
        cur.execute("ALTER TABLE users ADD COLUMN real_name TEXT DEFAULT ''")
    except:
        pass
    try:
        cur.execute("ALTER TABLE users ADD COLUMN phone TEXT DEFAULT ''")
    except:
        pass
    try:
        cur.execute("ALTER TABLE users ADD COLUMN city TEXT DEFAULT ''")
    except:
        pass
    try:
        cur.execute("ALTER TABLE users ADD COLUMN country TEXT DEFAULT ''")
    except:
        pass
    try:
        cur.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT DEFAULT ''")
    except:
        pass

    cur.execute('PRAGMA journal_mode=WAL;')
    cur.fetchall()

    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        balance REAL DEFAULT 0.0,
        btc_balance REAL DEFAULT 0.0,
        eth_balance REAL DEFAULT 0.0,
        usdt_balance REAL DEFAULT 0.0,
        status TEXT DEFAULT 'Offline',
        ip_address TEXT DEFAULT '127.0.0.1',
        login_time TEXT DEFAULT '',
        last_online TEXT DEFAULT '',
        deposit_limit REAL DEFAULT 10000.0,
        withdraw_limit REAL DEFAULT 5000.0
    )''')

    # escrow_balance column ထည့်ပါ (ရှိပြီးသား DB တွေအတွက်)
    try:
        cur.execute("ALTER TABLE users ADD COLUMN escrow_balance REAL DEFAULT 0.0")
    except:
        pass

    for col_name, col_def in [
        ("account_status", "TEXT DEFAULT 'active'"),
        ("assigned_admin_id", "INTEGER DEFAULT 0"),
        ("passcode_hash", "TEXT DEFAULT ''"),
        ("anti_phishing_code", "TEXT DEFAULT ''"),
        ("kyc_status", "TEXT DEFAULT 'not_submitted'"),
        ("kyc_doc_path", "TEXT DEFAULT ''"),
        ("kyc_submitted_at", "TEXT DEFAULT ''"),
        ("kyc_full_name", "TEXT DEFAULT ''"),
        ("kyc_dob", "TEXT DEFAULT ''"),
        ("kyc_nationality", "TEXT DEFAULT ''"),
        ("kyc_address_line1", "TEXT DEFAULT ''"),
        ("kyc_address_city", "TEXT DEFAULT ''"),
        ("kyc_address_state", "TEXT DEFAULT ''"),
        ("kyc_address_postal", "TEXT DEFAULT ''"),
        ("kyc_address_country", "TEXT DEFAULT ''"),
        ("kyc_id_type", "TEXT DEFAULT ''"),
        ("kyc_id_number", "TEXT DEFAULT ''"),
        ("kyc_id_front_path", "TEXT DEFAULT ''"),
        ("kyc_id_back_path", "TEXT DEFAULT ''"),
        ("kyc_selfie_path", "TEXT DEFAULT ''"),
        ("referral_code", "TEXT DEFAULT ''"),
    ]:
        try:
            sql = "ALTER TABLE users ADD COLUMN " + col_name + " " + col_def
            cur.execute(sql)
        except:
            pass


    # Set user ID starting from 87422
    cur.execute("INSERT INTO sqlite_sequence (name, seq) SELECT 'users', 87421 WHERE NOT EXISTS (SELECT 1 FROM sqlite_sequence WHERE name='users')")

    cur.execute('''CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        symbol TEXT,
        trade_type TEXT,
        amount REAL,
        price REAL,
        duration INTEGER,
        profit_percent REAL,
        status TEXT DEFAULT 'pending',
        result TEXT DEFAULT 'pending',
        created_at TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS admin_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        forced_result TEXT DEFAULT 'auto'
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT,
        amount REAL,
        description TEXT,
        created_at TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS wallet_balances (
        user_id INTEGER,
        coin TEXT,
        balance REAL DEFAULT 0.0,
        PRIMARY KEY (user_id, coin)
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS deposit_addresses (
        coin TEXT PRIMARY KEY,
        address TEXT NOT NULL
    )''')
    cur.execute('INSERT OR IGNORE INTO deposit_addresses (coin, address) VALUES ("BTC", "bc1qvzxcctt3kd6kvjqdg24rqfzytdncyc4hul8g46")')
    cur.execute('INSERT OR IGNORE INTO deposit_addresses (coin, address) VALUES ("ETH", "0xDAaf41254f7cCfD4bCE565EE354DfDe225c5E74")')
    cur.execute('INSERT OR IGNORE INTO deposit_addresses (coin, address) VALUES ("USDT", "0xDAaf41254f7cCfD4bCE565EE354DfDe225c5E74")')

    cur.execute('''CREATE TABLE IF NOT EXISTS deposit_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        coin TEXT,
        tx_hash TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS withdraw_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        address TEXT,
        coin TEXT DEFAULT 'USDT',
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT DEFAULT ''
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS referral_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        admin_id INTEGER,
        active INTEGER DEFAULT 1,
        created_at TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        sender TEXT,
        message TEXT,
        created_at TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS admin_chat_seen (
        user_id INTEGER PRIMARY KEY,
        last_seen_chat_id INTEGER DEFAULT 0
    )''')

    conn.commit()
    conn.close()



import time
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random as random_module

def parse_plan_range(quantity_str):
    numbers = quantity_str.replace('$', '').replace(',', '').split('-')
    if len(numbers) == 2:
        return int(numbers[0]), int(numbers[1])
    return 0, 0

def process_active_plans():
    now = datetime.now()
    conn = get_db()
    active_plans = conn.execute("SELECT * FROM active_plans WHERE status='active'").fetchall()
    
    for plan in active_plans:
        try:
            start_time = datetime.strptime(plan['start_time'], "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(plan['end_time'], "%Y-%m-%d %H:%M:%S")
            daily_income_amount = round(plan['escrow_amount'] * (plan['daily_income_percent'] / 100), 2)
            total_days = plan['total_days']
            
            # Count how many days have passed
            effective_now = min(now, end_time)
            elapsed_days = max(0, (effective_now - start_time).days)
            
            # Count credited days from transactions (not from total_income)
            tx_count = conn.execute("SELECT COUNT(*) as cnt FROM transactions WHERE user_id=? AND type='daily_income' AND description LIKE ?", 
                                    (plan['user_id'], f'%{plan["plan_name"]}%')).fetchone()['cnt']
            
            days_to_credit = max(0, min(elapsed_days - tx_count, total_days - tx_count))
            
            if days_to_credit > 0:
                cur = conn.cursor()
                for _ in range(days_to_credit):
                    cur.execute('UPDATE users SET escrow_balance = escrow_balance + ? WHERE id=?', (daily_income_amount, plan['user_id']))
                    cur.execute('UPDATE active_plans SET total_income = total_income + ? WHERE id=?', (daily_income_amount, plan['id']))
                    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
                    cur.execute('INSERT INTO transactions (user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)',
                                (plan['user_id'], 'daily_income', daily_income_amount, f'Daily income from {plan["plan_name"]}', now_str))
                conn.commit()
            
            # Plan completed - return principal
            if now >= end_time:
                principal = plan['escrow_amount']
                cur = conn.cursor()
                cur.execute('UPDATE users SET escrow_balance = escrow_balance + ? WHERE id=?', (principal, plan['user_id']))
                cur.execute('UPDATE active_plans SET status=? WHERE id=?', ('completed', plan['id']))
                now_str = now.strftime("%Y-%m-%d %H:%M:%S")
                cur.execute('INSERT INTO transactions (user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)',
                            (plan['user_id'], 'plan_completed', principal, f'Plan completed: {plan["plan_name"]}', now_str))
                conn.commit()
        except Exception as e:
            print(f"Error processing plan {plan['id']}: {e}")
    conn.close()
def ensure_wallet_balances(user_id):
    conn = get_db()
    cur = conn.cursor()
    for symbol, _ in SUPPORTED_COINS:
        cur.execute('INSERT OR IGNORE INTO wallet_balances (user_id, coin, balance) VALUES (?, ?, 0.0)', (user_id, symbol))
    conn.commit()
    conn.close()


class User(UserMixin):
    def __init__(self, row):
        self.id = row['id']
        self.username = row['username']
        self.email = row['email']
        self.role = row['role']
        self.balance = row['balance']
        self.btc_balance = row['btc_balance']
        self.eth_balance = row['eth_balance']
        self.usdt_balance = row['usdt_balance']
        self.escrow_balance = row['escrow_balance'] if 'escrow_balance' in row.keys() else 0.0
        self.account_status = row['account_status'] if 'account_status' in row.keys() else 'active'
        self.kyc_status = row['kyc_status'] if 'kyc_status' in row.keys() else 'not_submitted'
        self.kyc_doc_path = row['kyc_doc_path'] if 'kyc_doc_path' in row.keys() else ''


@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    row = conn.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    conn.close()
    return User(row) if row else None


# ==================== AUTH ROUTES ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        conn = get_db()
        row = conn.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
        if row and check_password_hash(row['password_hash'], password):
            # Check if 2FA is enabled
            twofa_enabled = row['twofa_enabled'] if 'twofa_enabled' in row.keys() else 0
            
            if twofa_enabled:
                # Generate and send 2FA code
                code = str(random_module.randint(100000, 999999))
                conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('verify_code_' || ?, ?)", (str(row['id']), code))
                conn.commit()
                conn.close()
                
                send_verification_email(row['email'], code)
                
                return jsonify({'success': True, 'needs_2fa': True, 'user_id': row['id'], 'debug_code': code})
            else:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn.execute('UPDATE users SET status=?, ip_address=?, login_time=?, last_online=? WHERE id=?',
                             ('Online', request.remote_addr, now_str, now_str, row['id']))
                conn.commit()
                conn.close()
                login_user(User(row))
                ensure_wallet_balances(row['id'])
                return redirect(url_for('index'))
        conn.close()
        flash('Invalid credentials.', 'error')
    return render_template('login.html')


@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    country = request.form.get('country', '').strip()
    phone = request.form.get('phone', '').strip()
    referral_code = request.form.get('referral_code', '').strip()
    city = request.form.get('city', '').strip()
    real_name = request.form.get('real_name', '').strip()

    if len(password) < 8:
        flash('Password must be 8+ characters.', 'error')
        return redirect(url_for('login'))

    # Check if subadmin system is enabled
    subadmin_enabled = conn.execute("SELECT value FROM settings WHERE key='subadmin_system_enabled'").fetchone()
    subadmin_on = subadmin_enabled['value'] == '1' if subadmin_enabled else True
    
    if subadmin_on and not referral_code:
        flash('Referral code is required to register.', 'error')
        return redirect(url_for('login'))

    # Validate referral code exists
    conn_check = get_db()
    ref_exists = conn_check.execute('SELECT admin_id FROM referral_codes WHERE code=? AND active=1', (referral_code,)).fetchone()
    conn_check.close()
    if not ref_exists:
        flash('Invalid referral code.', 'error')
        return redirect(url_for('login'))
    assigned_admin_id = ref_exists['admin_id']

    conn = get_db()
    
    # Find which sub admin owns this referral code
    ref_row = conn.execute('SELECT admin_id FROM referral_codes WHERE code=? AND active=1', (referral_code,)).fetchone()
    if not ref_row:
        conn.close()
        flash('Invalid referral code.', 'error')
        return redirect(url_for('login'))
    
    assigned_admin_id = ref_row['admin_id']
    
    if conn.execute('SELECT id FROM users WHERE username=? OR email=?', (username, email)).fetchone():
        conn.close()
        flash('Username/Email exists.', 'error')
        return redirect(url_for('login'))

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.cursor()
    # Initialize wallet_balances for new user
    for coin_sym in ['BTC', 'ETH', 'USDT', 'BNB', 'SOL', 'ADA', 'XRP', 'DOGE', 'DOT', 'MATIC']:
        cur.execute('INSERT OR IGNORE INTO wallet_balances (user_id, coin, balance) VALUES (?, ?, 0.0)', (user_id, coin_sym))
    
    cur.execute('''INSERT INTO users (username, email, password_hash, balance, btc_balance, eth_balance, usdt_balance, status, ip_address, login_time, last_online, phone, country, register_date, created_at), assigned_admin_id
                   VALUES (?, ?, ?, 0.0, 0.0, 0.0, 0.0, 'Online', ?, ?, ?, ?, ?, ?, ?, ?)''', 
                (username, email, generate_password_hash(password, method='scrypt'), request.remote_addr, now_str, now_str, phone, country, now_str, now_str, assigned_admin_id))
    user_id = cur.lastrowid
    if city or real_name:
        conn.execute('UPDATE users SET city=?, real_name=? WHERE id=?', (city, real_name, user_id))
        conn.commit()
    conn.commit()
    # Fetch user row for login
    user_row = conn.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    conn.close()
    ensure_wallet_balances(user_id)
    login_user(User(user_row))
    flash('Account created and logged in successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    conn = get_db()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute('UPDATE users SET status=?, last_online=? WHERE id=?',
                 ('Offline', now_str, current_user.id))
    conn.commit()
    conn.close()
    logout_user()
    return redirect(url_for('login'))


# ==================== PAGE ROUTES ====================

@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/trading')
@login_required
def trading_page():
    return render_template('partials/trading.html')


@app.route('/markets')
@login_required
def markets_page():
    return render_template('partials/markets.html')


@app.route('/notifications')
@login_required
def notifications_page():
    return render_template('partials/notifications.html')


@app.route('/ai-arbitrage')
@login_required
def ai_arbitrage():
    return render_template('partials/ai_arbitrage.html', PLAN_DATA=PLAN_DATA)


@app.route('/arbitrage/plan/<plan_id>')
@login_required
def arbitrage_plan(plan_id):
    plan = PLAN_DATA.get(plan_id)
    if not plan:
        return 'Plan not found', 404
    return render_template('partials/plan_detail.html', plan=plan)


@app.route('/help')
def help_page():
    return render_template('help.html')


@app.route('/convert')
@login_required
def convert_page():
    return render_template('convert.html')


# ==================== ADMIN ROUTES ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login_page():
    if request.method == 'POST':
        user = request.form.get('username', '').strip()
        pwd = request.form.get('password', '').strip()
        conn = get_db()
        row = conn.execute('SELECT * FROM users WHERE username=? AND role IN ("admin", "subadmin")', (user,)).fetchone()
        if row and check_password_hash(row['password_hash'], pwd):
            session['is_admin_logged'] = True
            session['admin_user_id'] = row['id']
            session['admin_role'] = row['role']
            conn.close()
            return redirect(url_for('admin_dashboard'))
        conn.close()
        flash('Invalid Admin Credentials', 'error')
    return render_template('admin_login.html')


@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('is_admin_logged'):
        return redirect(url_for('admin_login_page'))

    admin_id = session.get('admin_user_id')
    admin_role = session.get('admin_role', 'admin')

    conn = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('user_id')

        # Ensure subadmins only manage their assigned customers
        if admin_role == 'subadmin':
            if user_id:
                # Verify target user is assigned to this subadmin
                assigned = conn.execute('SELECT assigned_admin_id FROM users WHERE id=?', (user_id,)).fetchone()
                if not assigned or assigned['assigned_admin_id'] != admin_id:
                    conn.close()
                    return redirect(url_for('admin_dashboard'))

        if action in ['deposit', 'withdraw']:
            try:
                amt = float(request.form.get('amount', 0))
                cur = conn.cursor()
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if action == 'deposit':
                    cur.execute('UPDATE users SET balance = balance + ?, usdt_balance = usdt_balance + ? WHERE id=?', (amt, amt, user_id))
                    cur.execute('INSERT INTO transactions (user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)',
                                (user_id, 'deposit', amt, f'Deposit of ${amt:.2f}', now_str))
                    cur.execute('INSERT INTO wallet_balances (user_id, coin, balance) VALUES (?, ?, ?) ON CONFLICT(user_id, coin) DO UPDATE SET balance = balance + ?',
                                (user_id, 'USDT', amt, amt))
                elif action == 'withdraw':
                    cur.execute('UPDATE users SET balance = MAX(0, balance - ?), usdt_balance = MAX(0, usdt_balance - ?) WHERE id=?', (amt, amt, user_id))
                    cur.execute('INSERT INTO transactions (user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)',
                                (user_id, 'withdrawal', -amt, f'Withdrawal ${amt:.2f}', now_str))
                    cur.execute('INSERT INTO wallet_balances (user_id, coin, balance) VALUES (?, ?, ?) ON CONFLICT(user_id, coin) DO UPDATE SET balance = balance - ?',
                                (user_id, 'USDT', -amt, amt))
                conn.commit()
            except ValueError:
                pass

        if action in ['add_balance', 'take_balance']:
            try:
                amt = float(request.form.get('amount', 0))
                cur = conn.cursor()
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                if action == 'add_balance':
                    # Add to wallet_balances and sync
                    wallet = cur.execute("SELECT balance FROM wallet_balances WHERE user_id=? AND coin='USDT'", (user_id,)).fetchone()
                    wallet_bal = wallet['balance'] if wallet else 0
                    new_bal = round(wallet_bal + amt, 2)
                    
                    cur.execute("UPDATE wallet_balances SET balance=? WHERE user_id=? AND coin='USDT'", (new_bal, user_id))
                    cur.execute('UPDATE users SET usdt_balance=?, balance=? WHERE id=?', (new_bal, new_bal, user_id))
                    cur.execute('INSERT INTO transactions (user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)',
                                (user_id, 'deposit', amt, 'Deposit', now_str))
                elif action == 'take_balance':
                    wallet = cur.execute("SELECT balance FROM wallet_balances WHERE user_id=? AND coin='USDT'", (user_id,)).fetchone()
                    wallet_bal = wallet['balance'] if wallet else 0
                    
                    if wallet_bal < amt:
                        conn.close()
                        return redirect(url_for('admin_dashboard'))
                    
                    new_bal = round(wallet_bal - amt, 2)
                    
                    cur.execute("UPDATE wallet_balances SET balance=? WHERE user_id=? AND coin='USDT'", (new_bal, user_id))
                    cur.execute('UPDATE users SET usdt_balance=?, balance=? WHERE id=?', (new_bal, new_bal, user_id))
                    cur.execute('INSERT INTO transactions (user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)',
                                (user_id, 'withdrawal', -amt, 'Withdrawal', now_str))
                
                conn.commit()
            except Exception as e:
                print(f"Balance error: {e}")
        elif action == 'set_result':
            forced_res = request.form.get('forced_result', 'auto')
            existing = conn.execute('SELECT id FROM admin_settings WHERE user_id=?', (user_id,)).fetchone()
            if existing:
                conn.execute('UPDATE admin_settings SET forced_result=? WHERE user_id=?', (forced_res, user_id))
            else:
                conn.execute('INSERT INTO admin_settings (user_id, forced_result) VALUES (?, ?)', (user_id, forced_res))
            conn.commit()

        elif action == 'reset_password':
            new_pass = request.form.get('new_password', '').strip()
            if len(new_pass) >= 6:
                hashed = generate_password_hash(new_pass, method='scrypt')
                conn.execute('UPDATE users SET password_hash = ? WHERE id=?', (hashed, user_id))
                conn.commit()

        elif action == 'reset_passcode':
            new_passcode = request.form.get('new_passcode', '').strip()
            if new_passcode.isdigit() and 4 <= len(new_passcode) <= 6:
                passcode_hash = generate_password_hash(new_passcode, method='scrypt')
                conn.execute('UPDATE users SET passcode_hash=? WHERE id=?', (passcode_hash, user_id))
                conn.commit()

        elif action == 'freeze_account':
            conn.execute("UPDATE users SET account_status='frozen' WHERE id=?", (user_id,))
            conn.commit()

        elif action == 'unfreeze_account':
            conn.execute("UPDATE users SET account_status='active' WHERE id=?", (user_id,))
            conn.commit()

        elif action == 'delete_account':
            cur = conn.cursor()
            for table in ['transactions','active_plans','trades','chat_messages','deposit_requests','withdraw_requests','wallet_balances','admin_settings']:
                cur.execute(f"DELETE FROM {table} WHERE user_id=?", (user_id,))
            cur.execute("DELETE FROM users WHERE id=?", (user_id,))
            conn.commit()

        elif action == 'update_address':
            if admin_role == 'admin':  # Only super admin
                coin = request.form.get('coin')
                new_addr = request.form.get('new_address', '').strip()
                if coin in ('BTC', 'ETH', 'USDT') and new_addr:
                    conn.execute('INSERT OR REPLACE INTO deposit_addresses (coin, address) VALUES (?, ?)', (coin, new_addr))
                    conn.commit()

        elif action == 'create_subadmin':
            if admin_role == 'admin':  # Only super admin
                new_username = request.form.get('new_username', '').strip()
                new_email = request.form.get('new_email', '').strip()
                new_password = request.form.get('new_password', '').strip()
                if new_username and new_email and len(new_password) >= 6:
                    existing = conn.execute('SELECT id FROM users WHERE username=? OR email=?', (new_username, new_email)).fetchone()
                    if not existing:
                        hashed = generate_password_hash(new_password, method='scrypt')
                        cur = conn.cursor()
                        cur.execute('INSERT INTO users (username, email, password_hash, role, balance, usdt_balance, escrow_balance, account_status) VALUES (?, ?, ?, "subadmin", 0, 0, 0, "active")',
                                     (new_username, new_email, hashed))
                        subadmin_id = cur.lastrowid
                        
                        # Auto-generate referral code
                        import random as _random
                        auto_code = 'EGO' + str(_random.randint(100000, 999999))
                        cur.execute('INSERT INTO referral_codes (code, admin_id, active, created_at) VALUES (?, ?, 1, ?)',
                                    (auto_code, subadmin_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()

        elif action == 'reset_subadmin_password':
            sub_id = request.form.get('subadmin_id')
            new_pass = request.form.get('new_subadmin_password', '').strip()
            if sub_id and len(new_pass) >= 6:
                hashed = generate_password_hash(new_pass, method='scrypt')
                conn.execute('UPDATE users SET password_hash=? WHERE id=? AND role="subadmin"', (hashed, sub_id))
                conn.commit()

        elif action == 'toggle_subadmin_system':
            if admin_role == 'admin':
                current = conn.execute("SELECT value FROM settings WHERE key='subadmin_system_enabled'").fetchone()
                new_val = '0' if current and current['value'] == '1' else '1'
                conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('subadmin_system_enabled', ?)", (new_val,))
                conn.commit()

        elif action == 'delete_subadmin':
            if admin_role == 'admin':
                sub_id = request.form.get('subadmin_id')
                cur = conn.cursor()
                cur.execute('UPDATE users SET account_status="deleted" WHERE id=? AND role="subadmin"', (sub_id,))
                # Or hard delete
                # cur.execute('DELETE FROM users WHERE id=? AND role="subadmin"', (sub_id,))
                conn.commit()

        elif action == 'create_referral_code':
            if admin_role == 'admin':
                code = request.form.get('referral_code', '').strip()
                subadmin_id = request.form.get('subadmin_id')
                if code and subadmin_id:
                    conn.execute('INSERT OR IGNORE INTO referral_codes (code, admin_id, active, created_at) VALUES (?, ?, 1, ?)',
                                 (code, subadmin_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()

        elif action == 'delete_referral_code':
            if admin_role == 'admin':
                ref_id = request.form.get('ref_id')
                conn.execute('DELETE FROM referral_codes WHERE id=?', (ref_id,))
                conn.commit()

        conn.close()
        return redirect(url_for('admin_dashboard'))

    # GET request
    if admin_role == 'admin':
        users = conn.execute('''
            SELECT u.*,
                   (SELECT COUNT(*) FROM trades WHERE user_id = u.id) as trade_count,
                   (SELECT COUNT(*) FROM active_plans WHERE user_id = u.id AND status='active') as active_positions,
                   (SELECT COALESCE(SUM(total_income), 0) FROM active_plans WHERE user_id = u.id) as total_arbitrage_income,
                   u.escrow_balance as total_escrow_balance,
                   COALESCE((SELECT forced_result FROM admin_settings WHERE user_id = u.id), 'auto') as forced_result
            FROM users u
        ''').fetchall()
    else:
        # Sub-admin sees only their assigned customers
        users = conn.execute('''
            SELECT u.*,
                   (SELECT COUNT(*) FROM trades WHERE user_id = u.id) as trade_count,
                   (SELECT COUNT(*) FROM active_plans WHERE user_id = u.id AND status='active') as active_positions,
                   (SELECT COALESCE(SUM(total_income), 0) FROM active_plans WHERE user_id = u.id) as total_arbitrage_income,
                   u.escrow_balance as total_escrow_balance,
                   COALESCE((SELECT forced_result FROM admin_settings WHERE user_id = u.id), 'auto') as forced_result
            FROM users u
            WHERE u.assigned_admin_id = ?
        ''', (admin_id,)).fetchall()

    # KYC pending users
    kyc_pending = conn.execute("SELECT id, username, email, real_name, kyc_dob, kyc_nationality, kyc_address_line1, kyc_address_city, kyc_address_state, kyc_address_postal, kyc_address_country, kyc_id_type, kyc_id_number, kyc_id_front_path, kyc_id_back_path, kyc_selfie_path, kyc_doc_path, kyc_submitted_at, kyc_status FROM users WHERE kyc_status IN ('pending', 'approved') AND kyc_submitted_at != '' ORDER BY kyc_submitted_at DESC").fetchall()
    
    debit_cards = conn.execute("SELECT dc.*, u.username, u.id as uid FROM debit_cards dc JOIN users u ON dc.user_id = u.id ORDER BY dc.id DESC").fetchall()
    
    bank_accounts = conn.execute("SELECT ba.*, u.username, u.id as uid FROM bank_accounts ba JOIN users u ON ba.user_id = u.id ORDER BY ba.id DESC").fetchall()

    deposit_requests = conn.execute('SELECT * FROM deposit_requests ORDER BY id DESC LIMIT 200').fetchall()
    withdraw_requests = conn.execute('SELECT * FROM withdraw_requests ORDER BY id DESC LIMIT 200').fetchall()
    addresses = {row['coin']: row['address'] for row in conn.execute('SELECT coin, address FROM deposit_addresses').fetchall()}

    # Get sub-admins and referral codes if super admin
    subadmins = []
    referral_codes = []
    if admin_role == 'admin':
        subadmins = conn.execute('SELECT id, username, email FROM users WHERE role="subadmin"').fetchall()
        referral_codes = conn.execute('SELECT * FROM referral_codes').fetchall()
    
    settings = {row['key']: row['value'] for row in conn.execute('SELECT key, value FROM settings').fetchall()}

    conn.close()
    return render_template('admin.html',
                           users=users,
                           addresses=addresses,
                           deposit_requests=deposit_requests,
                           withdraw_requests=withdraw_requests,
                           is_superadmin=(admin_role == 'admin'),
                           subadmins=subadmins,
                           settings=settings,
                           referral_codes=referral_codes,
                           kyc_pending=kyc_pending,
                           debit_cards=debit_cards,
                           bank_accounts=bank_accounts)

@app.route('/admin/approve-deposit/<int:req_id>', methods=['POST'])
def admin_approve_deposit(req_id):
    if not session.get('is_admin_logged'):
        return redirect(url_for('admin_login_page'))
    conn = get_db()
    admin_id = session.get('admin_user_id')
    admin_role = session.get('admin_role', 'admin')
    req = conn.execute('SELECT * FROM deposit_requests WHERE id=? AND status=?', (req_id, 'pending')).fetchone()
    if not req:
        conn.close()
        return redirect(url_for('admin_dashboard'))
    if not is_assigned_to_admin(conn, req['user_id'], admin_id, admin_role):
        conn.close()
        return redirect(url_for('admin_dashboard'))
    user_id = req['user_id']
    amount = req['amount']
    coin = req['coin']
    conn.execute('UPDATE users SET balance = balance + ?, usdt_balance = usdt_balance + ? WHERE id=?', (amount, amount, user_id))
    conn.execute('INSERT INTO wallet_balances (user_id, coin, balance) VALUES (?, ?, ?) ON CONFLICT(user_id, coin) DO UPDATE SET balance = balance + ?',
                 (user_id, coin, amount, amount))
    conn.execute('UPDATE deposit_requests SET status = ? WHERE id=?', ('approved', req_id))
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute('INSERT INTO transactions (user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)',
                 (user_id, 'deposit', amount, f'Deposit approved: {amount} {coin}', now))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/reject-deposit/<int:req_id>', methods=['POST'])
def admin_reject_deposit(req_id):
    if not session.get('is_admin_logged'):
        return redirect(url_for('admin_login_page'))
    conn = get_db()
    conn.execute('UPDATE deposit_requests SET status = ? WHERE id=?', ('rejected', req_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/approve-withdraw/<int:req_id>', methods=['POST'])
def admin_approve_withdraw(req_id):
    if not session.get('is_admin_logged'):
        return redirect(url_for('admin_login_page'))
    conn = get_db()
    admin_id = session.get('admin_user_id')
    admin_role = session.get('admin_role', 'admin')
    req = conn.execute('SELECT * FROM withdraw_requests WHERE id=? AND status=?', (req_id, 'pending')).fetchone()
    if not req:
        conn.close()
        return redirect(url_for('admin_dashboard'))
    if not is_assigned_to_admin(conn, req['user_id'], admin_id, admin_role):
        conn.close()
        return redirect(url_for('admin_dashboard'))
    user_id = req['user_id']
    amount = req['amount']
    address = req['address']
    coin = req['coin']
    # Balance already deducted on request submission
    pass
    conn.execute('UPDATE withdraw_requests SET status = ? WHERE id=?', ('approved', req_id))
    sync_balance(req['user_id'])
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute('INSERT INTO transactions (user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)',
                 (user_id, 'withdrawal', -amount, f'Withdrawal approved: {amount} {coin}', now))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/reject-withdraw/<int:req_id>', methods=['POST'])
def admin_reject_withdraw(req_id):
    if not session.get('is_admin_logged'):
        return redirect(url_for('admin_login_page'))
    conn = get_db()
    # Refund balance since it was deducted on submission
    req = conn.execute('SELECT user_id, amount FROM withdraw_requests WHERE id=?', (req_id,)).fetchone()
    if req:
        conn.execute('UPDATE users SET usdt_balance = usdt_balance + ?, balance = balance + ? WHERE id=?', (req['amount'], req['amount'], req['user_id']))
        conn.execute('UPDATE wallet_balances SET balance = balance + ? WHERE user_id=? AND coin=?', (req['amount'], req['user_id'], req['coin']))
    conn.execute('UPDATE withdraw_requests SET status = ? WHERE id=?', ('rejected', req_id))
    sync_balance(req['user_id'])
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin_logged', None)
    return redirect(url_for('admin_login_page'))


# ==================== USER API ROUTES ====================

@app.route('/api/data')
@login_required
def api_data():
    conn = get_db()
    user = conn.execute('SELECT balance, usdt_balance, id, username FROM users WHERE id=?', (current_user.id,)).fetchone()
    conn.close()
    return jsonify({
        'balance': round(user['usdt_balance'] or user['balance'], 2),
        'id': user['id'],
        'name': user['username']
    })


@app.route('/api/user/wallet')
@login_required
def api_user_wallet():
    conn = get_db()
    user = conn.execute('SELECT btc_balance, eth_balance, usdt_balance FROM users WHERE id=?', (current_user.id,)).fetchone()
    conn.close()
    return jsonify({
        'success': True,
        'balances': {
            'BTC': round(user['btc_balance'] or 0.0, 6),
            'ETH': round(user['eth_balance'] or 0.0, 6),
            'USDT': round(user['usdt_balance'] or 0.0, 2)
        }
    })


@app.route('/api/wallet/all')
@login_required
def api_wallet_all():
    conn = get_db()
    rows = conn.execute('SELECT coin, balance FROM wallet_balances WHERE user_id=?', (current_user.id,)).fetchall()
    conn.close()
    balances = {row['coin']: row['balance'] for row in rows}
    result = []
    for sym, name in SUPPORTED_COINS:
        result.append({'symbol': sym, 'name': name, 'balance': balances.get(sym, 0.0)})
    return jsonify(result)


@app.route('/api/convert', methods=['POST'])
@login_required
def api_convert():
    data = request.get_json() or {}
    from_coin = data.get('from_coin')
    to_coin = data.get('to_coin')
    prices = data.get('prices', {})
    try:
        amount = float(data.get('amount', 0))
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid amount.'})
    if amount <= 0 or from_coin == to_coin or not prices:
        return jsonify({'success': False, 'message': 'Invalid parameters.'})
    from_price = float(prices.get(from_coin, 0))
    to_price = float(prices.get(to_coin, 0))
    if from_price <= 0 or to_price <= 0:
        return jsonify({'success': False, 'message': 'Invalid prices.'})
    conn = get_db()
    from_row = conn.execute('SELECT balance FROM wallet_balances WHERE user_id=? AND coin=?', (current_user.id, from_coin)).fetchone()
    from_balance = from_row['balance'] if from_row else 0.0
    if from_balance < amount:
        conn.close()
        return jsonify({'success': False, 'message': f'Insufficient {from_coin} balance.'})
    converted_amount = (amount * from_price) / to_price
    conn.execute('UPDATE wallet_balances SET balance = balance - ? WHERE user_id=? AND coin=?', (amount, current_user.id, from_coin))
    conn.execute('INSERT INTO wallet_balances (user_id, coin, balance) VALUES (?, ?, ?) ON CONFLICT(user_id, coin) DO UPDATE SET balance = balance + ?',
                 (current_user.id, to_coin, converted_amount, converted_amount))
    if from_coin == 'USDT':
        conn.execute('UPDATE users SET usdt_balance = usdt_balance - ? WHERE id=?', (amount, current_user.id))
    if to_coin == 'USDT':
        conn.execute('UPDATE users SET usdt_balance = usdt_balance + ? WHERE id=?', (converted_amount, current_user.id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'Converted {amount} {from_coin} to {converted_amount:.6f} {to_coin}'})


@app.route('/api/withdraw', methods=['POST'])
@login_required
def api_withdraw():
    data = request.get_json() or {}
    try:
        amount = float(data.get('amount', 0))
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid amount.'})
    if amount <= 0 or not data.get('address'):
        return jsonify({'success': False, 'message': 'Invalid data.'})
    conn = get_db()
    cur = conn.cursor()
    user = cur.execute('SELECT usdt_balance FROM users WHERE id=?', (current_user.id,)).fetchone()
    if not user or user['usdt_balance'] < amount:
        conn.close()
        return jsonify({'success': False, 'message': 'Insufficient balance.'})
    cur.execute('UPDATE users SET usdt_balance = usdt_balance - ? WHERE id=?', (amount, current_user.id))
    cur.execute('UPDATE wallet_balances SET balance = balance - ? WHERE user_id=? AND coin=?', (amount, current_user.id, 'USDT'))
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute('INSERT INTO transactions (user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)',
                 (current_user.id, 'withdrawal', -amount, f'Withdrawal of ${amount:.2f}', now_str))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Withdrawal submitted!'})


@app.route('/api/deposit-request', methods=['POST'])
@login_required
def api_deposit_request():
    data = request.get_json() or {}
    amount = data.get('amount')
    coin = data.get('coin', 'USDT')
    tx_hash = data.get('tx_hash', '')
    try:
        amount = float(amount)
    except:
        return jsonify({'success': False, 'message': 'Invalid amount'})
    if amount <= 0:
        return jsonify({'success': False, 'message': 'Amount must be positive'})
    conn = get_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute('INSERT INTO deposit_requests (user_id, amount, coin, tx_hash, status, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                 (current_user.id, amount, coin, tx_hash, 'pending', now))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Deposit request submitted'})


@app.route('/api/withdraw-request', methods=['POST'])
@login_required
def api_withdraw_request():
    # Check 24-hour withdrawal lock
    conn_check = get_db()
    user_lock = conn_check.execute("SELECT value FROM settings WHERE key='withdraw_lock_' || ?", (str(current_user.id),)).fetchone()
    conn_check.close()
    
    if user_lock is not None and user_lock['value'] == 'on':
        # Lock is ON - check if 24 hours passed since last withdrawal
        conn_check2 = get_db()
        last_withdraw = conn_check2.execute("SELECT created_at FROM withdraw_requests WHERE user_id=? ORDER BY id DESC LIMIT 1", (current_user.id,)).fetchone()
        conn_check2.close()
        
        if last_withdraw:
            from datetime import datetime as dt
            last_time = dt.strptime(last_withdraw['created_at'], "%Y-%m-%d %H:%M:%S")
            elapsed = dt.now() - last_time
            if elapsed.total_seconds() < 86400:  # 24 hours
                remaining = 86400 - elapsed.total_seconds()
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                return jsonify({'success': False, 'message': f'Withdrawal locked. Please wait {hours}h {minutes}m before next withdrawal.'}), 403
    data = request.get_json() or {}
    amount = data.get('amount')
    address = data.get('address')
    coin = data.get('coin', 'USDT')
    passcode = data.get('passcode', '')

    try:
        amount = float(amount)
    except:
        return jsonify({'success': False, 'message': 'Invalid amount'})
    if amount <= 0 or not address:
        return jsonify({'success': False, 'message': 'Invalid data'})

    conn = get_db()
    user = conn.execute('SELECT usdt_balance, passcode_hash FROM users WHERE id=?', (current_user.id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': 'User not found'})

    # Passcode verification
    if not user['passcode_hash']:
        conn.close()
        return jsonify({'success': False, 'message': 'You must set a passcode before withdrawing. Please go to Settings > Security > Set Passcode.'}), 403
    if not passcode or not check_password_hash(user['passcode_hash'], passcode):
        conn.close()
        return jsonify({'success': False, 'message': 'Invalid passcode'}), 400

    if user['usdt_balance'] < amount:
        conn.close()
        return jsonify({'success': False, 'message': 'Insufficient balance'})

    # Check for existing pending withdrawal
    existing_pending = conn.execute('SELECT id FROM withdraw_requests WHERE user_id=? AND status="pending"', (current_user.id,)).fetchone()
    if existing_pending:
        conn.close()
        return jsonify({'success': False, 'message': 'You already have a pending withdrawal request. Wait for admin approval first.'})

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Deduct balance from BOTH tables immediately
    conn.execute('UPDATE users SET usdt_balance = usdt_balance - ?, balance = balance - ? WHERE id=?', (amount, amount, current_user.id))
    conn.execute('UPDATE wallet_balances SET balance = balance - ? WHERE user_id=? AND coin=?', (amount, current_user.id, coin))
    
    conn.execute('INSERT INTO withdraw_requests (user_id, amount, address, coin, status, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                 (current_user.id, amount, address, coin, 'pending', now))
    conn.commit()
    conn.close()
    sync_balance(current_user.id)
    return jsonify({'success': True, 'message': 'Withdrawal request submitted'})


@app.route('/api/deposit-addresses')
def api_deposit_addresses():
    conn = get_db()
    rows = conn.execute('SELECT coin, address FROM deposit_addresses').fetchall()
    conn.close()
    result = {row['coin']: row['address'] for row in rows}
    return jsonify(result)


@app.route('/api/coingecko/markets')
def api_coingecko_markets():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=50&page=1&sparkline=false'
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        
        result = []
        for coin in data:
            result.append({
                'symbol': coin['symbol'].upper(),
                'name': coin['name'],
                'current_price': coin['current_price'],
                'price_change_percentage_24h': coin.get('price_change_percentage_24h', 0)
            })
        
        return jsonify(result)
    except Exception as e:
        print(f"CoinGecko markets error: {e}")
        return jsonify([])


@app.route('/api/coingecko/prices')
def api_coingecko_prices():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd'
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        btc_price = data.get('bitcoin', {}).get('usd', 0)
        eth_price = data.get('ethereum', {}).get('usd', 0)
        return jsonify({'btc': f"{btc_price:,.2f}", 'eth': f"{eth_price:,.2f}"})
    except Exception as e:
        print(f"CoinGecko error: {e}")
        return jsonify({'btc': '0.00', 'eth': '0.00'})


@app.route('/api/live-prices')
def live_prices():
    try:
        ids = 'bitcoin,ethereum'
        url = f'https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd'
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10).json()
        return jsonify({'btc': f"{resp['bitcoin']['usd']:,.2f}", 'eth': f"{resp['ethereum']['usd']:,.2f}"})
    except:
        return jsonify({'btc': '0.00', 'eth': '0.00'})


@app.route('/api/trading-data/<coin_id>')
def trading_data(coin_id):
    # Yahoo Finance symbol map
    symbol_map = {
        # Crypto (Yahoo uses USD suffix)
        'bitcoin': 'BTC-USD',
        'ethereum': 'ETH-USD',
        'solana': 'SOL-USD',
        'binancecoin': 'BNB-USD',
        'ripple': 'XRP-USD',
        'dogecoin': 'DOGE-USD',
        'cardano': 'ADA-USD',
        'avalanche-2': 'AVAX-USD',
        'chainlink': 'LINK-USD',
        'polkadot': 'DOT-USD',
        'litecoin': 'LTC-USD',
        'shiba-inu': 'SHIB-USD',
        'tron': 'TRX-USD',
        'matic-network': 'MATIC-USD',
        'cosmos': 'ATOM-USD',
        'uniswap': 'UNI-USD',
        'aave': 'AAVE-USD',
        'algorand': 'ALGO-USD',
        'bitcoin-cash': 'BCH-USD',
        'ethereum-classic': 'ETC-USD',
        # Metals
        'gold': 'GC=F',
        'silver': 'SI=F',
        'platinum': 'PL=F',
        'palladium': 'PA=F',
        'copper': 'HG=F',
        # Stocks
        'apple': 'AAPL',
        'tesla': 'TSLA',
        'microsoft': 'MSFT',
        'google': 'GOOGL',
        'amazon': 'AMZN',
        'meta': 'META',
        'netflix': 'NFLX',
        'nvidia': 'NVDA',
        'amd': 'AMD',
        'intel': 'INTC',
        'paypal': 'PYPL',
        'adobe': 'ADBE',
        'salesforce': 'CRM',
        'uber': 'UBER',
        'shopify': 'SHOP',
        'zoom': 'ZM'
    }
    symbol = symbol_map.get(coin_id, 'DOGE-USD')
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1h&range=2d'
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        if data.get('chart', {}).get('result'):
            result = data['chart']['result'][0]
            timestamps = result['timestamp']
            quote = result['indicators']['quote'][0]
            ohlc = []
            for i in range(len(timestamps)):
                if quote['open'][i] is not None:
                    ohlc.append([
                        int(timestamps[i]),
                        float(quote['open'][i]),
                        float(quote['high'][i]),
                        float(quote['low'][i]),
                        float(quote['close'][i])
                    ])
            if len(ohlc) > 2:
                current_price = ohlc[-1][4]
                return jsonify({'success': True, 'ohlc': ohlc[-48:], 'current_price': current_price, 'fallback': 'none'})
            else:
                raise Exception('Not enough data')
        else:
            raise Exception('Yahoo Finance error')
    except Exception as e:
        print("Yahoo Finance error:", str(e))
        return jsonify({'success': True, 'ohlc': [], 'current_price': 0, 'fallback': 'dogecoin'})

@app.route('/api/trade', methods=['POST'])
@login_required
def api_trade():
    data = request.get_json() or {}
    trade_type = data.get('type')
    symbol = data.get('symbol')
    try:
        amount = float(data.get('amount', 0))
        price = float(data.get('price', 0))
        duration = int(data.get('duration', 30))
        profit_percent = float(data.get('profit_percent', 40))
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid parameters.'})
    if amount <= 0 or price <= 0:
        return jsonify({'success': False, 'message': 'Amount and price must be positive.'})

    conn = get_db()
    cur = conn.cursor()
    user = cur.execute('SELECT usdt_balance FROM users WHERE id=?', (current_user.id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': 'User not found.'})

    total_cost = round(amount * price, 2)
    if user['usdt_balance'] < total_cost:
        conn.close()
        return jsonify({'success': False, 'message': f'Insufficient USDT balance. Need ${total_cost:.2f}'})

    cur.execute('UPDATE users SET usdt_balance = usdt_balance - ? WHERE id=?', (total_cost, current_user.id))
    cur.execute('UPDATE wallet_balances SET balance = balance - ? WHERE user_id=? AND coin=?', (total_cost, current_user.id, 'USDT'))
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute('INSERT INTO transactions (user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)',
                (current_user.id, 'trade_open', -total_cost, f'Trade opened ({trade_type.upper()}) ${total_cost:.2f}', now_str))
    cur.execute('''INSERT INTO trades (user_id, symbol, trade_type, amount, price, duration, profit_percent, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)''',
                (current_user.id, symbol, trade_type, amount, price, duration, profit_percent, now_str))
    trade_id = cur.lastrowid
    conn.commit()
    sync_balance(current_user.id)
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'trade_id': trade_id, 'message': 'Order executed successfully!'})


@app.route('/api/resolve-trade/<int:trade_id>', methods=['POST'])
@login_required
def api_resolve_trade_by_id(trade_id):
    conn = get_db()
    cur = conn.cursor()
    # Atomically claim trade to prevent double resolution
    cur.execute("UPDATE trades SET status='processing' WHERE id=? AND user_id=? AND status='pending'", (trade_id, current_user.id))
    if cur.rowcount == 0:
        conn.commit()
        conn.close()
        return jsonify({'success': False, 'message': 'Trade already resolved or invalid.'}), 400
    trade = cur.execute('SELECT * FROM trades WHERE id=? AND user_id=?', (trade_id, current_user.id)).fetchone()
    if not trade:
        conn.close()
        return jsonify({'success': False, 'message': 'Invalid trade.'}), 400

    invested_usdt = round(trade['amount'] * trade['price'], 2)
    profit_amount = round(invested_usdt * (trade['profit_percent'] / 100), 2)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    forced = get_forced_result(current_user.id)
    if forced == 'win':
        is_win = True
    elif forced == 'loss':
        is_win = False
    else:
        is_win = random.choice([True, False])

    if is_win:
        total_payout = round(invested_usdt + profit_amount, 2)
        cur.execute('UPDATE users SET usdt_balance = usdt_balance + ? WHERE id=?', (total_payout, current_user.id))
        cur.execute('UPDATE wallet_balances SET balance = balance + ? WHERE user_id=? AND coin=?', (total_payout, current_user.id, 'USDT'))
        cur.execute('INSERT INTO transactions (user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)',
                    (current_user.id, 'trade_profit', profit_amount, f'Trade win +${profit_amount:.2f}', now_str))
    else:
        refund_amount = round(invested_usdt - profit_amount, 2)
        cur.execute('UPDATE users SET usdt_balance = usdt_balance + ? WHERE id=?', (refund_amount, current_user.id))
        cur.execute('UPDATE wallet_balances SET balance = balance + ? WHERE user_id=? AND coin=?', (refund_amount, current_user.id, 'USDT'))
        cur.execute('INSERT INTO transactions (user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)',
                    (current_user.id, 'trade_loss', -profit_amount, f'Trade loss -${profit_amount:.2f}', now_str))

    cur.execute('UPDATE trades SET status=?, result=? WHERE id=?', ('completed', 'win' if is_win else 'loss', trade_id))
    conn.commit()
    user_updated = cur.execute('SELECT usdt_balance FROM users WHERE id=?', (current_user.id,)).fetchone()
    conn.close()
    sync_balance(current_user.id)
    return jsonify({'success': True, 'result': 'win' if is_win else 'loss',
                    'profit_amount': profit_amount,
                    'new_balance': round(user_updated['usdt_balance'], 2)})



@app.route('/api/trade/resolve', methods=['POST'])
@login_required
def api_trade_resolve():
    data = request.get_json() or {}
    trade_id = data.get('trade_id')

    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE trades SET status='processing' WHERE id=? AND user_id=? AND status='pending'", (trade_id, current_user.id))
    if cur.rowcount == 0:
        conn.commit()
        conn.close()
        return jsonify({'success': False, 'message': 'Trade already resolved or invalid.'}), 400
    trade = cur.execute('SELECT * FROM trades WHERE id=? AND user_id=?', (trade_id, current_user.id)).fetchone()
    if not trade:
        conn.close()
        return jsonify({'success': False, 'message': 'Invalid trade.'}), 400

    invested_usdt = round(trade['amount'] * trade['price'], 2)
    profit_amount = round(invested_usdt * (trade['profit_percent'] / 100), 2)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    forced = get_forced_result(current_user.id)
    if forced == 'win':
        is_win = True
    elif forced == 'loss':
        is_win = False
    else:
        is_win = random.choice([True, False])

    if is_win:
        total_payout = round(invested_usdt + profit_amount, 2)
        cur.execute('UPDATE users SET usdt_balance = usdt_balance + ? WHERE id=?', (total_payout, current_user.id))
        cur.execute('UPDATE wallet_balances SET balance = balance + ? WHERE user_id=? AND coin=?', (total_payout, current_user.id, 'USDT'))
        cur.execute('INSERT INTO transactions (user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)',
                    (current_user.id, 'trade_profit', profit_amount, f'Trade win +${profit_amount:.2f}', now_str))
    else:
        refund_amount = round(invested_usdt - profit_amount, 2)
        cur.execute('UPDATE users SET usdt_balance = usdt_balance + ? WHERE id=?', (refund_amount, current_user.id))
        cur.execute('UPDATE wallet_balances SET balance = balance + ? WHERE user_id=? AND coin=?', (refund_amount, current_user.id, 'USDT'))
        cur.execute('INSERT INTO transactions (user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)',
                    (current_user.id, 'trade_loss', -profit_amount, f'Trade loss -${profit_amount:.2f}', now_str))

    cur.execute('UPDATE trades SET status=?, result=? WHERE id=?', ('completed', 'win' if is_win else 'loss', trade_id))
    conn.commit()
    user_updated = cur.execute('SELECT usdt_balance FROM users WHERE id=?', (current_user.id,)).fetchone()
    conn.close()
    sync_balance(current_user.id)
    return jsonify({'success': True, 'result': 'win' if is_win else 'loss',
                    'profit_amount': profit_amount,
                    'new_balance': round(user_updated['usdt_balance'], 2)})



@app.route('/api/escrow/balance')
@login_required
def api_escrow_balance():
    conn = get_db()
    user = conn.execute('SELECT usdt_balance, escrow_balance FROM users WHERE id=?', (current_user.id,)).fetchone()
    conn.close()
    return jsonify({
        'wallet_balance': round(user['usdt_balance'] or 0.0, 2),
        'escrow_balance': round(user['escrow_balance'] or 0.0, 2)
    })


@app.route('/api/escrow/order', methods=['POST'])
@login_required
def api_escrow_order():
    data = request.get_json() or {}
    try:
        amount = float(data.get('amount', 0))
    except:
        return jsonify({'success': False, 'message': 'Invalid amount.'})
    if amount <= 0:
        return jsonify({'success': False, 'message': 'Amount must be positive.'})
    conn = get_db()
    cur = conn.cursor()
    user = cur.execute('SELECT usdt_balance, escrow_balance FROM users WHERE id=?', (current_user.id,)).fetchone()
    if not user or user['usdt_balance'] < amount:
        conn.close()
        return jsonify({'success': False, 'message': 'Insufficient wallet balance.'})
    cur.execute('UPDATE users SET usdt_balance = usdt_balance - ? WHERE id=?', (amount, current_user.id))
    cur.execute('UPDATE wallet_balances SET balance = balance - ? WHERE user_id=? AND coin=?', (amount, current_user.id, 'USDT'))
    cur.execute('UPDATE users SET escrow_balance = escrow_balance + ? WHERE id=?', (amount, current_user.id))
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur.execute('INSERT INTO transactions (user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)',
                (current_user.id, 'escrow_deposit', -amount, f'Escrow order deposited: {amount} USDT', now))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Escrow order placed successfully!'})


@app.route('/api/transactions')
@login_required
def api_transactions():
    conn = get_db()
    txs = conn.execute("SELECT * FROM transactions WHERE user_id=? AND type IN ('deposit','withdrawal','withdraw','trade_open','trade_profit','trade_loss','daily_income','plan_activate','plan_completed','position_stopped','trade_refund') ORDER BY id DESC LIMIT 50", (current_user.id,)).fetchall()
    
    result = []
    for tx in txs:
        item = {
            'id': tx['id'],
            'type': tx['type'],
            'amount': tx['amount'],
            'description': tx['description'],
            'created_at': tx['created_at'],
            'address': ''
        }
        
        # If withdrawal, get real address and details from withdraw_requests
        if tx['type'] in ('withdrawal', 'withdraw', 'admin_deduction'):
            withdraw = conn.execute('SELECT * FROM withdraw_requests WHERE user_id=? AND created_at LIKE ? ORDER BY id DESC LIMIT 1', (current_user.id, tx['created_at'][:10] + '%')).fetchone()
            if not withdraw:
                withdraw = conn.execute('SELECT * FROM withdraw_requests WHERE user_id=? ORDER BY id DESC LIMIT 1', (current_user.id,)).fetchone()
            if withdraw:
                item['address'] = withdraw['address']
                item['coin'] = withdraw['coin'] if 'coin' in withdraw.keys() else 'USDT'
                item['status'] = withdraw['status'] if 'status' in withdraw.keys() else 'pending'
                item['tx_hash'] = withdraw['tx_hash'] if 'tx_hash' in withdraw.keys() else ''
        
        # If deposit, get real tx_hash from deposit_requests
        if tx['type'] == 'deposit':
            deposit = conn.execute('SELECT * FROM deposit_requests WHERE user_id=? AND created_at LIKE ? ORDER BY id DESC LIMIT 1', (current_user.id, tx['created_at'][:10] + '%')).fetchone()
            if not deposit:
                deposit = conn.execute('SELECT * FROM deposit_requests WHERE user_id=? ORDER BY id DESC LIMIT 1', (current_user.id,)).fetchone()
            if deposit:
                item['tx_hash'] = deposit['tx_hash'] if 'tx_hash' in deposit.keys() else ''
                item['coin'] = deposit['coin'] if 'coin' in deposit.keys() else 'USDT'
                item['status'] = deposit['status'] if 'status' in deposit.keys() else 'pending'
                item['address'] = deposit['tx_hash'] if 'tx_hash' in deposit.keys() else ''
        
        # If trade, get trade details
        if 'trade' in tx['type']:
            trade = conn.execute("SELECT * FROM trades WHERE user_id=? AND created_at LIKE ? LIMIT 1", (current_user.id, tx['created_at'][:10] + '%')).fetchone()
            if not trade:
                trade = conn.execute("SELECT * FROM trades WHERE user_id=? ORDER BY id DESC LIMIT 1", (current_user.id,)).fetchone()
            if trade:
                item['symbol'] = trade['symbol']
                item['trade_type'] = trade['trade_type']
                item['duration'] = trade['duration']
                item['profit_percent'] = trade['profit_percent']
                item['price'] = trade['price']
                item['trade_result'] = trade['result']
                item['trade_amount'] = trade['amount']
        
        # If plan, get plan details by matching description
        if 'plan' in tx['type'] or 'income' in tx['type']:
            plan_name = tx['description'].replace('Activated ', '').replace('Daily income from ', '').replace('Plan completed: ', '').replace('Position stopped: ', '').strip()
            plan = conn.execute("SELECT * FROM active_plans WHERE user_id=? AND plan_name=? ORDER BY id DESC LIMIT 1", (current_user.id, plan_name)).fetchone()
            if not plan:
                plan = conn.execute("SELECT * FROM active_plans WHERE user_id=? ORDER BY id DESC LIMIT 1", (current_user.id,)).fetchone()
            if plan:
                item['plan_name'] = plan['plan_name']
                item['escrow_amount'] = plan['escrow_amount']
                item['daily_income_percent'] = plan['daily_income_percent']
                item['total_days'] = plan['total_days']
                item['total_income'] = plan['total_income']
                item['start_time'] = plan['start_time']
                item['end_time'] = plan['end_time']
        
        result.append(item)
    
    conn.close()
    return jsonify(result)



@app.route('/api/escrow/withdraw', methods=['POST'])
@login_required
def api_escrow_withdraw():
    data = request.get_json() or {}
    try:
        amount = float(data.get('amount', 0))
    except:
        return jsonify({'success': False, 'message': 'Invalid amount.'})
    if amount <= 0:
        return jsonify({'success': False, 'message': 'Amount must be positive.'})
    conn = get_db()
    cur = conn.cursor()
    user = cur.execute('SELECT usdt_balance, escrow_balance FROM users WHERE id=?', (current_user.id,)).fetchone()
    if not user or user['escrow_balance'] < amount:
        conn.close()
        return jsonify({'success': False, 'message': 'Insufficient escrow balance.'})
    cur.execute('UPDATE users SET escrow_balance = escrow_balance - ? WHERE id=?', (amount, current_user.id))
    cur.execute('UPDATE users SET usdt_balance = usdt_balance + ? WHERE id=?', (amount, current_user.id))
    cur.execute('UPDATE wallet_balances SET balance = balance + ? WHERE user_id=? AND coin=?', (amount, current_user.id, 'USDT'))
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur.execute('INSERT INTO transactions (user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)',
                (current_user.id, 'escrow_withdraw', amount, f'Escrow withdrawal: {amount} USDT', now))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'{amount} USDT moved back to main wallet!'})

@app.route('/<page>')
@login_required
def render_partial(page):
    if page in ['trading', 'wallet', 'markets', 'settings']:
        return render_template(f'partials/{page}.html')
    return jsonify({'error': 'Not found'}), 404



@app.route('/api/plan/activate', methods=['POST'])
@login_required
def api_activate_plan():
    data = request.get_json() or {}
    plan_id = data.get('plan_id')
    amount = float(data.get('amount', 0))
    
    if amount <= 0:
        return jsonify({'success': False, 'message': 'Invalid amount'})
    
    plan = PLAN_DATA.get(plan_id)
    if not plan:
        return jsonify({'success': False, 'message': 'Plan not found'})
    
    qty_str = plan['quantity'].replace('$', '').replace(',', '')
    parts = qty_str.split('-')
    min_qty = int(parts[0]) if len(parts) == 2 else 0
    max_qty = int(parts[1]) if len(parts) == 2 else 0
    
    if amount < min_qty:
        return jsonify({'success': False, 'message': f'Minimum amount for {plan["name"]} is ${min_qty}'})
    if amount > max_qty:
        return jsonify({'success': False, 'message': f'Maximum amount for {plan["name"]} is ${max_qty}'})
    
    conn = get_db()
    cur = conn.cursor()
    
    # Check participation limit
    plan_limit = plan.get('limit', 999)
    participation_count = cur.execute('SELECT COUNT(*) FROM active_plans WHERE user_id=? AND plan_name=?', (current_user.id, plan['name'])).fetchone()[0]
    if participation_count >= plan_limit:
        conn.close()
        return jsonify({'success': False, 'message': f'Participation limit reached for {plan["name"]}. Max {plan_limit} times allowed.'})
    
    # Check if user already has an active position
    existing = cur.execute("SELECT id FROM active_plans WHERE user_id=? AND status='active'", (current_user.id,)).fetchone()
    if existing:
        conn.close()
        return jsonify({'success': False, 'message': 'You already have an active position. Please wait for it to complete or stop it first.'})
    
    user = cur.execute('SELECT escrow_balance FROM users WHERE id=?', (current_user.id,)).fetchone()
    if not user or user['escrow_balance'] < amount:
        conn.close()
        return jsonify({'success': False, 'message': 'Insufficient escrow balance'})
    
    income_str = plan['income'].split('-')[0].strip('%')
    daily_percent = float(income_str)
    total_days = int(plan['days'].split()[0])
    
    now = datetime.now()
    end_time = now + timedelta(days=total_days)
    
    cur.execute('UPDATE users SET escrow_balance = escrow_balance - ? WHERE id=?', (amount, current_user.id))
    
    try:
        cur.execute('INSERT INTO active_plans (user_id, plan_name, escrow_amount, daily_income_percent, total_days, start_time, end_time, status, total_income, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (current_user.id, plan['name'], amount, daily_percent, total_days, now.strftime("%Y-%m-%d %H:%M:%S"), end_time.strftime("%Y-%m-%d %H:%M:%S"), 'active', 0.0, now.strftime("%Y-%m-%d %H:%M:%S")))
        print('INSERT success, lastrowid:', cur.lastrowid)
    except Exception as e:
        print('INSERT error:', e)
    new_plan_id = cur.lastrowid
    
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    cur.execute('INSERT INTO transactions (user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)',
                (current_user.id, 'plan_activate', -amount, f'Activated {plan["name"]}', now_str))
    
    conn.commit()
    conn.close()
    
    print('new_plan_id:', new_plan_id)
    return jsonify({'success': True, 'plan_id': new_plan_id, 'message': f'Successfully hosted {plan["name"]} with ${amount}'})

@app.route('/api/plans/active')
@login_required
def api_active_plans():
    process_active_plans()
    conn = get_db()
    plans = conn.execute('SELECT * FROM active_plans WHERE user_id=? AND status=? ORDER BY id DESC', (current_user.id, 'active')).fetchall()
    conn.close()
    result = []
    for p in plans:
        result.append({
            'id': p['id'],
            'plan_name': p['plan_name'],
            'escrow_amount': p['escrow_amount'],
            'daily_income_percent': p['daily_income_percent'],
            'total_days': p['total_days'],
            'start_time': p['start_time'],
            'end_time': p['end_time'],
            'status': p['status'],
            'total_income': p['total_income']
        })
    return jsonify(result)



@app.route('/plan-countdown/<int:plan_id>')
@login_required
def plan_countdown(plan_id):
    conn = get_db()
    plan = conn.execute('SELECT * FROM active_plans WHERE id=? AND user_id=? AND status=?', (plan_id, current_user.id, 'active')).fetchone()
    conn.close()
    if not plan:
        return "Plan not found", 404
    return render_template('partials/plan_countdown.html', plan=plan)




@app.route('/api/positions/active')
@login_required
def api_positions_active():
    conn = get_db()
    plans = conn.execute('SELECT * FROM active_plans WHERE user_id=? AND status=? ORDER BY id DESC', (current_user.id, 'active')).fetchall()
    conn.close()
    result = []
    for p in plans:
        result.append({
            'id': p['id'],
            'plan_name': p['plan_name'],
            'escrow_amount': p['escrow_amount'],
            'daily_income_percent': p['daily_income_percent'],
            'total_days': p['total_days'],
            'start_time': p['start_time'],
            'end_time': p['end_time'],
            'status': p['status'],
            'total_income': p['total_income'],
            'daily_income': p['escrow_amount'] * (p['daily_income_percent'] / 100)
        })
    return jsonify(result)

@app.route('/api/positions/stop/<int:plan_id>', methods=['POST'])
@login_required
def api_stop_position(plan_id):
    conn = get_db()
    plan = conn.execute('SELECT * FROM active_plans WHERE id=? AND user_id=? AND status=?', (plan_id, current_user.id, 'active')).fetchone()
    if not plan:
        conn.close()
        return jsonify({'success': False, 'message': 'Position not found'})
    
    # Return principal only - no profit for partial day
    principal = plan['escrow_amount']
    cur = conn.cursor()
    cur.execute('UPDATE users SET escrow_balance = escrow_balance + ? WHERE id=?', (principal, current_user.id))
    cur.execute('UPDATE active_plans SET status=? WHERE id=?', ('stopped', plan_id))
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute('INSERT INTO transactions (user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)',
                (current_user.id, 'position_stopped', principal, f'Position stopped: {plan["plan_name"]}', now_str))
    
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Position stopped. Principal returned.'})

@app.route('/api/positions/history')
@login_required
def api_positions_history():
    conn = get_db()
    plans = conn.execute('SELECT * FROM active_plans WHERE user_id=? AND status != ? ORDER BY id DESC', (current_user.id, 'active')).fetchall()
    conn.close()
    result = []
    for p in plans:
        result.append({
            'id': p['id'],
            'plan_name': p['plan_name'],
            'escrow_amount': p['escrow_amount'],
            'daily_income_percent': p['daily_income_percent'],
            'total_days': p['total_days'],
            'start_time': p['start_time'],
            'end_time': p['end_time'],
            'status': p['status'],
            'total_income': p['total_income'],
            'principal': p['escrow_amount'],
            'final_amount': p['escrow_amount'] + p['total_income']
        })
    return jsonify(result)


@app.before_request
def before_request():
    # Update last_online on user activity (every request)
    if current_user.is_authenticated:
        conn = get_db()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute('UPDATE users SET last_online=? WHERE id=?', (now_str, current_user.id))
        conn.commit()
        conn.close()
    if current_user.is_authenticated and current_user.account_status != 'active':
        logout_user()
        flash('Your account has been restricted. Please contact support.', 'error')
        return redirect(url_for('login'))
    process_active_plans()
    return None
@app.route('/api/server-time')
def api_server_time():
    return jsonify({'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})



@app.route('/api/trade/history')
@login_required
def api_trade_history():
    conn = get_db()
    trades = conn.execute('SELECT * FROM trades WHERE user_id=? ORDER BY id DESC LIMIT 50', (current_user.id,)).fetchall()
    conn.close()
    result = []
    for t in trades:
        result.append({
            'id': t['id'],
            'symbol': t['symbol'],
            'trade_type': t['trade_type'],
            'amount': t['amount'],
            'price': t['price'],
            'duration': t['duration'],
            'profit_percent': t['profit_percent'],
            'status': t['status'],
            'result': t['result'],
            'created_at': t['created_at']
        })
    return jsonify(result)



@app.route('/api/notifications')
@login_required
def api_notifications():
    notifications = []
    
    # Crypto News from CoinDesk RSS
    try:
        import xml.etree.ElementTree as ET
        url = 'https://news.google.com/rss/search?q=crypto&hl=en-US&gl=US&ceid=US:en'
        resp = requests.get(url, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
        root = ET.fromstring(resp.content)
        
        for item in root.findall('.//item')[:10]:
            title = item.find('title').text if item.find('title') is not None else 'No title'
            description = item.find('description').text if item.find('description') is not None else ''
            link = item.find('link').text if item.find('link') is not None else '#'
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
            
            import re
            clean_desc = re.sub(r'<[^>]+>', '', description)[:150] + '...'
            
            notifications.append({
                'id': abs(hash(link)) % 100000,
                'icon': 'fa-solid fa-newspaper text-blue-400',
                'title': title,
                'message': clean_desc,
                'link': link,
                'created_at': pub_date,
                'read': False
            })
    except Exception as e:
        print("News fetch error:", e)
    
    # Deposit & Withdrawal only
    conn = get_db()
    transactions = conn.execute("SELECT * FROM transactions WHERE user_id=? AND type IN ('deposit', 'withdrawal') ORDER BY id DESC LIMIT 5", (current_user.id,)).fetchall()
    conn.close()
    
    for tx in transactions:
        if tx['type'] == 'deposit':
            icon = 'fa-solid fa-arrow-down text-emerald-400'
            title = 'Deposit'
        elif tx['type'] == 'withdrawal':
            icon = 'fa-solid fa-arrow-up text-rose-400'
            title = 'Withdrawal'
        else:
            continue
        
        notifications.append({
            'id': tx['id'],
            'icon': icon,
            'title': title,
            'message': tx['description'],
            'created_at': tx['created_at'],
            'read': False
        })
    
    return jsonify(notifications)



@app.route('/api/crypto-news')
def api_crypto_news():
    try:
        import xml.etree.ElementTree as ET
        url = 'https://news.google.com/rss/search?q=crypto&hl=en-US&gl=US&ceid=US:en'
        resp = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        root = ET.fromstring(resp.content)
        
        news_items = []
        for item in root.findall('.//item')[:10]:
            title = item.find('title').text if item.find('title') is not None else 'No title'
            description = item.find('description').text if item.find('description') is not None else ''
            link = item.find('link').text if item.find('link') is not None else '#'
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
            
            # Clean HTML from description
            import re
            clean_desc = re.sub(r'<[^>]+>', '', description)[:200] + '...'
            
            news_items.append({
                'id': abs(hash(link)) % 100000,
                'title': title,
                'message': clean_desc,
                'link': link,
                'icon': 'fa-solid fa-newspaper text-blue-400',
                'created_at': pub_date,
                'read': False
            })
        
        return jsonify(news_items)
    except Exception as e:
        print("RSS error:", e)
        return jsonify([])



@app.route('/settings')
@login_required
def settings_page():
    return render_template('partials/settings.html')

@app.route('/api/user/change-password', methods=['POST'])
@login_required
def api_change_password():
    data = request.get_json() or {}
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    if len(new_password) < 8:
        return jsonify({'success': False, 'message': 'New password must be at least 8 characters'})
    conn = get_db()
    user = conn.execute('SELECT password_hash FROM users WHERE id=?', (current_user.id,)).fetchone()
    if not user or not check_password_hash(user['password_hash'], old_password):
        conn.close()
        return jsonify({'success': False, 'message': 'Old password is incorrect'})
    hashed = generate_password_hash(new_password, method='scrypt')
    conn.execute('UPDATE users SET password_hash=? WHERE id=?', (hashed, current_user.id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Password changed successfully'})











@app.route('/api/user/profile')
@login_required
def api_user_profile():
    conn = get_db()
    user = conn.execute('SELECT id, username, email, real_name, phone, city, country, profile_pic, deposit_limit, withdraw_limit, status, login_time, last_online FROM users WHERE id=?', (current_user.id,)).fetchone()
    conn.close()
    if user:
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'real_name': user['real_name'] or '',
                'phone': user['phone'] or '',
                'city': user['city'] or '',
                'country': user['country'] or '',
                'profile_pic': user['profile_pic'] or '',
                'deposit_limit': user['deposit_limit'],
                'withdraw_limit': user['withdraw_limit'],
                'status': user['status'],
                'login_time': user['login_time'],
                'last_online': user['last_online']
            }
        })
    return jsonify({'success': False, 'message': 'User not found'})


@app.route('/api/user/update-profile', methods=['POST'])
@login_required
def api_update_profile():
    data = request.get_json() or {}
    real_name = data.get('real_name', '').strip()
    phone = data.get('phone', '').strip()
    city = data.get('city', '').strip()
    country = data.get('country', '').strip()
    email = data.get('email', '').strip()

    if not email:
        return jsonify({'success': False, 'message': 'Email is required'})

    conn = get_db()
    existing = conn.execute('SELECT id FROM users WHERE email=? AND id != ?', (email, current_user.id)).fetchone()
    if existing:
        conn.close()
        return jsonify({'success': False, 'message': 'Email already exists'})

    conn.execute('UPDATE users SET real_name=?, phone=?, city=?, country=?, email=? WHERE id=?', (real_name, phone, city, country, email, current_user.id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Profile updated successfully'})


@app.route('/api/user/upload-profile-pic', methods=['POST'])
@login_required
def api_upload_profile_pic():
    if 'profile_pic' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})
    file = request.files['profile_pic']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.png', '.jpg', '.jpeg', '.gif']:
        return jsonify({'success': False, 'message': 'Invalid file type. Allowed: png, jpg, jpeg, gif'})
    filename = f"user_{current_user.id}{ext}"
    upload_folder = os.path.join('static', 'uploads', 'profile_pics')
    os.makedirs(upload_folder, exist_ok=True)
    path = os.path.join(upload_folder, filename)
    file.save(path)
    profile_pic = '/' + path.replace('\\', '/')
    conn = get_db()
    conn.execute('UPDATE users SET profile_pic=? WHERE id=?', (profile_pic, current_user.id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'profile_pic': profile_pic, 'message': 'Profile picture updated successfully'})



@app.route('/api/get-settings')
def api_get_settings():
    conn = get_db()
    rows = conn.execute('SELECT key, value FROM settings').fetchall()
    conn.close()
    result = {row['key']: row['value'] for row in rows}
    # Ensure subadmin_system_enabled has default
    if 'subadmin_system_enabled' not in result:
        result['subadmin_system_enabled'] = '1'
    return jsonify(result)

@app.route('/api/admin/settings', methods=['POST'])
def api_admin_update_settings():
    data = request.get_json() or {}
    telegram = data.get('telegram_link', '').strip()
    whatsapp = data.get('whatsapp_number', '').strip()

    # Telegram link ကို သန့်စင်ပါ
    if telegram:
        if telegram.startswith('@'):
            telegram = 'https://t.me/' + telegram[1:]
        elif not telegram.startswith('http'):
            telegram = 'https://t.me/' + telegram

    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('telegram_link', ?)", (telegram,))
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('whatsapp_number', ?)", (whatsapp,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Settings updated'})



@app.route('/api/chat/send', methods=['POST'])
def api_chat_send():
    is_admin = session.get('is_admin_logged') and request.get_json() and 'user_id' in request.get_json()
    if is_admin:
        data = request.get_json() or {}
        message = data.get('message', '').strip()
        if not message:
            return jsonify({'success': False, 'message': 'Message is required'})
        try:
            user_id = int(data.get('user_id', 0))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid user ID'}), 400
        if user_id <= 0:
            return jsonify({'success': False, 'message': 'User ID is required'}), 400
        sender = 'Egocrypto'
        recipient_id = user_id
    elif current_user.is_authenticated:
        message = (request.get_json() or {}).get('message', '').strip()
        if not message:
            return jsonify({'success': False, 'message': 'Message is required'})
        sender = current_user.username
        recipient_id = current_user.id
    else:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_db()
    if recipient_id:
        user_exists = conn.execute('SELECT id FROM users WHERE id=?', (recipient_id,)).fetchone()
        if not user_exists:
            conn.close()
            return jsonify({'success': False, 'message': 'User not found'}), 404
    conn.execute('INSERT INTO chat_messages (user_id, sender, message, created_at) VALUES (?, ?, ?, ?)',
                 (recipient_id, sender, message, now_str))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/chat/messages')
def api_chat_messages():
    if current_user.is_authenticated:
        conn = get_db()
        rows = conn.execute('SELECT * FROM chat_messages WHERE user_id=? ORDER BY id ASC', (current_user.id,)).fetchall()
        conn.close()
    elif session.get('is_admin_logged'):
        try:
            user_id = int(request.args.get('user_id', 0))
        except (ValueError, TypeError):
            return jsonify([])
        if user_id <= 0:
            return jsonify([])
        conn = get_db()
        admin_id = session.get('admin_user_id')
        admin_role = session.get('admin_role', 'admin')
        if admin_role == 'subadmin':
            assigned = conn.execute('SELECT assigned_admin_id FROM users WHERE id=?', (user_id,)).fetchone()
            if not assigned or assigned['assigned_admin_id'] != admin_id:
                conn.close()
                return jsonify([])
        rows = conn.execute('SELECT * FROM chat_messages WHERE user_id=? ORDER BY id ASC', (user_id,)).fetchall()
        if rows:
            latest_id = rows[-1]['id']
            conn.execute('INSERT OR REPLACE INTO admin_chat_seen (user_id, last_seen_chat_id) VALUES (?, ?)', (user_id, latest_id))
            conn.commit()
        conn.close()
    else:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    messages = []
    for r in rows:
        messages.append({
            'sender': r['sender'],
            'message': r['message'],
            'created_at': r['created_at'],
            'is_admin': r['sender'] == 'Egocrypto'
        })
    return jsonify(messages)

@app.route('/chat')
@login_required
def chat_page():
    return render_template('chat.html')



@app.route('/support')
def support_redirect():
    conn = get_db()
    settings = {row['key']: row['value'] for row in conn.execute('SELECT key, value FROM settings').fetchall()}
    conn.close()

    telegram = settings.get('telegram_link', '').strip()
    whatsapp = settings.get('whatsapp_number', '').strip()

    if telegram:
        return redirect(telegram, code=302)
    elif whatsapp:
        # WhatsApp number ကို digits only သန့်စင်ပြီး wa.me link သို့ redirect
        digits = ''.join(filter(str.isdigit, whatsapp))
        if digits:
            return redirect(f'https://wa.me/{digits}', code=302)

    # ဘာမှ မသတ်မှတ်ထားရင် Help page သို့ ပြန်ညွှန်းပါ
    return redirect(url_for('help_page'))



@app.route('/api/admin/unread-counts')
def api_admin_unread_counts():
    if not session.get('is_admin_logged'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    admin_id = session.get('admin_user_id')
    admin_role = session.get('admin_role', 'admin')
    conn = get_db()

    if admin_role == 'admin':
        max_user_id = conn.execute('SELECT MAX(id) as max_id FROM users').fetchone()['max_id'] or 0
        pending_deposits = conn.execute('SELECT COUNT(*) as cnt FROM deposit_requests WHERE status="pending"').fetchone()['cnt']
        pending_withdrawals = conn.execute('SELECT COUNT(*) as cnt FROM withdraw_requests WHERE status="pending"').fetchone()['cnt']
        max_chat_id = conn.execute('SELECT MAX(id) as max_id FROM chat_messages').fetchone()['max_id'] or 0
    else:
        # Sub-admin: only their assigned customers
        max_user_id = conn.execute('SELECT MAX(u.id) as max_id FROM users u WHERE u.assigned_admin_id=?', (admin_id,)).fetchone()['max_id'] or 0
        pending_deposits = conn.execute('SELECT COUNT(*) as cnt FROM deposit_requests WHERE status="pending" AND user_id IN (SELECT id FROM users WHERE assigned_admin_id=?)', (admin_id,)).fetchone()['cnt']
        pending_withdrawals = conn.execute('SELECT COUNT(*) as cnt FROM withdraw_requests WHERE status="pending" AND user_id IN (SELECT id FROM users WHERE assigned_admin_id=?)', (admin_id,)).fetchone()['cnt']
        max_chat_id = conn.execute('SELECT MAX(cm.id) as max_id FROM chat_messages cm JOIN users u ON cm.user_id = u.id WHERE u.assigned_admin_id=?', (admin_id,)).fetchone()['max_id'] or 0

    conn.close()
    return jsonify({
        'success': True,
        'max_user_id': max_user_id,
        'pending_deposits': pending_deposits,
        'pending_withdrawals': pending_withdrawals,
        'max_chat_id': max_chat_id
    })



@app.route('/api/admin/chat-unread')
def api_admin_chat_unread():
    if not session.get('is_admin_logged'):
        return jsonify([])
    conn = get_db()
    rows = conn.execute('SELECT user_id, MAX(id) as latest_chat_id FROM chat_messages GROUP BY user_id').fetchall()
    conn.close()
    return jsonify([{'user_id': r['user_id'], 'latest_chat_id': r['latest_chat_id']} for r in rows])



@app.route('/forgot-password/request', methods=['POST'])
def forgot_password_request():
    import random as _random
    data = request.get_json() or {}
    identifier = data.get('identifier', '').strip()
    if not identifier:
        return jsonify({'success': False, 'message': 'Identifier is required'}), 400
    conn = get_db()
    user = conn.execute('SELECT id FROM users WHERE username=? OR email=?', (identifier, identifier)).fetchone()
    conn.close()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    reset_code = str(_random.randint(100000, 999999))
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('reset_code_' || ?, ?)", (str(user['id']), reset_code))
    conn.commit()
    conn.close()
    print(f"Reset code for {identifier}: {reset_code}")
    return jsonify({'success': True, 'message': 'Code sent!', 'debug_code': reset_code})

@app.route('/forgot-password/reset', methods=['POST'])
def forgot_password_reset():
    data = request.get_json() or {}
    identifier = data.get('identifier', '').strip()
    code = data.get('code', '').strip()
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')
    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match'}), 400
    if len(new_password) < 8:
        return jsonify({'success': False, 'message': 'Password must be 8+ characters'}), 400
    conn = get_db()
    user = conn.execute('SELECT id FROM users WHERE username=? OR email=?', (identifier, identifier)).fetchone()
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': 'User not found'}), 404
    stored = conn.execute("SELECT value FROM settings WHERE key='reset_code_' || ?", (str(user['id']),)).fetchone()
    if not stored or stored['value'] != code:
        conn.close()
        return jsonify({'success': False, 'message': 'Invalid code'}), 400
    hashed = generate_password_hash(new_password, method='scrypt')
    conn.execute('UPDATE users SET password_hash=? WHERE id=?', (hashed, user['id']))
    conn.execute("DELETE FROM settings WHERE key='reset_code_' || ?", (str(user['id']),))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Password reset!'})

@app.route('/api/email/verify-request', methods=['POST'])
def api_email_verify_request():
    data = request.get_json() or {}
    identifier = data.get('identifier', '').strip()
    
    if not identifier:
        return jsonify({'success': False, 'message': 'Email or username is required'}), 400
    
    conn = get_db()
    user = conn.execute('SELECT id, email FROM users WHERE username=? OR email=?', (identifier, identifier)).fetchone()
    conn.close()
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    code = str(random_module.randint(100000, 999999))
    
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('verify_code_' || ?, ?)", (str(user['id']), code))
    conn.commit()
    conn.close()
    
    send_verification_email(user['email'], code)
    
    return jsonify({'success': True, 'message': 'Code sent!', 'debug_code': code})


@app.route('/api/email/verify', methods=['POST'])
def api_email_verify():
    data = request.get_json() or {}
    identifier = data.get('identifier', '').strip()
    code = data.get('code', '').strip()
    
    conn = get_db()
    user = conn.execute('SELECT id FROM users WHERE username=? OR email=?', (identifier, identifier)).fetchone()
    
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    stored = conn.execute("SELECT value FROM settings WHERE key='verify_code_' || ?", (str(user['id']),)).fetchone()
    conn.close()
    
    if stored and stored['value'] == code:
        return jsonify({'success': True, 'message': 'Verified!'})
    return jsonify({'success': False, 'message': 'Invalid code'}), 400


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('login'))
        if len(new_password) < 8:
            flash('Password must be at least 8 characters.', 'error')
            return redirect(url_for('login'))

        conn = get_db()
        user = conn.execute('SELECT id FROM users WHERE username=? OR email=?', (identifier, identifier)).fetchone()
        if not user:
            conn.close()
            flash('User not found.', 'error')
            return redirect(url_for('login'))

        hashed = generate_password_hash(new_password, method='scrypt')
        conn.execute('UPDATE users SET password_hash=? WHERE id=?', (hashed, user['id']))
        conn.commit()
        conn.close()
        flash('Password reset successfully. Please login.', 'success')
        return redirect(url_for('login'))
    return redirect(url_for('login'))



@app.route('/api/user/kyc/status')
@login_required
def kyc_status():
    conn = get_db()
    user = conn.execute('SELECT kyc_status, kyc_doc_path, kyc_submitted_at, real_name FROM users WHERE id=?', (current_user.id,)).fetchone()
    conn.close()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    return jsonify({
        'success': True,
        'kyc_status': user['kyc_status'],
        'kyc_doc_path': user['kyc_doc_path'],
        'kyc_submitted_at': user['kyc_submitted_at'],
        'real_name': user['real_name']
    })

# Admin KYC routes
@app.route('/admin/approve-kyc/<int:user_id>', methods=['POST'])
def admin_approve_kyc(user_id):
    if not session.get('is_admin_logged'):
        return redirect(url_for('admin_login_page'))
    conn = get_db()
    conn.execute("UPDATE users SET kyc_status='approved' WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject-kyc/<int:user_id>', methods=['POST'])
def admin_reject_kyc(user_id):
    if not session.get('is_admin_logged'):
        return redirect(url_for('admin_login_page'))
    conn = get_db()
    conn.execute("UPDATE users SET kyc_status='rejected' WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))



@app.route('/api/user/change-passcode', methods=['POST'])
@login_required
def change_passcode():
    data = request.get_json() or {}
    old_passcode = data.get('old_passcode', '')
    new_passcode = data.get('new_passcode', '')
    confirm_passcode = data.get('confirm_passcode', '')

    if not new_passcode.isdigit() or not (4 <= len(new_passcode) <= 6):
        return jsonify({'success': False, 'message': 'Passcode must be 4-6 digits.'}), 400
    if new_passcode != confirm_passcode:
        return jsonify({'success': False, 'message': 'New passcode and confirm passcode do not match.'}), 400

    conn = get_db()
    user = conn.execute('SELECT passcode_hash FROM users WHERE id=?', (current_user.id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': 'User not found'}), 404

    # If user already has a passcode, verify old passcode
    if user['passcode_hash']:
        if not old_passcode or not check_password_hash(user['passcode_hash'], old_passcode):
            conn.close()
            return jsonify({'success': False, 'message': 'Old passcode is incorrect'}), 400

    new_hash = generate_password_hash(new_passcode, method='scrypt')
    conn.execute('UPDATE users SET passcode_hash=? WHERE id=?', (new_hash, current_user.id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Passcode updated successfully.'})



@app.route('/api/user/passcode-status')
@login_required
def passcode_status():
    conn = get_db()
    user = conn.execute('SELECT passcode_hash FROM users WHERE id=?', (current_user.id,)).fetchone()
    conn.close()
    has_passcode = bool(user and user['passcode_hash'])
    return jsonify({'success': True, 'has_passcode': has_passcode})



@app.route('/api/user/anti-phishing', methods=['POST'])
@login_required
def set_anti_phishing():
    code = (request.get_json() or {}).get('code', '').strip()
    if not code:
        return jsonify({'success': False, 'message': 'Code is required'}), 400
    if len(code) < 4 or len(code) > 20:
        return jsonify({'success': False, 'message': 'Code must be 4-20 characters'}), 400
    conn = get_db()
    conn.execute('UPDATE users SET anti_phishing_code=? WHERE id=?', (code, current_user.id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Anti-phishing code saved successfully'})

@app.route('/api/user/anti-phishing/status')
@login_required
def anti_phishing_status():
    conn = get_db()
    user = conn.execute('SELECT anti_phishing_code FROM users WHERE id=?', (current_user.id,)).fetchone()
    conn.close()
    return jsonify({'success': True, 'anti_phishing_code': user['anti_phishing_code'] if user else ''})



@app.route('/api/user/devices')
@login_required
def user_devices():
    conn = get_db()
    user = conn.execute('SELECT ip_address, login_time, last_online, status FROM users WHERE id=?', (current_user.id,)).fetchone()
    conn.close()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    # We'll return basic current device info
    devices = []
    if user['ip_address']:
        devices.append({
            'device_name': 'Current Device',
            'ip_address': user['ip_address'],
            'login_time': user['login_time'],
            'last_online': user['last_online'],
            'status': user['status']
        })

    return jsonify({'success': True, 'devices': devices})



@app.route('/api/user/account-activity')
@login_required
def account_activity():
    conn = get_db()
    # Get latest 20 transactions for this user
    txs = conn.execute('SELECT * FROM transactions WHERE user_id=? ORDER BY id DESC LIMIT 20', (current_user.id,)).fetchall()
    conn.close()

    activities = []
    for tx in txs:
        activities.append({
            'id': tx['id'],
            'type': tx['type'],
            'amount': tx['amount'],
            'description': tx['description'],
            'created_at': tx['created_at']
        })

    return jsonify({'success': True, 'activities': activities})

@app.route('/payment/debit-card')
@login_required
def debit_card_page():
    return render_template('debit_card.html')


@app.route('/api/payment/debit-card', methods=['POST'])
@login_required
def api_save_debit_card():
    data = request.get_json() or {}
    card_name = data.get('card_name', '').strip()
    card_number = data.get('card_number', '').strip()
    card_expiry = data.get('card_expiry', '').strip()
    card_cvc = data.get('card_cvc', '').strip()
    card_address = data.get('card_address', '').strip()
    
    if not all([card_name, card_number, card_expiry, card_cvc, card_address]):
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    conn.execute('''INSERT INTO debit_cards (user_id, card_name, card_number, card_expiry, card_cvc, card_address, created_at) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 (current_user.id, card_name, card_number, card_expiry, card_cvc, card_address, now_str))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Card added successfully!'})


@app.route('/payment/bank-account')
@login_required
def bank_account_page():
    return render_template('bank_account.html')


@app.route('/api/payment/bank-account', methods=['POST'])
@login_required
def api_save_bank_account():
    data = request.get_json() or {}
    account_holder = data.get('account_holder', '').strip()
    bank_name = data.get('bank_name', '').strip()
    account_number = data.get('account_number', '').strip()
    routing_number = data.get('routing_number', '').strip()
    account_type = data.get('account_type', 'checking')
    billing_address = data.get('billing_address', '').strip()
    
    if not all([account_holder, bank_name, account_number, routing_number, billing_address]):
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    conn.execute('''INSERT INTO bank_accounts (user_id, account_holder, bank_name, account_number, routing_number, account_type, billing_address, created_at) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 (current_user.id, account_holder, bank_name, account_number, routing_number, account_type, billing_address, now_str))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Bank account linked successfully!'})


@app.route('/api/2fa/enable', methods=['POST'])
@login_required
def api_2fa_enable():
    data = request.get_json() or {}
    code = data.get('code', '').strip()
    
    conn = get_db()
    stored = conn.execute("SELECT value FROM settings WHERE key='verify_code_' || ?", (str(current_user.id),)).fetchone()
    
    if not stored or stored['value'] != code:
        conn.close()
        return jsonify({'success': False, 'message': 'Invalid code'}), 400
    
    conn.execute('UPDATE users SET twofa_enabled=1 WHERE id=?', (current_user.id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '2FA Enabled!'})


@app.route('/api/2fa/verify-login', methods=['POST'])
def api_2fa_verify_login():
    data = request.get_json() or {}
    user_id = data.get('user_id', 0)
    code = data.get('code', '').strip()
    
    conn = get_db()
    stored = conn.execute("SELECT value FROM settings WHERE key='verify_code_' || ?", (str(user_id),)).fetchone()
    conn.close()
    
    if stored and stored['value'] == code:
        return jsonify({'success': True, 'message': '2FA Verified!'})
    return jsonify({'success': False, 'message': 'Invalid code'}), 400


@app.route('/api/register/verify-request', methods=['POST'])
def api_register_verify_request():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    
    if not email or '@' not in email:
        return jsonify({'success': False, 'message': 'Valid email is required'}), 400
    
    # Generate 6-digit code
    code = str(random_module.randint(100000, 999999))
    
    # Store temporarily
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('register_verify_' || ?, ?)", (email, code))
    conn.commit()
    conn.close()
    
    # Send email
    send_verification_email(email, code)
    
    return jsonify({'success': True, 'message': 'Verification code sent!', 'debug_code': code})


@app.route('/api/register/verify', methods=['POST'])
def api_register_verify():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    code = data.get('code', '').strip()
    
    conn = get_db()
    stored = conn.execute("SELECT value FROM settings WHERE key='register_verify_' || ?", (email,)).fetchone()
    conn.close()
    
    if stored and stored['value'] == code:
        return jsonify({'success': True, 'message': 'Email verified!'})
    return jsonify({'success': False, 'message': 'Invalid code'}), 400


@app.route('/favicon.ico')
def favicon():
    return '', 204


@app.route('/api/trade/cancel/<int:trade_id>', methods=['POST'])
@login_required
def api_trade_cancel(trade_id):
    try:
        conn = get_db()
        conn.execute('PRAGMA busy_timeout = 10000;')
        cur = conn.cursor()
        
        trade = cur.execute("SELECT * FROM trades WHERE id=? AND user_id=? AND status='pending'", (trade_id, current_user.id)).fetchone()
        
        if not trade:
            conn.close()
            return jsonify({'success': False, 'message': 'Trade not found or already resolved'})
        
        # Full refund
        refund_amount = round(trade['amount'] * trade['price'], 2)
        
        # Update wallet_balances (source of truth)
        wallet = cur.execute("SELECT balance FROM wallet_balances WHERE user_id=? AND coin='USDT'", (current_user.id,)).fetchone()
        wallet_bal = wallet['balance'] if wallet else 0
        new_bal = wallet_bal + refund_amount
        
        cur.execute("UPDATE wallet_balances SET balance=? WHERE user_id=? AND coin='USDT'", (new_bal, current_user.id))
        cur.execute('UPDATE users SET usdt_balance=?, balance=? WHERE id=?', (new_bal, new_bal, current_user.id))
        cur.execute("UPDATE trades SET status='cancelled', result='refunded' WHERE id=?", (trade_id,))
        
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute('INSERT INTO transactions (user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)',
                    (current_user.id, 'trade_refund', refund_amount, 'Trade cancelled - full refund', now_str))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Trade cancelled! Full amount refunded.'})
    except Exception as e:
        print(f"Cancel error: {e}")
        return jsonify({'success': False, 'message': 'Error cancelling trade'})


@app.route('/api/kyc/list')
def api_kyc_list():
    if not session.get('is_admin_logged'):
        return jsonify([])
    conn = get_db()
    kyc_requests = conn.execute("SELECT * FROM users WHERE kyc_status='pending' ORDER BY kyc_submitted_at DESC").fetchall()
    conn.close()
    result = []
    for k in kyc_requests:
        result.append({
            'user_id': k['id'],
            'username': k['username'],
            'real_name': k['real_name'],
            'kyc_status': k['kyc_status'],
            'kyc_submitted_at': k['kyc_submitted_at']
        })
    return jsonify(result)


@app.route('/api/withdraw-lock/toggle', methods=['POST'])
@login_required
def api_toggle_withdraw_lock():
    data = request.get_json() or {}
    action = data.get('action', 'toggle')
    
    conn = get_db()
    key = f"withdraw_lock_{current_user.id}"
    
    current = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    
    if action == 'on':
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, 'on')", (key,))
    elif action == 'off':
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, 'off')", (key,))
    elif action == 'toggle':
        if current and current['value'] == 'on':
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, 'off')", (key,))
        else:
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, 'on')", (key,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Withdrawal lock updated'})


@app.route('/api/withdraw-lock/status')
@login_required
def api_withdraw_lock_status():
    conn = get_db()
    key = f"withdraw_lock_{current_user.id}"
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    
    enabled = row and row['value'] == 'on'
    return jsonify({'success': True, 'enabled': enabled})


#if __name__ == '__main__':
#    init_db()
#    from waitress import serve
#    serve(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

@app.route('/api/user/kyc/submit', methods=['POST'])
@login_required
def submit_kyc():
    full_name = request.form.get('full_name', '').strip()
    dob = request.form.get('dob', '').strip()
    nationality = request.form.get('nationality', '').strip()
    address_line1 = request.form.get('address_line1', '').strip()
    id_number = request.form.get('id_number', '').strip()
    
    if not full_name or not id_number:
        return jsonify({'success': False, 'message': 'Full name and ID number are required'})
    
    upload_folder = os.path.join('static', 'uploads', 'kyc')
    os.makedirs(upload_folder, exist_ok=True)
    
    id_front_path = ''
    id_back_path = ''
    selfie_path = ''
    
    if 'id_front' in request.files:
        file = request.files['id_front']
        if file and file.filename:
            ext = os.path.splitext(file.filename)[1].lower()
            if not ext:
                ext = '.jpg'
            filename = "kyc_" + str(current_user.id) + "_front" + ext
            path = os.path.join(upload_folder, filename)
            file.save(path)
            id_front_path = "/" + path.replace(os.sep, "/")
    
    if 'id_back' in request.files:
        file = request.files['id_back']
        if file and file.filename:
            ext = os.path.splitext(file.filename)[1].lower()
            if not ext:
                ext = '.jpg'
            filename = "kyc_" + str(current_user.id) + "_back" + ext
            path = os.path.join(upload_folder, filename)
            file.save(path)
            id_back_path = "/" + path.replace(os.sep, "/")
    
    if 'selfie' in request.files:
        file = request.files['selfie']
        if file and file.filename:
            ext = os.path.splitext(file.filename)[1].lower()
            if not ext:
                ext = '.jpg'
            filename = "kyc_" + str(current_user.id) + "_selfie" + ext
            path = os.path.join(upload_folder, filename)
            file.save(path)
            selfie_path = "/" + path.replace(os.sep, "/")
    
    doc_path = id_front_path or id_back_path or selfie_path
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = "UPDATE users SET kyc_status='pending', kyc_doc_path=?, kyc_id_front_path=?, kyc_id_back_path=?, kyc_selfie_path=?, kyc_submitted_at=?, real_name=?, kyc_dob=?, kyc_nationality=?, kyc_address_line1=?, kyc_address_city=?, kyc_address_state=?, kyc_address_postal=?, kyc_address_country=?, kyc_id_type=?, kyc_id_number=? WHERE id=?"
    conn = get_db()
    conn.execute(sql, (doc_path, id_front_path, id_back_path, selfie_path, now_str, full_name, dob, nationality, address_line1, request.form.get('address_city', ''), request.form.get('address_state', ''), request.form.get('address_postal', ''), request.form.get('address_country', ''), request.form.get('id_type', ''), id_number, current_user.id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'KYC submitted successfully!'})



if __name__ == '__main__':

import os
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
