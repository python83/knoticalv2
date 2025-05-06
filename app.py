# app.py
from flask import Flask, request, jsonify, render_template # Added render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import date, timedelta
from models import db, Habit, HabitEntry # Use relative import if structure allows
from services import get_habit_status_for_day, calculate_streaks # Use relative import
import os 

app = Flask(__name__)
# Configure database connection (SQLite)
# --- Change to Absolute Path ---
basedir = os.path.abspath(os.path.dirname(__file__)) # Gets the directory where app.py is located
instance_path = os.path.join(basedir, 'instance') # Path to the instance folder
# Ensure the instance directory exists before configuring the URI
os.makedirs(instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_path, 'habits.db')
# -----------------------------

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

# --- API Routes ---

@app.route('/api/habits', methods=['GET'])
def get_habits():
    """Get all active habits, categorized."""
    habits = Habit.query.filter_by(is_deleted=False).order_by(Habit.created_at.desc()).all()
    today = date.today()

    categorized_habits = {
        "done_today": [],
        "done_this_week": [],
        "pending": [],
        "not_applicable_today": [] # For habits not relevant today (e.g. weekday habit on weekend)
    }

    for habit in habits:
        status = get_habit_status_for_day(habit, today)
        habit_data = {
            "id": habit.id,
            "name": habit.name,
            "frequency_type": habit.frequency_type,
            # Add completion count for today/this week if needed for display
            "completed_today": status == "done_today", # Boolean flag
        }
        if status == "done_today":
             categorized_habits["done_today"].append(habit_data)
        elif status == "done_this_week":
             categorized_habits["done_this_week"].append(habit_data)
        elif status == "pending":
             categorized_habits["pending"].append(habit_data)
        else: # 'not_applicable_today'
             categorized_habits["not_applicable_today"].append(habit_data)


    # Mimic the screenshot sorting: Pending first, then Done Today/Week
    # The client-side will likely handle the final display order
    return jsonify(categorized_habits)


@app.route('/api/habits', methods=['POST'])
def add_habit():
    """Add a new habit."""
    data = request.get_json()
    if not data or 'name' not in data or 'frequency_type' not in data:
        return jsonify({"error": "Missing name or frequency_type"}), 400

    name = data['name']
    frequency = data['frequency_type']

    if frequency not in ['daily_all', 'daily_weekdays', 'weekly']:
         return jsonify({"error": "Invalid frequency_type"}), 400

    new_habit = Habit(name=name, frequency_type=frequency)
    db.session.add(new_habit)
    db.session.commit()

    return jsonify({
        "id": new_habit.id,
        "name": new_habit.name,
        "frequency_type": new_habit.frequency_type
    }), 201

@app.route('/api/habits/<int:habit_id>/complete', methods=['POST'])
def complete_habit_today(habit_id):
    """Mark a habit as complete for today."""
    habit = Habit.query.get(habit_id)
    if not habit or habit.is_deleted:
        return jsonify({"error": "Habit not found"}), 404

    today = date.today()

    # Check if already completed today
    existing_entry = HabitEntry.query.filter_by(habit_id=habit_id, completion_date=today).first()
    if existing_entry:
        return jsonify({"message": "Habit already completed today"}), 200 # Or 409 Conflict

    # Add new entry
    new_entry = HabitEntry(habit_id=habit_id, completion_date=today)
    db.session.add(new_entry)
    db.session.commit()

    return jsonify({
        "message": "Habit marked as complete for today",
        "habit_id": habit.id,
        "date": today.isoformat()
    }), 201

# Optional: Add an endpoint to UNcomplete a task for today
@app.route('/api/habits/<int:habit_id>/uncomplete', methods=['POST'])
def uncomplete_habit_today(habit_id):
    """Unmarks a habit completion for today."""
    habit = Habit.query.get(habit_id)
    if not habit or habit.is_deleted:
        return jsonify({"error": "Habit not found"}), 404

    today = date.today()
    entry = HabitEntry.query.filter_by(habit_id=habit_id, completion_date=today).first()

    if not entry:
        return jsonify({"error": "Habit was not completed today"}), 404

    db.session.delete(entry)
    db.session.commit()

    return jsonify({"message": "Habit completion for today removed"}), 200


@app.route('/api/habits/<int:habit_id>', methods=['DELETE'])
def delete_habit(habit_id):
    """Delete a habit (soft delete)."""
    habit = Habit.query.get(habit_id)
    if not habit:
        return jsonify({"error": "Habit not found"}), 404

    # Soft delete: Mark as deleted instead of removing from DB
    habit.is_deleted = True
    # Optionally delete future entries or keep history? Soft delete keeps history.
    # Hard delete: db.session.delete(habit)
    db.session.commit()

    return jsonify({"message": "Habit marked as deleted"}), 200


@app.route('/api/habits/<int:habit_id>/stats', methods=['GET'])
def get_habit_stats(habit_id):
    """Get statistics for a specific habit."""
    habit = Habit.query.filter_by(id=habit_id, is_deleted=False).first()
    if not habit:
        return jsonify({"error": "Habit not found"}), 404

    streaks = calculate_streaks(habit_id)
    entries = HabitEntry.query.filter_by(habit_id=habit_id).order_by(HabitEntry.completion_date).all()

    # Data for calendar view (list of completion dates)
    completion_dates = [entry.completion_date.isoformat() for entry in entries]

    # Overall status (e.g., total completions)
    total_completions = len(entries)
    goals_met = total_completions # Simple example, could be more complex

    return jsonify({
        "id": habit.id,
        "name": habit.name,
        "frequency_type": habit.frequency_type,
        "created_at": habit.created_at.isoformat(),
        "current_streak": streaks["current_streak"],
        "best_streak": streaks["best_streak"],
        "goals_met": goals_met, # Total completions
        "completion_dates": completion_dates # For calendar highlighting
    })


# --- Optional Simple HTML Interface ---

@app.route('/')
def index():
    """Render a basic HTML page to interact with the API."""
    # This route doesn't fetch data itself, it serves the HTML.
    # JavaScript in index.html will call the /api/habits endpoint.
    return render_template('index.html')

@app.route('/habit/<int:habit_id>')
def habit_detail(habit_id):
     """Render a basic detail page for a habit."""
     # JavaScript on this page will call /api/habits/<id>/stats
     habit = Habit.query.get_or_404(habit_id) # Ensure habit exists
     return render_template('habit_detail.html', habit_name=habit.name, habit_id=habit.id)


if __name__ == '__main__':
    app.run(debug=True) # Enable debug mode for development