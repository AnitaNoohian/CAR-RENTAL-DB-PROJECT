from flask import Blueprint, render_template
from db import get_db_connection
from flask import flash, redirect, session
import psycopg2

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT COUNT(*) FROM car")
        total_cars = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM car WHERE is_rented = TRUE")
        rented_cars = cur.fetchone()[0]

        available_cars = total_cars - rented_cars

        cur.execute("SELECT COUNT(*) FROM client")
        total_clients = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM receipt WHERE is_paid = FALSE")
        unpaid_receipts = cur.fetchone()[0]

        cur.execute("SELECT COALESCE(SUM(total_price),0) FROM receipt WHERE is_paid = TRUE")
        total_money = cur.fetchone()[0]

        cur.execute("""
            SELECT r.id, c.name AS car_name, cl.first_name || ' ' || cl.last_name AS client_name, r.registration_date, c.is_rented
            FROM rent r
            JOIN car c ON r.car_id = c.id
            JOIN client cl ON r.client_id = cl.id
            ORDER BY r.id DESC
            LIMIT 5
        """)
        recent_rents = cur.fetchall()

        return render_template(
            "dashboard.html",
            total_cars = total_cars,
            rented_cars = rented_cars,
            available_cars = available_cars,
            total_clients = total_clients,
            unpaid_receipts = unpaid_receipts,
            total_money = total_money,
            recent_rents = recent_rents
        )

    except psycopg2.Error:
        flash("Error loading dashboard data!", "danger")
        return redirect('/')

    finally:
        cur.close()
        conn.close()
