# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime

db = SQLAlchemy()

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False) # Can include emojis
    frequency_type = db.Column(db.String(20), nullable=False) # 'daily_all', 'daily_weekdays', 'weekly'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False) # For soft deletes

    # Relationship to track completions
    entries = db.relationship('HabitEntry', backref='habit', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Habit {self.name}>'

class HabitEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=False)
    completion_date = db.Column(db.Date, nullable=False, default=date.today)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow) # Exact time of completion

    # Ensure a habit can only be marked complete once per day
    __table_args__ = (db.UniqueConstraint('habit_id', 'completion_date', name='_habit_date_uc'),)

    def __repr__(self):
        return f'<HabitEntry {self.habit.name} on {self.completion_date}>'