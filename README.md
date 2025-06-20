# SERVICES_DASH

## Description
A Flask-based web dashboard for monitoring and managing systemd services. This application provides a simple web interface to view service statuses, read logs, and perform basic service operations (start, stop, restart).

![Full Screen](https://github.com/Phrendo/systemd-web-dash-boards/static/DASH_01.jpg?raw=true)

![Log Accordion View](https://github.com/Phrendo/systemd-web-dash-boards/static/DASH_02.jpg?raw=true)


## Features
- Real-time service status monitoring
- Live log viewing with auto-refresh
- Service management (start, stop, restart)
- Add/remove services from monitoring
- Responsive web interface with collapsible log sections

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python init_db.py
```

## Usage

### Running the Application

1. Start as the services-dash user:
```bash
sudo su - services-dash
cd /opt/services-dash
source venv/bin/activate
python app.py
```

2. Or create a systemd service (recommended for production):
```bash
sudo nano /etc/systemd/system/services-dash.service
```

Add this content:
```ini
[Unit]
Description=Services Dashboard Monitor
After=network.target

[Service]
Type=simple
User=services-dash
Group=services-dash
WorkingDirectory=/opt/services-dash
Environment=PATH=/opt/services-dash/venv/bin
ExecStart=/opt/services-dash/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable services-dash
sudo systemctl start services-dash
```

### Using the Web Interface

1. Open your web browser and navigate to `http://localhost:5000`

2. Use the web interface to:
   - View service statuses on the main dashboard
   - Click service names to expand/collapse log views
   - Use the "Manage Services" link to add or remove services
   - Control services with start/stop/restart buttons

## Requirements
- Python 3.7+
- Linux system with systemd

## System Setup (Required)

### 1. Create Application User
Create a dedicated user for running the application:

```bash
# Create the services-dash user with home directory
sudo useradd -m -s /bin/bash services-dash

# Add user to systemd-journal group for log access
sudo usermod -a -G systemd-journal services-dash

# Set up application directory
sudo mkdir -p /opt/services-dash
sudo chown services-dash:services-dash /opt/services-dash
```

### 2. Grant SystemD Permissions
Create a PolicyKit rule to allow the services-dash user to manage systemd services:

```bash
# Create PolicyKit rule file
sudo nano /etc/polkit-1/rules.d/50-services-dash.rules
```

Add the following content:
```javascript
polkit.addRule(function(action, subject) {
    if (action.id.match("org.freedesktop.systemd1.manage-units") &&
        subject.user == "services-dash") {
        return polkit.Result.YES;
    }
});
```

Restart PolicyKit to apply changes:
```bash
sudo systemctl restart polkit
```

### 3. Deploy Application
Switch to the application user and deploy:

```bash
# Switch to services-dash user
sudo su - services-dash

# Clone repository to application directory
cd /opt/services-dash
git clone <repository-url> .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py
```
