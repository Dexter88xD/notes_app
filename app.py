from flask import Flask, render_template, request, redirect, url_for, session, flash, g
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'app.db'

def get_db_connection():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    if 'user_id' in session:
        conn = get_db_connection()
        notes = conn.execute('SELECT * FROM notes WHERE user_id = ?', (session['user_id'],)).fetchall()
        return render_template('index.html', notes=notes)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        flash('Invalid credentials. Please try again.', 'error')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            conn.close()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose a different one.', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/add', methods=['GET', 'POST'])
def add_note():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['note']
        conn = get_db_connection()
        conn.execute('INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)', (session['user_id'], title, content))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('note_form.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_note(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    note = conn.execute('SELECT * FROM notes WHERE id = ? AND user_id = ?', (id, session['user_id'])).fetchone()

    if request.method == 'POST':
        new_title = request.form['title']
        new_content = request.form['note']
        conn.execute('UPDATE notes SET title = ?, content = ? WHERE id = ?', (new_title, new_content, id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    conn.close()
    return render_template('note_form.html', note=note)

@app.route('/delete/<int:id>')
def delete_note(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute('DELETE FROM notes WHERE id = ? AND user_id = ?', (id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
