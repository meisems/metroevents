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
* **Database:** SQLAlchemy (PostgreSQL/SQLite), SQLite ('metro_events.db')

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
```

## Getting Started

### Prerequisites
Make sure you have Python installed. It is highly recommended to use a virtual environment.

### Installation

### 1. Clone the repository:
   ```bash
   git clone [https://github.com/meisems/metroevents.git](https://github.com/meisems/metroevents.git)
   cd metroevents
   ```
### 2. Create and activate a virtual environment:

```Bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3.Install the dependencies:
```Bash
pip install -r requirements.txt
```

### 4.Initialize the Database:
## Run the seed script to set up the local SQLite database and populate it with initial sample data.
```Bash
python seed.py
```

### 5.Run the Application:
```Bash
python run.py
```
*Navigate to http://127.0.0.1:5000 in your web browser to view the app.*

```markdown
Deployment
This application includes a `Procfile` and is ready to be deployed to platform-as-a-service providers like Heroku. 
```

## Contributors
* [@meisems](https://github.com/meisems)
