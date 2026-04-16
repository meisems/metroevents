# Metro Events

## Overview
Metro Events is a comprehensive Event Resource Management (ERM) system designed to streamline the event planning process. Originally developed for a software design laboratory project, this system provides event organizers with robust tools to manage clients, track event progress, and generate detailed estimates. 

The core philosophy of the application is a "One Event = One Workspace" logic, ensuring that all data, communications, and requirements for a specific event are centralized and isolated for maximum organization.

## Features
* **CRM Pipeline:** Track prospective clients and manage relationships seamlessly.
* **Quotation Builder:** Generate dynamic, customized cost estimates and quotations for events.
* **Dedicated Workspaces:** Isolated dashboards and management screens for every individual event.
* **Modular Design:** Built with a clean separation of routes, models, and templates.

## Tech Stack
* **Frontend:** HTML, CSS, JavaScript (rendered via Jinja2 templates)
* **Backend:** Python (Flask)
* **Database:** SQLite (`metro_events.db`)

## Project Structure
```text
metroevents/
├── models/             # Database schemas and models
├── routes/             # Flask routing and controller logic
├── static/             # Static assets (CSS, JS, Images)
├── templates/          # HTML templates (Jinja2)
├── app.py / run.py     # Main application entry points
├── config.py           # Application configuration variables
├── database.py         # Database connection and setup logic
├── seed.py             # Utility to populate the database with initial sample data
├── Procfile            # Deployment instructions (e.g., for Heroku)
└── requirements.txt    # Required Python packages and dependencies
