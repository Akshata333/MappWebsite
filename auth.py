import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        security_q = request.form['securityq']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif not security_q:
            error = 'Security question answer is required.'
        elif db.execute(
            'SELECT id FROM user WHERE username = ?', (username,)
        ).fetchone() is not None:
            error = 'User {} is already registered.'.format(username)

        if error is None:
            db.execute(
                'INSERT INTO user (username, password, security_question) VALUES (?, ?, ?)',
                (username, generate_password_hash(password), security_q)
            )
            db.commit()
            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')

@bp.route('/forgotPassword', methods=('GET', 'POST'))
def forgotPassword():
    if request.method == 'POST':
        username = request.form['username']
        securityq = request.form['securityq']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif (user['security_question'] != securityq):
            error = 'Incorrect security answer.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('myAccount.forgotPasswordVerified'))

        flash(error)

    return render_template('auth/forgotPassword.html')

@bp.route('/forgotUsername', methods=('GET', 'POST'))
def forgotUsername():
    if request.method == 'POST':
        password = request.form['password']
        securityq = request.form['securityq']
        db = get_db()
        error = None

        rows = db.execute(
            'SELECT * FROM user WHERE security_question = ?', (securityq,)
        ).fetchall()
        for i in rows:
            if (check_password_hash(i['password'], password)):
                user = i

        #user = db.execute(
        #    'SELECT * FROM user WHERE security_question = ? AND password = ?', (securityq, generate_password_hash(password))
        #).fetchone()

        if user is None:
            error = 'Incorrect security answer.'
        elif not (check_password_hash(user['password'], password)):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('myAccount.account'))

        flash(error)

    return render_template('auth/forgotUsername.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view