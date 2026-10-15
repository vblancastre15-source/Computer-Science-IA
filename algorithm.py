# algorithms.py - Workout tracker logic

import math
from datetime import date

TARGET_REPS = {
    "Strength": 5, 
    "Muscle gain": 8, 
    "Power": 3, 
    "General conditioning": 10
}

TARGET_SETS = {
    "Strength": 4,
    "Muscle gain": 3,
    "Power": 4,
    "General conditioning": 3,
}

WORKOUT_TYPES = ["Legs", "Arms", "Full upper body", "Lower body", "Core"]

LEG_WORKOUT_EXERCISES = [
    "Barbell back squat",
    "Leg press",
    "Bulgarian split squat",
    "Leg extension",
    "Standing calf raise",
]

LOWER_BODY_EXERCISES = [
    "Front squat",
    "Walking lunges",
    "Seated leg curl",
    "Romanian deadlift",
    "Hip thrust",
]


def calculate_volume(entry):
    #Volume calculation formula: sets * reps * weight
    return entry["sets"] * entry["reps"] * entry["weight"]


def estimated_1rm(weight, reps):
    #Epley formula for 1RM estimation
    if weight <= 0 or reps < 1 or reps > 10:
        return None
    if reps == 1:
        return weight
    
    #Rounding
    val = weight * (1 + reps / 30)
    return round(val, 1)


def group_history_by_exercise(history):
    grouped = {}
    #Looping through to group by exercise ID
    for item in history:
        ex_id = item["exercise_id"]
        if ex_id not in grouped:
            grouped[ex_id] = []
        grouped[ex_id].append(item)
    return grouped


def progressive_overload(history, profile):
    #Recommend the next load according to history of one exercise.
    if not history:
        return None, "Baseline", "Choose a starting load with your coach."

    #get unique workout dates
    dates = set()
    for entry in history:
        dates.add(entry["date"])
    
    workout_dates = sorted(dates, reverse=True)

    latest_entries = []
    for entry in history:
        if entry["date"] == workout_dates[0]:
            latest_entries.append(entry)
            
    weight = latest_entries[0]["weight"]

    # checking age profile restrictions
    if profile["age"] < 18:
        return (
            None,
            "Coach review",
            "Under-18 player: agree loads with a youth strength coach.",
        )
        
    if profile["goal"] == "Power":
        return (
            None,
            "Coach review",
            "Power work needs technique and movement-speed feedback.",
        )
        
    # check if person hasn't trained in a while
    latest_date_obj = date.fromisoformat(workout_dates[0])
    if (date.today() - latest_date_obj).days > 21:
        return None, "Coach review", "The latest record is over 21 days old."
        
    mixed_loads = False
    for entry in latest_entries:
        if entry["weight"] != weight:
            mixed_loads = True
            break
            
    if weight == 0 or mixed_loads:
        return (
            None,
            "Coach review",
            "The latest session has zero or mixed working loads.",
        )

    missed_target = False
    very_high_effort = False
    effort_above_eight = False
    
    for entry in latest_entries:
        if entry["reps"] < entry["target_reps"]:
            missed_target = True
        if entry["rpe"] >= 9.5:
            very_high_effort = True
        if entry["rpe"] > 8:
            effort_above_eight = True
            
    if missed_target or very_high_effort:
        reduced = math.floor(weight * 0.95 / 2.5) * 2.5
        if 0 < reduced < weight and reduced >= weight * 0.90:
            return reduced, "Reduce", "A rep target was missed or RPE reached 9.5–10."
        return weight, "Hold", "A 2.5 kg reduction would be too large."

    if effort_above_eight:
        return weight, "Hold", "Effort was above RPE 8. Do not force extra repetitions."
        
    if len(workout_dates) < 2:
        return weight, "Hold", "Log a second comparable session before increasing."

    previous_entries = []
    for entry in history:
        if entry["date"] == workout_dates[1]:
            previous_entries.append(entry)
            
    prev_date_obj = date.fromisoformat(workout_dates[1])
    gap = (latest_date_obj - prev_date_obj).days
    
    if gap > 21:
        return (
            weight,
            "Hold",
            "The previous comparable session is over 21 days earlier.",
        )

    latest_sets = 0
    for entry in latest_entries:
        latest_sets += entry["sets"]

    previous_sets = 0
    for entry in previous_entries:
        previous_sets += entry["sets"]
        
    if latest_sets < 2 or latest_sets != previous_sets:
        return weight, "Hold", "Use the same total set count, with at least two sets."

    for entry in latest_entries + previous_entries:
        same_load = entry["weight"] == weight
        same_target = entry["target_reps"] == latest_entries[0]["target_reps"]
        goal_target = TARGET_REPS[profile["goal"]]
        successful = entry["reps"] >= max(entry["target_reps"], goal_target) + 1
        manageable = entry["rpe"] <= 8
        if not (same_load and same_target and successful and manageable):
            return (
                weight,
                "Hold",
                "Both sessions must meet the same load, target and effort rules.",
            )

    increased = weight + 2.5
    percentage_increase = 2.5 / weight
    if increased > 500 or not (0.02 <= percentage_increase <= 0.05):
        return weight, "Hold", "A 2.5 kg step is outside the permitted 2–5% increase."
        
    return increased, "Increase", "Both comparable sessions met the progression rules."


