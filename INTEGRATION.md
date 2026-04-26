# Metro Events — Meeting Schedules: Integration Instructions
# ============================================================
# Drop all files into your project, then apply the two patches below.


## 1. File placement

Place files in these exact locations in your project:

  models/meeting.py
  routes/meetings.py
  templates/meetings/index.html
  templates/meetings/form.html


## 2. Patch app.py  — register the blueprint
# Inside create_app(), after the last `from routes.xxx import xxx_bp` block,
# add these two lines:

    from routes.meetings import meetings_bp
    app.register_blueprint(meetings_bp)


## 3. Add the nav tab
# In your base template (templates/base.html or your sidebar/navbar partial),
# add this nav item alongside the existing tabs:

    <a href="{{ url_for('meetings.index') }}"
       class="nav-link {% if request.blueprint == 'meetings' %}active{% endif %}">
      <i class="bi bi-calendar2-event me-1"></i> Meeting Schedules
    </a>


## 4. Run a DB migration
# The Meeting model creates a new `meetings` table. Run:

    flask db migrate -m "add meetings table"
    flask db upgrade

# OR if you're using db.create_all() (no migrations), just restart the app —
# the table is auto-created via the `with app.app_context(): db.create_all()`
# block already in your app.py.


## 5. Verify
# Navigate to http://127.0.0.1:5000/meetings
# You should see the Meeting Schedules page with stat cards and an empty table.
# Click "Schedule Meeting" to add your first entry.
