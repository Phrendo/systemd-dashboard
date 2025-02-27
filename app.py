import subprocess
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, render_template_string, make_response
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

from flask import render_template_string  # Import for inline template rendering

@app.route("/status")
def status():
    services = Service.query.all()
    
    # Update service statuses
    for service in services:
        service.status = get_service_status(service.name)
        service.last_checked = datetime.now(timezone.utc)
    db.session.commit()

    response = make_response(render_template_string(
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
        "{% endfor %}",
        services=services
    ))
    
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response



@app.route("/add_service", methods=["POST"])
def add_service():
    """Add a new service from the GUI."""
    try:
        data = request.get_json()  # Ensure JSON is parsed
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
