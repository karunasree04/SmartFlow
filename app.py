from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3, os, json
from datetime import datetime

from detector import process_video
from algorithms import (
    calculate_priority, priority_queue, get_highest_priority,
    calculate_green_time, get_all_paths_info, ROAD_NETWORK
)

app = Flask(__name__)
app.secret_key = "secret123"
os.makedirs("uploads", exist_ok=True)

# ─────────────────────────────────────────
#  DATABASE
# ─────────────────────────────────────────
def init_db():
    conn = sqlite3.connect('users.db')
    cur  = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, email TEXT UNIQUE, password TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email  TEXT,
        timestamp   TEXT,
        lane1 INTEGER, lane2 INTEGER, lane3 INTEGER, lane4 INTEGER,
        decision    TEXT,
        green_lane  INTEGER,
        green_time  INTEGER,
        ambulance   INTEGER
    )''')
    conn.commit()
    conn.close()

init_db()

def save_history(email, lane_counts, decision, green_lane, green_time, ambulance):
    conn = sqlite3.connect('users.db')
    cur  = conn.cursor()
    cur.execute('''INSERT INTO history
        (user_email,timestamp,lane1,lane2,lane3,lane4,decision,green_lane,green_time,ambulance)
        VALUES (?,?,?,?,?,?,?,?,?,?)''',
        (email, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
         *lane_counts, decision, green_lane, green_time, int(ambulance)))
    conn.commit()
    conn.close()

def get_history(email):
    conn = sqlite3.connect('users.db')
    cur  = conn.cursor()
    cur.execute('SELECT * FROM history WHERE user_email=? ORDER BY id DESC LIMIT 20', (email,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_stats(email):
    conn = sqlite3.connect('users.db')
    cur  = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM history WHERE user_email=?',      (email,))
    total = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM history WHERE user_email=? AND ambulance=1', (email,))
    amb   = cur.fetchone()[0]
    cur.execute('SELECT AVG(lane1+lane2+lane3+lane4) FROM history WHERE user_email=?', (email,))
    avg   = cur.fetchone()[0] or 0
    conn.close()
    return {'total': total, 'ambulance': amb, 'avg_vehicles': round(avg, 1)}

# ─────────────────────────────────────────
#  HOME
# ─────────────────────────────────────────
@app.route('/')
def home():
    return render_template('index.html')

# ─────────────────────────────────────────
#  SIGNUP / LOGIN / LOGOUT
# ─────────────────────────────────────────
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        name, email, pw = request.form['name'], request.form['email'], request.form['password']
        conn = sqlite3.connect('users.db')
        try:
            conn.execute("INSERT INTO users (name,email,password) VALUES (?,?,?)", (name,email,pw))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('signup.html', error="Email already registered.")
        conn.close()
        return redirect('/login')
    return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email, pw = request.form['email'], request.form['password']
        conn = sqlite3.connect('users.db')
        user = conn.execute("SELECT * FROM users WHERE email=? AND password=?", (email,pw)).fetchone()
        conn.close()
        if user:
            session['user']      = email
            session['user_name'] = user[1]
            return redirect('/dashboard')
        return render_template('login.html', error="Invalid email or password.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ─────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────
@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    result = None
    if request.method == 'POST':
        file = request.files.get('video')
        if file and file.filename:
            path = "uploads/input.mp4"
            file.save(path)

            lane_counts, ambulance, video = process_video(path)
            priorities  = calculate_priority(lane_counts)
            pq          = priority_queue(priorities)

            if ambulance:
                decision   = "Ambulance Detected — GREEN ALL"
                green_lane = -1
                green_time = 999
            else:
                _, green_lane = get_highest_priority(pq)
                green_time    = calculate_green_time(lane_counts[green_lane])
                decision      = f"Lane {green_lane+1} — GREEN SIGNAL"

            save_history(session['user'], lane_counts, decision,
                         green_lane+1, green_time, ambulance)

            result = {
                'lane_counts': lane_counts,
                'decision':    decision,
                'video':       video,
                'green_lane':  green_lane,
                'green_time':  green_time,
                'ambulance':   ambulance,
            }

    stats = get_stats(session['user'])
    return render_template('dashboard.html', result=result, stats=stats,
                           user_name=session.get('user_name','User'))

# ─────────────────────────────────────────
#  HISTORY PAGE
# ─────────────────────────────────────────
@app.route('/history')
def history():
    if 'user' not in session:
        return redirect('/login')
    rows  = get_history(session['user'])
    stats = get_stats(session['user'])
    return render_template('history.html', rows=rows, stats=stats,
                           user_name=session.get('user_name','User'))

# ─────────────────────────────────────────
#  PATH FINDER (GOOGLE MAPS STYLE)
# ─────────────────────────────────────────
@app.route('/pathfinder')
def pathfinder():
    if 'user' not in session:
        return redirect('/login')
    nodes     = list(ROAD_NETWORK['nodes'].keys())
    node_labels = {k: v['label'] for k,v in ROAD_NETWORK['nodes'].items()}
    return render_template('pathfinder.html',
                           nodes=nodes,
                           node_labels=node_labels,
                           user_name=session.get('user_name','User'))

@app.route('/api/findpath', methods=['POST'])
def find_path():
    if 'user' not in session:
        return jsonify({'error': 'unauthorized'}), 401
    data  = request.json
    start = data.get('start')
    end   = data.get('end')
    lane_counts = data.get('lane_counts', [0,0,0,0])

    if not start or not end or start == end:
        return jsonify({'error': 'Invalid start/end'}), 400

    result = get_all_paths_info(start, end, lane_counts)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
