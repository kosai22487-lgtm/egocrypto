import re

with open('app.py', 'r') as f:
    content = f.read()

# ====== 1. Replace /api/resolve-trade/<int:trade_id> ======
pattern1 = r"@app\.route\('/api/resolve-trade/<int:trade_id>', methods=\['POST'\]\)[\s\S]*?(?=\n@app\.route\('/api/trade/resolve')"
new_resolve_id = '''@app.route('/api/resolve-trade/<int:trade_id>', methods=['POST'])
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

    invested_usdt = trade['amount'] * trade['price']
    profit_amount = invested_usdt * (trade['profit_percent'] / 100)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    forced = get_forced_result(current_user.id)
    if forced == 'win':
        is_win = True
    elif forced == 'loss':
        is_win = False
    else:
        is_win = random.choice([True, False])

    if is_win:
        total_payout = invested_usdt + profit_amount
        cur.execute('UPDATE users SET usdt_balance = usdt_balance + ? WHERE id=?', (total_payout, current_user.id))
        cur.execute('UPDATE wallet_balances SET balance = balance + ? WHERE user_id=? AND coin=?', (total_payout, current_user.id, 'USDT'))
        cur.execute('INSERT INTO transactions (user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)',
                    (current_user.id, 'trade_profit', profit_amount, f'Trade win +${profit_amount:.2f}', now_str))
    else:
        refund_amount = invested_usdt - profit_amount
        cur.execute('UPDATE users SET usdt_balance = usdt_balance + ? WHERE id=?', (refund_amount, current_user.id))
        cur.execute('UPDATE wallet_balances SET balance = balance + ? WHERE user_id=? AND coin=?', (refund_amount, current_user.id, 'USDT'))
        cur.execute('INSERT INTO transactions (user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)',
                    (current_user.id, 'trade_loss', -profit_amount, f'Trade loss -${profit_amount:.2f}', now_str))

    cur.execute('UPDATE trades SET status=?, result=? WHERE id=?', ('completed', 'win' if is_win else 'loss', trade_id))
    conn.commit()
    user_updated = cur.execute('SELECT usdt_balance FROM users WHERE id=?', (current_user.id,)).fetchone()
    conn.close()
    return jsonify({'success': True, 'result': 'win' if is_win else 'loss',
                    'profit_amount': profit_amount,
                    'new_balance': round(user_updated['usdt_balance'], 2)})
'''

# ====== 2. Replace /api/trade/resolve ======
pattern2 = r"@app\.route\('/api/trade/resolve', methods=\['POST'\]\)[\s\S]*?(?=\n@app\.route\('/api/escrow/balance')"
new_resolve = '''@app.route('/api/trade/resolve', methods=['POST'])
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

    invested_usdt = trade['amount'] * trade['price']
    profit_amount = invested_usdt * (trade['profit_percent'] / 100)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    forced = get_forced_result(current_user.id)
    if forced == 'win':
        is_win = True
    elif forced == 'loss':
        is_win = False
    else:
        is_win = random.choice([True, False])

    if is_win:
        total_payout = invested_usdt + profit_amount
        cur.execute('UPDATE users SET usdt_balance = usdt_balance + ? WHERE id=?', (total_payout, current_user.id))
        cur.execute('UPDATE wallet_balances SET balance = balance + ? WHERE user_id=? AND coin=?', (total_payout, current_user.id, 'USDT'))
        cur.execute('INSERT INTO transactions (user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)',
                    (current_user.id, 'trade_profit', profit_amount, f'Trade win +${profit_amount:.2f}', now_str))
    else:
        refund_amount = invested_usdt - profit_amount
        cur.execute('UPDATE users SET usdt_balance = usdt_balance + ? WHERE id=?', (refund_amount, current_user.id))
        cur.execute('UPDATE wallet_balances SET balance = balance + ? WHERE user_id=? AND coin=?', (refund_amount, current_user.id, 'USDT'))
        cur.execute('INSERT INTO transactions (user_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)',
                    (current_user.id, 'trade_loss', -profit_amount, f'Trade loss -${profit_amount:.2f}', now_str))

    cur.execute('UPDATE trades SET status=?, result=? WHERE id=?', ('completed', 'win' if is_win else 'loss', trade_id))
    conn.commit()
    user_updated = cur.execute('SELECT usdt_balance FROM users WHERE id=?', (current_user.id,)).fetchone()
    conn.close()
    return jsonify({'success': True, 'result': 'win' if is_win else 'loss',
                    'profit_amount': profit_amount,
                    'new_balance': round(user_updated['usdt_balance'], 2)})
'''

# Apply replacements
content, count1 = re.subn(pattern1, new_resolve_id + "\n\n", content, flags=re.DOTALL)
content, count2 = re.subn(pattern2, new_resolve + "\n\n", content, flags=re.DOTALL)

if count1 == 0 or count2 == 0:
    print("⚠️ One or both resolve functions not found. Trying broader regex...")
    # Fallback: replace from first resolve route to before escrow route
    broad_pattern = r"(@app\.route\('/api/resolve-trade/<int:trade_id>', methods=\['POST'\]\)[\s\S]*?)(?=\n@app\.route\('/api/escrow/balance')"
    content, count_broad = re.subn(broad_pattern, new_resolve_id + "\n\n", content, flags=re.DOTALL)
    if count_broad == 0:
        print("❌ Could not locate trade resolve functions. Please check app.py manually.")
    else:
        print(f"✅ Broad replacement applied ({count_broad} functions).")
else:
    print(f"✅ Both resolve functions replaced successfully ({count1}, {count2}).")

# Ensure get_forced_result exists (if missing, add it)
if 'def get_forced_result' not in content:
    forced_func = '''
def get_forced_result(user_id):
    conn = get_db()
    row = conn.execute('SELECT forced_result FROM admin_settings WHERE user_id=?', (user_id,)).fetchone()
    conn.close()
    return row['forced_result'] if row else 'auto'
'''
    # Insert after get_db function
    get_db_pattern = r"def get_db\(\):\n(?:    .*\n)+"
    content = re.sub(get_db_pattern, lambda m: m.group(0) + forced_func, content, count=1)
    print("✅ get_forced_result function added.")
else:
    print("✅ get_forced_result already exists.")

with open('app.py', 'w') as f:
    f.write(content)

print("🎉 Trade control patch completed. Restart server now.")
