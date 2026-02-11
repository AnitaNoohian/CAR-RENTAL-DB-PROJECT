from flask import Blueprint, render_template, redirect, request,session
from db import get_db_connection
from datetime import date
from flask import flash
import psycopg2


receipt_bp = Blueprint('receipt_bp', __name__, url_prefix='/receipts')

def login_required():
    return 'admin' in session

@receipt_bp.route('/')
def list_receipts():
    if not login_required():
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT rec.id, c.name, cl.first_name, cl.last_name, e.first_name, e.last_name,
                rec.daily_price, rec.total_days, rec.total_price, rec.damage_fee, rec.is_paid
            FROM receipt rec
            JOIN rent r ON rec.rental_id = r.id
            JOIN car c ON r.car_id = c.id
            JOIN client cl ON r.client_id = cl.id
            JOIN employee e ON r.employee_id = e.id
            ORDER BY rec.id
        """)
        receipts = cur.fetchall()

        return render_template('receipts.html', receipts=receipts)
    
    except psycopg2.Error:
        flash("Error loading receipts!", "danger")
        return redirect('/')

    finally:
        cur.close()
        conn.close()


# View Receipt
@receipt_bp.route('/view/<int:rent_id>')
def view_receipt(rent_id):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT km_end FROM rent WHERE id = %s", (rent_id,))
        rent = cur.fetchone()

        if not rent or rent[0] is None:
            cur.close()
            conn.close()
            return redirect('/rents')

        cur.execute("""
            SELECT rc.total_days,
                rc.daily_price,
                rc.damage_fee,
                rc.total_price,
                rc.is_paid
            FROM receipt rc
            WHERE rc.rental_id = %s
        """, (rent_id,))

        receipt = cur.fetchone()

        return render_template("view_receipt.html", receipt=receipt, rent_id=rent_id)

    except psycopg2.Error:
        flash("Error loading receipt!", "danger")
        return redirect('/rents')

    finally:
        cur.close()
        conn.close()

# Edit Receipt
@receipt_bp.route('/edit/<int:rent_id>', methods=['GET', 'POST'])
def edit_receipt(rent_id):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT km_end FROM rent WHERE id = %s", (rent_id,))
        rent = cur.fetchone()

        if not rent or rent[0] is None:
            cur.close()
            conn.close()
            return redirect('/rents')

        if request.method == 'POST':
            try:
                daily_price = int(request.form['daily_price'])
                damage_fee = int(request.form.get('damage_fee', 0))
            except ValueError:
                flash("Invalid numeric input!", "danger")
                return redirect(f"/receipts/edit/{rent_id}")

            cur.execute("""
                SELECT total_days
                FROM receipt
                WHERE rental_id = %s
            """, (rent_id,))
            result = cur.fetchone()

            if not result:
                cur.close()
                conn.close()
                return redirect('/rents')

            total_days = result[0]

            total_price = total_days * daily_price + damage_fee

            cur.execute("""
                UPDATE receipt
                SET daily_price = %s,
                    damage_fee = %s,
                    total_price = %s
                WHERE rental_id = %s
            """, (daily_price, damage_fee, total_price, rent_id))

            conn.commit()

            flash("Receipt updated successfully!", "success")
            return redirect(f"/receipts/view/{rent_id}")

        # GET request
        cur.execute("""
            SELECT daily_price, damage_fee
            FROM receipt
            WHERE rental_id = %s
        """, (rent_id,))
        receipt = cur.fetchone()

        return render_template("edit_receipt.html", receipt=receipt, rent_id=rent_id)

    except psycopg2.Error:
        conn.rollback()
        flash("Database error occurred!", "danger")
        return redirect('/rents')

    finally:
        cur.close()
        conn.close()