#Validation checks for the inputs

import math
import re
from datetime import date

#Implementing Rugby positions for profile
POSITIONS = [
    "Prop",
    "Hooker",
    "Lock",
    "Flanker",
    "Number eight",
    "Scrum-half",
    "Fly-half",
    "Centre",
    "Wing",
    "Full-back",
]

#Training goals in which the user wants the application to be used for
GOALS = ["Strength", "Muscle gain", "Power", "General conditioning"]


def check_number(value, label, minimum, maximum, whole_number=False):
    #Convert a value to a number and check its permitted range.
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a number.")
        
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f"{label} must be a number.") from None
        
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise ValueError(f"{label} must be between {minimum} and {maximum}.")
        
    if whole_number and not number.is_integer():
        raise ValueError(f"{label} must be a whole number.")
        
    return int(number) if whole_number else number


def check_username(username):
    username = username.strip().lower()
    
    #In username only lowercase letters, numbers, and underscores allowed
    if not re.fullmatch(r"[a-z0-9_]{3,30}", username):
        raise ValueError("Username: use 3–30 letters, numbers or underscores.")
        
    return username


def check_profile(profile):
    #Check if position has been entered
    if profile["position"] not in POSITIONS:
        raise ValueError("Choose a listed rugby position.")
        
    #Check if goak has been entered
    if profile["goal"] not in GOALS:
        raise ValueError("Choose a listed training goal.")
        
    #Returning cleaned profile data using check_number helper
    validated_data = {
        "age": check_number(profile["age"], "Age", 13, 100, True),
        "height": check_number(profile["height"], "Height", 100, 250),
        "body_weight": check_number(profile["body_weight"], "Body weight", 30, 300),
        "position": profile["position"],
        "goal": profile["goal"],
    }
    
    return validated_data


def check_workout(entry):
    #Checking date format - must be valid iso date string
    try:
        workout_date = date.fromisoformat(str(entry["date"]))
    except (TypeError, ValueError):
        raise ValueError("Enter the date as YYYY-MM-DD.") from None
        
    #Ensure the date entered is from today, not in the future or the past
    if not date(2025, 1, 1) <= workout_date <= date.today():
        raise ValueError("Workout date must be between 1 January 2025 and today.")
        
    #Return an entry without errors
    clean_entry = {
        "date": workout_date.isoformat(),
        "exercise_id": check_number(entry["exercise_id"], "Exercise", 1, 1000, True),
        "sets": check_number(entry["sets"], "Sets", 1, 20, True),
        "reps": check_number(entry["reps"], "Completed reps", 0, 30, True),
        "target_reps": check_number(entry["target_reps"], "Planned reps", 1, 30, True),
        "weight": check_number(entry["weight"], "Load", 0, 500),
        "rpe": check_number(entry["rpe"], "RPE", 1, 10),
    }
    
    return clean_entry
