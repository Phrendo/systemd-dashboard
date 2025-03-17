import subprocess, os
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, send_from_directory
from models import db, Service

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///services.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

def get_service_status(service_name):
    """Check systemd status of a service."""
    try:
        result = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True)
        status = result.stdout.strip()
        return status
    except Exception as e:
        return "error"

@app.route("/")
def index():
    """Render the main dashboard with preloaded logs."""
    services = Service.query.all()

    for service in services:
        service.status = get_service_status(service.name)  # Force a live check
        print(f"DEBUG: Passing to UI -> {service.name}: {service.status}")  # Debug Output

    return render_template("index.html", services=services)

@app.route("/manage_services")
def manage_services():
    """Render the service management page."""
    services = Service.query.all()
    return render_template("manage_services.html", services=services)

@app.route("/status")
def status():
    """Fetch updated service statuses and return as JSON."""
    services = Service.query.all()
    status_data = {service.name: get_service_status(service.name) for service in services}
    return jsonify(status_data)

@app.route("/logs/<service_name>")
def logs(service_name):
    """Return logs for the requested service."""
    process = subprocess.Popen([
        "journalctl", "-u", service_name, "--output=short", "-n", "50"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    logs, _ = process.communicate()
    return logs, 200, {"Content-Type": "text/plain"}

@app.route("/add_service", methods=["POST"])
def add_service():
    """Add a new service."""
    data = request.get_json()
    if not data or "name" not in data:
        return jsonify({"error": "Invalid request"}), 400
    service_name = data["name"].strip()
    if Service.query.filter_by(name=service_name).first():
        return jsonify({"error": "Service already exists"}), 400
    new_service = Service(name=service_name, status="unknown")
    db.session.add(new_service)
    db.session.commit()
    return jsonify({"success": True, "name": service_name})

@app.route("/delete_service/<int:service_id>", methods=["DELETE"])
def delete_service(service_id):
    """Remove a service."""
    service = Service.query.get(service_id)
    if not service:
        return jsonify({"error": "Service not found"}), 404
    db.session.delete(service)
    db.session.commit()
    return jsonify({"success": True})

# New route to handle start, stop, and restart actions:
@app.route("/service/<service_name>/<action>", methods=["POST"])
def service_action(service_name, action):
    """Perform a systemctl action on the service (start, stop, or restart)."""
    valid_actions = ["start", "stop", "restart"]
    if action not in valid_actions:
        return jsonify({"error": "Invalid action"}), 400
    try:
        #subprocess.run(["systemctl", action, service_name], check=True)
        subprocess.run(["sudo", "systemctl", action, service_name], check=True)
        updated_status = get_service_status(service_name)
        # Optionally update status in the database:
        service = Service.query.filter_by(name=service_name).first()
        if service:
            service.status = updated_status
            db.session.commit()
        return jsonify({"success": True, "status": updated_status})
    except subprocess.CalledProcessError:
        return jsonify({"success": False, "error": f"Failed to {action} service {service_name}"}), 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
