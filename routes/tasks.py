from flask import Blueprint, jsonify

# 1. Define the Blueprint. The variable MUST be named tasks_bp
tasks_bp = Blueprint('tasks', __name__)

# 2. Create a simple test route
@tasks_bp.route('/api/tasks', methods=['GET'])
def get_tasks():
    return jsonify({
        "status": "success",
        "message": "Your tasks route is successfully connected!"
    })