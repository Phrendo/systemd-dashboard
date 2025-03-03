import subprocess, os
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, render_template_string
from flask import send_from_directory

from models import db, Service

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///services.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# def get_service_status(service_name):
#     """Check systemd status of a service."""
#     try:
#         result = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True)
#         return result.stdout.strip()
#     except Exception:
#         return "error"

def get_service_status(service_name):
    """Check systemd status of a service."""
    try:
        result = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True)
        status = result.stdout.strip()
        print(f"DEBUG: {service_name} -> '{status}'")  # Debug output
        return status
    except Exception as e:
        print(f"ERROR: Failed to check status of {service_name}: {e}")
        return "error"


@app.route("/")
def index():
    """Render the main dashboard."""
    services = Service.query.all()
    return render_template("index.html", services=services)

@app.route("/status")
def status():
    """Fetch updated service statuses."""
    services = Service.query.all()
    for service in services:
        service.status = get_service_status(service.name)
        service.last_checked = datetime.now(timezone.utc)
    db.session.commit()

    return "", 204  # No content response

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                          'term.ico',mimetype='image/vnd.microsoft.icon')


@app.route("/logs/<service_name>")
def logs(service_name):
    """Return logs for the requested service."""
    process = subprocess.Popen(
        ["journalctl", "-u", service_name, "--output=cat", "-n", "50"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    logs, _ = process.communicate()
    return logs, 200, {"Content-Type": "text/plain"}

@app.route("/add_service", methods=["POST"])
def add_service():
    """Add a new service from the GUI."""
    try:
        data = request.get_json()
        if not data or "name" not in data:
            return jsonify({"error": "Invalid request"}), 400

        service_name = data["name"].strip()
        description = data.get("description", "").strip()

        if Service.query.filter_by(name=service_name).first():
            return jsonify({"error": "Service already exists"}), 400

        new_service = Service(name=service_name, description=description, status="unknown")
        db.session.add(new_service)
        db.session.commit()

        return jsonify({"success": True, "name": service_name, "description": description})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/delete_service/<int:service_id>", methods=["DELETE"])
def delete_service(service_id):
    """Remove a service from the database."""
    service = Service.query.get(service_id)
    if not service:
        return jsonify({"error": "Service not found"}), 404

    db.session.delete(service)
    db.session.commit()
    return jsonify({"success": True})

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Ensure database is initialized
    app.run(host="0.0.0.0", port=5000, debug=True)
