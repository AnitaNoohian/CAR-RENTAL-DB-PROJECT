import psycopg2

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="CarRentalDB",   
        user="postgres",         
        password="Anet1383",
        port=5432
    )
