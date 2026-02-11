from flask import Blueprint, render_template, request, redirect, session
from db import get_db_connection
from datetime import date
from flask import flash
import psycopg2


rent_bp = Blueprint('rent', __name__, url_prefix='/rents')

def login_required():
    return 'admin' in session


@rent_bp.route('/add', methods=['GET', 'POST'])
def add_rent():
    if not login_required():
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        car_id = request.form['car_id']
        client_id = request.form['client_id']
        employee_id = request.form['employee_id']
        km_start = request.form['km_start']

        try:
            cur.execute("""
                INSERT INTO rent (km_start, car_id, employee_id, client_id)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (km_start, car_id, employee_id, client_id))

            rent_id = cur.fetchone()[0]

            # make a receipt
            cur.execute("""
                INSERT INTO receipt (daily_price, is_paid, rental_id)
                VALUES (%s, %s, %s)
            """, (0, False, rent_id))

            # update is_rented
            cur.execute("""
                UPDATE car SET is_rented = TRUE WHERE id = %s
            """, (car_id,))

            conn.commit()
            flash("Rent created successfully!", "success")
            return redirect('/rents')
        
        except psycopg2.Error:
            conn.rollback()
            flash("Error creating rent!", "danger")
            return redirect('/rents/add')

        finally:
            cur.close()
            conn.close()
    try:
        cur.execute("SELECT id, name FROM car WHERE is_rented = FALSE")
        cars = cur.fetchall()

        cur.execute("SELECT id, first_name, last_name FROM client")
        clients = cur.fetchall()

        cur.execute("SELECT id, first_name, last_name FROM employee")
        employees = cur.fetchall()

        cur.close()
        conn.close()

        return render_template(
            'add_rent.html',
            cars = cars,
            clients = clients,
            employees = employees
        )
    
    except psycopg2.Error:
        flash("Error loading form data!", "danger")
        return redirect('/rents')

    finally:
        cur.close()
        conn.close()

@rent_bp.route('/add/<int:car_id>', methods=['GET', 'POST'])
def add_rent_car(car_id):
    if not login_required():
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        client_id = request.form['client_id']
        employee_id = request.form['employee_id']
        km_start = request.form['km_start']

        try:
            cur.execute("""
                INSERT INTO rent (km_start, car_id, employee_id, client_id)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (km_start, car_id, employee_id, client_id))

            rent_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO receipt (daily_price, is_paid, rental_id)
                VALUES (%s, %s, %s)
            """, (0, False, rent_id))

            cur.execute("UPDATE car SET is_rented = TRUE WHERE id = %s", (car_id,))

            conn.commit()
            flash("Rent created successfully!", "success")
            return redirect('/rents')
        
        except psycopg2.Error:
            conn.rollback()
            flash("Error creating rent!", "danger")
            return redirect(f'/rents/add/{car_id}')

        finally:
            cur.close()
            conn.close()

    try:
        cur.execute("SELECT id, name FROM car WHERE id = %s", (car_id,))
        car = cur.fetchone()

        cur.execute("SELECT id, first_name, last_name FROM client")
        clients = cur.fetchall()

        cur.execute("SELECT id, first_name, last_name FROM employee")
        employees = cur.fetchall()

        cur.close()
        conn.close()

        return render_template(
            'add_rent.html',
            cars=[car],      
            clients=clients,
            employees=employees,
            selected_car_id=car_id
        )
    except psycopg2.Error:
        flash("Error loading form!", "danger")
        return redirect('/rents')

    finally:
        cur.close()
        conn.close()

@rent_bp.route('/')
def list_rents():       #rent list
    if not login_required():
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT r.id, c.name, cl.first_name, cl.last_name, e.first_name, e.last_name,
        r.registration_date, r.km_start, r.km_end
        FROM rent r
        JOIN car c ON r.car_id = c.id
        JOIN client cl ON r.client_id = cl.id
        JOIN employee e ON r.employee_id = e.id
        ORDER BY r.id
    """)
    rents = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('rents.html', rents=rents)


@rent_bp.route('/finish/<int:rent_id>', methods=['GET', 'POST'])
def finish_rent(rent_id):
    if not login_required():
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT km_end FROM rent WHERE id = %s", (rent_id,))
        result = cur.fetchone()

        if result[0] is not None:
            return redirect('/rents')


        if request.method == 'POST':
            try:
                km_end = int(request.form['km_end'])
                daily_price = int(request.form['daily_price'])
                damage_fee = int(request.form.get('damage_fee', 0))
            except ValueError:
                flash("Invalid numeric input!", "danger")
                return redirect(f'/rents/finish/{rent_id}')

            cur.execute("""
                SELECT r.registration_date, r.car_id
                FROM rent r
                WHERE r.id = %s
            """, (rent_id,))
            reg_date, car_id = cur.fetchone()

            total_days = (date.today() - reg_date.date()).days
            if total_days == 0:
                total_days = 1

            total_price = total_days * daily_price + damage_fee

            # update rent
            cur.execute("""
                UPDATE rent
                SET km_end = %s
                WHERE id = %s
            """, (km_end, rent_id))

            # update receipt
            cur.execute("""
                UPDATE receipt
                SET total_days = %s,
                    total_price = %s,
                    damage_fee = %s,
                    daily_price = %s,
                    is_paid = TRUE
                WHERE rental_id = %s
            """, (total_days, total_price, damage_fee, daily_price, rent_id))

            # change is_rented  
            cur.execute("""
                UPDATE car SET is_rented = FALSE WHERE id = %s
            """, (car_id,))

            conn.commit()
            cur.close()
            conn.close()

            return redirect('/rents')

        cur.execute("""
            SELECT r.id, c.name
            FROM rent r
            JOIN car c ON r.car_id = c.id
            WHERE r.id = %s
        """, (rent_id,))
        rent = cur.fetchone()

        cur.close()
        conn.close()

        return render_template('finish_rent.html', rent=rent)

    except psycopg2.Error:
        conn.rollback()
        flash("Database error occurred!", "danger")
        return redirect('/rents')

    finally:
        cur.close()
        conn.close()