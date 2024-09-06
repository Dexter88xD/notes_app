from flask import Flask, render_template, request, redirect, url_for, session, flash
from sqlite3 import IntegrityError
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def get_db():
    conn = sqlite3.connect('app.db')
    return conn

@app.route('/')
def index():
    if 'user_id' in session:
        conn = get_db()
        notes = conn.execute('SELECT * FROM notes WHERE user_id = ?', (session['user_id'],)).fetchall()
        return render_template('index.html', notes=notes)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            return redirect(url_for('index'))
        flash('Invalid credentials. Please try again.', 'error')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            conn.close()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
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
        conn = get_db()
        conn.execute('INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)', (session['user_id'], title, content))
        conn.commit()
        return redirect(url_for('index'))
    return render_template('note_form.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_note(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    note = conn.execute('SELECT * FROM notes WHERE id = ? AND user_id = ?', (id, session['user_id'])).fetchone()

    if request.method == 'POST':
        new_title = request.form['title']
        new_content = request.form['note']
        conn.execute('UPDATE notes SET title = ?, content = ? WHERE id = ?', (new_title, new_content, id))
        conn.commit()
        return redirect(url_for('index'))

    return render_template('note_form.html', note=note)


@app.route('/delete/<int:id>')
def delete_note(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    conn.execute('DELETE FROM notes WHERE id = ? AND user_id = ?', (id, session['user_id']))
    conn.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
