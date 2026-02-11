from flask import Flask
from routes.auth import auth_bp
from routes.car_routes import car_bp
from routes.rent_routes import rent_bp
from routes.dashboard_routes import dashboard_bp
from routes.receipt_routes import receipt_bp
from routes.client_routes import client_bp

app = Flask(__name__)
app.secret_key = "super-secret-key"

app.register_blueprint(auth_bp)
app.register_blueprint(car_bp)
app.register_blueprint(rent_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(receipt_bp)
app.register_blueprint(client_bp)


@app.route('/')
def index():
    return "App is running"

if __name__ == '__main__':
    app.run()

