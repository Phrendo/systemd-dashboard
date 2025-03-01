import subprocess
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from models import db, Service

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///services.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def get_service_status(service_name):
    """Check systemd status of a service."""
    try:
        result = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception:
        return "error"

@app.route("/")
def index():
    """Render the main dashboard."""
    services = Service.query.all()
    return render_template("index.html", services=services)

@app.route("/status")
def status():
    """Update service statuses and return them to the frontend."""
    services = Service.query.all()
    for service in services:
        service.status = get_service_status(service.name)
        service.last_checked = datetime.now(timezone.utc)
    db.session.commit()

    return render_template_string(
        "<tbody id='service-list'>"
        "{% for service in services %}"
        "<tr id='service-{{ service.id }}'>"
        "    <td>{{ service.name }}</td>"
        "    <td class='{{ service.status }}'>{{ service.status }}</td>"
        "    <td>"
        "        <button hx-delete='/delete_service/{{ service.id }}' "
        "                hx-target='#service-{{ service.id }}' "
        "                hx-swap='outerHTML'>❌ Remove</button>"
        "    </td>"
        "</tr>"
        "{% endfor %}"
        "</tbody>",
        services=services
    )

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

@app.route("/logs/<service_name>")
def logs(service_name):
    """Return logs as plain text for HTMX to insert directly."""
    process = subprocess.Popen(
        ["journalctl", "-u", service_name, "--output=cat", "-n", "50"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    logs, _ = process.communicate()
    return logs, 200, {"Content-Type": "text/plain"}


def fetch_logs(service_name):
    """Fetch the last 20 logs from journalctl for a given service."""
    try:
        result = subprocess.run(
            ["journalctl", "-u", service_name, "--output=cat", "-n", "20"],
            capture_output=True, text=True
        )
        return result.stdout.strip() if result.stdout else "No logs found."
    except Exception as e:
        return f"Error fetching logs: {e}"

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Ensure database is initialized
    app.run(host="0.0.0.0", port=5000, debug=True)
