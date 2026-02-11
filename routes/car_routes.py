from flask import Blueprint, render_template, request, redirect, session
from db import get_db_connection
from flask import flash
import psycopg2


car_bp = Blueprint('car', __name__, url_prefix='/cars')

def login_required():
    return 'admin' in session


@car_bp.route('/')
def list_cars():
    if not login_required():
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM car ORDER BY id")
    cars = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('cars.html', cars=cars)


@car_bp.route('/add', methods=['POST'])
def add_car():
    if not login_required():
        return redirect('/login')

    name = request.form['name']
    plate = request.form['plate_number']
    color = request.form['color']
    fuel = request.form['fuel_type']
    fuel_cons = request.form['fuel_consumption']

    if fuel_cons == '':
        fuel_cons = None

    if color == '':
        color = None


    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO car (name, plate_number, color, fuel_type, fuel_consumption_l_per_100km)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, plate, color, fuel, fuel_cons))

        conn.commit()
        flash("Car added successfully!", "success")
        return redirect('/cars')
    
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        flash("This plate number already exists!", "danger")
        return redirect('/cars')

    except psycopg2.Error:
        conn.rollback()
        flash("Invalid data entered!", "danger")
        return redirect('/cars')

    finally:
        cur.close()
        conn.close()


@car_bp.route('/delete/<int:id>')
def delete_car(id):
    if not login_required():
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM car WHERE id=%s", (id,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect('/cars')


@car_bp.route('/<int:id>')
def car_detail(id):
    if not login_required():
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM car WHERE id=%s", (id,))
    car = cur.fetchone()
    
    cur.execute("SELECT * FROM rent WHERE car_id=%s AND km_end IS NULL", (id,))
    rent = cur.fetchone()
    
    cur.close()
    conn.close()

    return render_template('car_detail.html', car=car, rented=bool(rent))

@car_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_car(id):
    if not login_required():
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        plate = request.form['plate_number']
        color = request.form['color'] or None
        fuel = request.form['fuel_type']
        fuel_cons = request.form['fuel_consumption'] or None

        try:
            cur.execute("""
                UPDATE car
                SET name=%s, plate_number=%s, color=%s,
                    fuel_type=%s, fuel_consumption_l_per_100km=%s
                WHERE id=%s
            """, (name, plate, color, fuel, fuel_cons, id))

            conn.commit()
            flash("Car updated successfully!", "success")
            return redirect(f'/cars/{id}')

        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash("Plate number already exists!", "danger")

        except psycopg2.Error:
            conn.rollback()
            flash("Something went wrong!", "danger")
            return redirect(f'/cars/edit/{id}')
        
    cur.execute("SELECT * FROM car WHERE id=%s", (id,))
    car = cur.fetchone()

    cur.close()
    conn.close()
    return render_template('edit_car.html', car=car)
