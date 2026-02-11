from flask import Blueprint, render_template, request, redirect, session
from db import get_db_connection
from flask import flash, redirect, session
import psycopg2

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash("Username and password are required!", "danger")
            return render_template('login.html')

        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute(
                "SELECT * FROM admin WHERE username=%s AND password=%s",
                (username, password)
            )
            admin = cur.fetchone()
            cur.close()
            conn.close()

            if admin:
                session['admin'] = username
                flash("Welcome back!", "success")
                return redirect('/dashboard')
            else:
                flash("Invalid username or password!", "danger")
                return render_template('login.html')
        
        except psycopg2.Error:
            flash("Database error occurred!", "danger")
            return render_template('login.html')

        finally:
            cur.close()
            conn.close()

    return render_template('login.html')

"""
@auth_bp.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect('/login')
    return render_template('dashboard.html')
    """


@auth_bp.route('/logout')
def logout():
    session.pop('admin', None)
    flash("Logged out successfully!", "info")
    return redirect('/login')
