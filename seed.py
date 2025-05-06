# seed.py

import random
from datetime import date, timedelta
from app import app, db  # Import your Flask app and db instance
from models import Habit, HabitEntry # Import your database models

def seed_database():
    """Populates the database with sample habits and past entries."""

    with app.app_context(): # IMPORTANT: Operations must be within the app context
        print("Seeding database...")

        # --- Optional: Clear existing data ---
        # Uncomment these lines if you want to start fresh each time you seed
        # print("Clearing existing data...")
        # HabitEntry.query.delete()
        # Habit.query.delete()
        # db.session.commit()
        # print("Existing data cleared.")
        # --- End Optional Clear ---


        # --- Define Sample Habits ---
        habits_data = [
            {"name": "🇩🇪 Learn German", "frequency_type": "daily_all"},
            {"name": "💪 Workout", "frequency_type": "daily_weekdays"},
            {"name": "🎹 Practice Piano", "frequency_type": "daily_all"},
            {"name": "💧 Water Plants", "frequency_type": "weekly"},
            {"name": "📚 Read Book", "frequency_type": "daily_all"},
        ]

        # --- Create Habit Objects ---
        created_habits = []
        print("Creating habits...")
        for data in habits_data:
            # Check if habit already exists (to avoid duplicates if not clearing)
            existing_habit = Habit.query.filter_by(name=data["name"]).first()
            if not existing_habit:
                habit = Habit(name=data["name"], frequency_type=data["frequency_type"])
                db.session.add(habit)
                created_habits.append(habit) # Keep track if newly created
            else:
                print(f"Habit '{data['name']}' already exists, skipping creation.")
                created_habits.append(existing_habit) # Use existing one for entries

        # Commit habits first to get their IDs assigned
        try:
            db.session.commit()
            print(f"{len(created_habits)} habits processed/created.")
        except Exception as e:
            db.session.rollback()
            print(f"Error committing habits: {e}")
            return # Stop if habits can't be created


        # --- Generate Past Habit Entries ---
        print("Generating past habit entries...")
        today = date.today()
        num_days_history = 90 # Go back 90 days

        for habit in created_habits: # Use the list of created/existing habits
            print(f"  Generating entries for: {habit.name} ({habit.frequency_type})")
            entries_added = 0
            for i in range(num_days_history):
                entry_date = today - timedelta(days=i)
                should_add = False

                # Determine if an entry should potentially exist based on frequency
                if habit.frequency_type == "daily_all":
                    # Simulate missing days randomly (e.g., 85% completion rate)
                    if random.random() < 0.85:
                        should_add = True
                elif habit.frequency_type == "daily_weekdays":
                    # Only add on weekdays (Mon-Fri, weekday() is 0-4)
                    if entry_date.weekday() < 5:
                        # Simulate missing days randomly (e.g., 90% completion rate on weekdays)
                         if random.random() < 0.90:
                            should_add = True
                elif habit.frequency_type == "weekly":
                     # Add roughly once a week, e.g., only on Sundays (weekday() == 6)
                     if entry_date.weekday() == 6:
                         # Simulate missing a week occasionally (e.g., 80% completion rate on the target day)
                         if random.random() < 0.80:
                             should_add = True

                # Specific logic for 'Read Book' - make it sparser
                if habit.name == "📚 Read Book":
                     if random.random() < 0.25: # Only 25% chance even if 'daily_all'
                         should_add = True
                     else:
                         should_add = False # Override previous daily check


                if should_add:
                    # Check if entry already exists for this specific habit and date
                    existing_entry = HabitEntry.query.filter_by(
                        habit_id=habit.id,
                        completion_date=entry_date
                    ).first()

                    if not existing_entry:
                        entry = HabitEntry(habit_id=habit.id, completion_date=entry_date)
                        db.session.add(entry)
                        entries_added += 1

            print(f"    Added {entries_added} entries for {habit.name}.")

        # Commit all the new entries
        try:
            db.session.commit()
            print("Habit entries committed successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"Error committing entries: {e}")

        print("Database seeding finished.")


if __name__ == "__main__":
    seed_database()