def exercise_matches_workout(exercise, workout_type):
    if workout_type == "Legs":
        return exercise["name"] in LEG_WORKOUT_EXERCISES
    if workout_type == "Lower body":
        return exercise["name"] in LOWER_BODY_EXERCISES
    if workout_type == "Arms":
        return exercise["category"] == "Biceps" or exercise["category"] == "Triceps"
    if workout_type == "Full upper body":
        upper_categories = ["Chest", "Back", "Shoulders", "Biceps", "Triceps"]
        return exercise["category"] in upper_categories
    if workout_type == "Core":
        return exercise["category"] == "Core"
    return False


def build_next_workout(exercises, history, profile, workout_type="Full upper body", today=None):
    today = today or date.today()
    grouped_history = group_history_by_exercise(history)
    candidates = []

    for exercise in exercises:
        if not exercise_matches_workout(exercise, workout_type):
            continue

        exercise_history = grouped_history.get(exercise["id"], [])
        score = 0
        reasons = []

        if not exercise_history:
            score += 2
            reasons.append("not trained yet")
        else:
            latest_date = date.fromisoformat(exercise_history[0]["date"])
            days_since = (today - latest_date).days
            latest_rpe = 0
            
            for entry in exercise_history:
                if entry["date"] == exercise_history[0]["date"]:
                    if entry["rpe"] > latest_rpe:
                        latest_rpe = entry["rpe"]
                        
            if days_since >= 7:
                score += 2
                reasons.append("not trained for 7+ days")
            elif 3 <= days_since <= 6:
                score += 1
                reasons.append("not trained for 3–6 days")
            elif days_since <= 1:
                score -= 3
                reasons.append("trained in the last 48 hours")
                
            if latest_rpe >= 9:
                score -= 2
                reasons.append("recent RPE was high")

        next_weight, action, progression_reason = progressive_overload(
            exercise_history, profile
        )
        
        if action == "Increase":
            score += 1
            reasons.append("ready to progress")
        elif action == "Reduce" or action == "Coach review":
            score -= 2
            reasons.append(action.lower())

        candidates.append(
            {
                "exercise": exercise["name"],
                "category": exercise["category"],
                "score": score,
                "sets": TARGET_SETS[profile["goal"]],
                "target_reps": TARGET_REPS[profile["goal"]],
                "next_weight": next_weight,
                "action": action,
                "reason": ", ".join(reasons) or "balanced option",
                "progression_reason": progression_reason,
            }
        )

    selected = []
    category_counts = {}

    category_limit = 5
    if workout_type == "Arms":
        category_limit = 3
    elif workout_type == "Full upper body":
        category_limit = 1

    while candidates and len(selected) < 5:
        best_index = 0
        for index in range(1, len(candidates)):
            if candidates[index]["score"] > candidates[best_index]["score"]:
                best_index = index
                
        best_exercise = candidates.pop(best_index)
        category = best_exercise["category"]
        category_count = category_counts.get(category, 0)
        
        if category_count < category_limit:
            selected.append(best_exercise)
            category_counts[category] = category_count + 1

    return selected


def calculate_statistics(history):
    #Calculating summary values from workout history
    sessions = set()
    total_sets = 0
    total_volume = 0
    total_rpe = 0
    exercise_counts = {}
    best_estimate = None

    for entry in history:
        sessions.add(entry["date"])
        total_sets += entry["sets"]
        total_volume += calculate_volume(entry)
        total_rpe += entry["rpe"] * entry["sets"]
        
        ex_name = entry["exercise"]
        exercise_counts[ex_name] = exercise_counts.get(ex_name, 0) + entry["sets"]
        
        estimate = estimated_1rm(entry["weight"], entry["reps"])
        if estimate is not None and (best_estimate is None or estimate > best_estimate):
            best_estimate = estimate

    most_trained = "—"
    highest_count = 0
    for exercise, count in exercise_counts.items():
        if count > highest_count:
            most_trained = exercise
            highest_count = count

    average_rpe = round(total_rpe / total_sets, 1) if total_sets else None
    
    return {
        "sessions": len(sessions),
        "sets": total_sets,
        "volume": round(total_volume, 1),
        "average_rpe": average_rpe,
        "best_estimated_1rm": best_estimate,
        "most_trained": most_trained,
    }
