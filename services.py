# services.py
from datetime import date, timedelta
from models import Habit, HabitEntry, db # Assuming models.py is in the same directory

def get_habit_status_for_day(habit: Habit, target_date: date = date.today()):
    """Determines if a habit is pending, done today, or done this week."""
    start_of_week = target_date - timedelta(days=target_date.weekday()) # Monday is 0

    # Check if completed today
    completed_today = HabitEntry.query.filter_by(
        habit_id=habit.id,
        completion_date=target_date
    ).first() is not None

    if completed_today:
        return "done_today"

    # If weekly, check if completed this week (and not today)
    if habit.frequency_type == 'weekly':
        completed_this_week = HabitEntry.query.filter(
            HabitEntry.habit_id == habit.id,
            HabitEntry.completion_date >= start_of_week,
            HabitEntry.completion_date <= target_date # Up to today
        ).first() is not None
        if completed_this_week:
             # Considered done this week if completed on a previous day of the week
            return "done_this_week"

    # Check if the habit should be pending today
    is_weekday = target_date.weekday() < 5 # Monday=0, Friday=4

    if habit.frequency_type == 'daily_all':
        return "pending"
    elif habit.frequency_type == 'daily_weekdays' and is_weekday:
        return "pending"
    elif habit.frequency_type == 'weekly':
         # Weekly tasks are always pending at the start of the week until completed
         # If not completed_this_week and not completed_today, it's pending
        return "pending"
    else:
        # e.g., It's a weekend and the habit is weekdays only
        return "not_applicable_today" # Or some other status


def calculate_streaks(habit_id: int):
    """Calculates the current and best streaks for a habit."""
    entries = HabitEntry.query.filter_by(habit_id=habit_id)\
                              .order_by(HabitEntry.completion_date.desc())\
                              .all()

    if not entries:
        return {"current_streak": 0, "best_streak": 0, "completion_dates": []}

    habit = Habit.query.get(habit_id)
    if not habit:
        return {"current_streak": 0, "best_streak": 0, "completion_dates": []}

    completion_dates = sorted([e.completion_date for e in entries])
    if not completion_dates:
         return {"current_streak": 0, "best_streak": 0, "completion_dates": []}


    today = date.today()
    current_streak = 0
    best_streak = 0
    current_run = 0

    # Calculate current streak
    temp_streak = 0
    last_date = None # Keep track of the last date checked

    # Check from today backwards
    check_date = today
    is_first_check = True # Handle case where today is the first completion day

    # Determine the decrement logic based on frequency
    if habit.frequency_type == 'daily_all':
        decrement = lambda d: d - timedelta(days=1)
        is_valid_day = lambda d: True
    elif habit.frequency_type == 'daily_weekdays':
        decrement = lambda d: d - timedelta(days=1)
        is_valid_day = lambda d: d.weekday() < 5
    elif habit.frequency_type == 'weekly':
        # For weekly, we check if *any* day in the previous week was completed
        # This logic is more complex - simplified for now: check if *last monday* had a completion in its week
        # A more robust weekly streak might need a different definition (e.g., completed every week without fail)
        # Simplified: treat as daily for streak calculation for now
        decrement = lambda d: d - timedelta(days=1)
        is_valid_day = lambda d: True # Simplified weekly streak
    else:
         decrement = lambda d: d - timedelta(days=1)
         is_valid_day = lambda d: True

    # Check current streak working backwards from today/yesterday
    yesterday = today - timedelta(days=1)
    # Start checking from today only if it was completed today or yesterday
    # and it was a valid day for the habit
    initial_check_date = None
    if today in completion_dates and is_valid_day(today):
        initial_check_date = today
    elif yesterday in completion_dates and is_valid_day(yesterday):
         initial_check_date = yesterday

    if initial_check_date:
        check_date = initial_check_date
        while True:
             if is_valid_day(check_date):
                 if check_date in completion_dates:
                     temp_streak += 1
                 else:
                     break # Streak broken
             # Move to the previous day regardless of validity,
             # but only count valid days where it was completed.
             check_date = decrement(check_date)
             # Safety break (e.g., don't go back indefinitely if logic is flawed)
             if check_date < completion_dates[0] - timedelta(days=1):
                 break
        current_streak = temp_streak


    # Calculate best streak iterating through all completion dates
    if completion_dates:
        best_run = 0
        current_run = 0
        expected_date = None

        # Sort dates ascending for best streak calculation
        sorted_dates = sorted(list(set(completion_dates))) # Unique dates, sorted

        for i, current_date in enumerate(sorted_dates):
             # Skip if not a valid day for the habit type (e.g., weekend for weekdays)
             if not is_valid_day(current_date):
                 continue

             if i == 0: # First entry starts a run of 1
                 current_run = 1
             else:
                 # Determine the expected previous date based on frequency
                 prev_date_in_list = sorted_dates[i-1]
                 # Find the *actual* previous valid day before current_date
                 expected_prev_date = current_date
                 while True:
                     expected_prev_date = decrement(expected_prev_date)
                     if is_valid_day(expected_prev_date):
                         break
                     # Safety break
                     if expected_prev_date < sorted_dates[0] - timedelta(days=1):
                         break


                 if prev_date_in_list == expected_prev_date:
                     # Dates are consecutive according to frequency rules
                     current_run += 1
                 else:
                     # Streak broken, start new run
                      best_run = max(best_run, current_run)
                      current_run = 1 # Start new streak

             best_run = max(best_run, current_run) # Update best run at the end of each iteration

        best_streak = best_run


    return {
        "current_streak": current_streak,
        "best_streak": best_streak,
        "completion_dates": [d.isoformat() for d in completion_dates] # Return dates as strings
    }