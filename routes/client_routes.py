from flask import Blueprint, render_template, request, redirect, session, flash
from db import get_db_connection
from datetime import date
import psycopg2

client_bp = Blueprint('client_bp', __name__, url_prefix='/clients')

def login_required():
    return 'admin' in session

@client_bp.route('/')
def list_clients():
    if not login_required():
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT c1.id, c1.first_name || ' ' || c1.last_name AS client_name, c1.national_id,
               c1.birth_date, c1.registration_date, c1.city, c1.street, c1.house_number,
               c2.phone_number
        FROM client c1
        LEFT JOIN client_phone c2 ON c2.client_id = c1.id
        ORDER BY c1.id DESC
    """)
    clients = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("clients.html", clients=clients)


@client_bp.route('/add', methods=['GET', 'POST'])
def add_client():
    if not login_required():
        return redirect('/login')

    if request.method == 'POST':
        full_name = request.form['name']
        first_name, last_name = full_name.split(' ', 1) if ' ' in full_name else (full_name, '')
        national_id = request.form.get('national_id', None)
        birthday = request.form.get('birthday', None) or None
        registration_date = request.form.get('registration_date', None) or date.today()
        city = request.form.get('city', None) or None
        street = request.form.get('street', None) or None
        house_number = request.form.get('house_number', None)  or None
        phone_number = request.form.get('phone_number', None)  or None

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                INSERT INTO client (first_name, last_name, national_id, birth_date, registration_date, city, street, house_number)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (first_name, last_name, national_id, birthday, registration_date, city, street, house_number))
            client_id = cur.fetchone()[0]

            # insert phone_number
            if phone_number:
                cur.execute("""
                    INSERT INTO client_phone (client_id, phone_number)
                    VALUES (%s, %s)
                """, (client_id, phone_number))

            conn.commit()
            cur.close()
            conn.close()

        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash("National ID or Phone already exists!", "danger")

        except psycopg2.Error:
            conn.rollback()
            flash("Something went wrong while adding client!", "danger")

        finally:
            cur.close()
            conn.close()

        return redirect('/clients')

    return render_template('client_form.html', action="Add")


@client_bp.route('/edit/<int:client_id>', methods=['GET', 'POST'])
def edit_client(client_id):
    if not login_required():
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        full_name = request.form['name']
        first_name, last_name = full_name.split(' ', 1) if ' ' in full_name else (full_name, '')
        national_id = request.form.get('national_id', None) 
        birthday = request.form.get('birthday', None) or None
        registration_date = request.form.get('registration_date', None) or date.today()
        city = request.form.get('city', None) or None
        street = request.form.get('street', None) or None
        house_number = request.form.get('house_number', None) or None
        phone_number = request.form.get('phone_number', None) or None

        try:
            # update client table
            cur.execute("""
                UPDATE client
                SET first_name=%s, last_name=%s, national_id=%s, birth_date=%s,
                    registration_date=%s, city=%s, street=%s, house_number=%s
                WHERE id=%s
            """, (first_name, last_name, national_id, birthday, registration_date, city, street, house_number, client_id))

            # update phone table
            if phone_number:
                cur.execute("""
                    INSERT INTO client_phone (client_id, phone_number)
                    VALUES (%s, %s)
                    ON CONFLICT (client_id, phone_number) DO NOTHING
                """, (client_id, phone_number))

            conn.commit()
            flash("Client updated successfully!", "success")
            return redirect('/clients')
        
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash("National ID or Phone already exists!", "danger")

        except psycopg2.Error:
            conn.rollback()
            flash("Something went wrong while updating client!", "danger")

        finally:
            cur.close()
            conn.close()

        return redirect(f'/clients/edit/{client_id}')

    try:
        cur.execute("""
            SELECT c1.id, c1.first_name || ' ' || c1.last_name AS client_name, c1.national_id,
                c1.birth_date, c1.registration_date, c1.city, c1.street, c1.house_number,
                c2.phone_number
            FROM client c1
            LEFT JOIN client_phone c2 ON c2.client_id = c1.id
            WHERE c1.id=%s
        """, (client_id,))
        client = cur.fetchone()
        cur.close()
        conn.close()
        return render_template('client_form.html', client=client, action="Edit")
    
    except psycopg2.Error:
        flash("Error loading client data!", "danger")
        return redirect('/clients')

    finally:
        cur.close()
        conn.close()