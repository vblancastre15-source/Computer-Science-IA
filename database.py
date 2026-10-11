#database - This is the sqlite handler for the rugby app

import hashlib
import hmac
import os
import secrets
import sqlite3
from contextlib import closing
from pathlib import Path

#validation functions from validations file
from validation import check_profile, check_username, check_workout

#db path - lets check environment variable first, otherwise put it in data/rugby.db
DATABASE = Path(
    os.environ.get("RUGBY_IA_DATABASE", Path(__file__).parent / "data" / "rugby.db")
)

#adding 10 exercises for each part of the body for the default db

EXERCISES = [
    #Chest
    ("Barbell bench press", "Chest"),
    ("Incline dumbbell press", "Chest"),
    ("Decline bench press", "Chest"),
    ("Dumbbell chest fly", "Chest"),
    ("Cable chest fly", "Chest"),
    ("Chest press machine", "Chest"),
    ("Pec deck fly", "Chest"),
    ("Weighted dips", "Chest"),
    ("Incline barbell bench press", "Chest"),
    ("Push-ups", "Chest"),

    #Back
    ("Pull-ups", "Back"),
    ("Lat pulldown", "Back"),
    ("Barbell bent-over row", "Back"),
    ("Seated cable row", "Back"),
    ("Single-arm dumbbell row", "Back"),
    ("T-bar row", "Back"),
    ("Chest-supported row", "Back"),
    ("Straight-arm pulldown", "Back"),
    ("Deadlift", "Back"),
    ("Close-grip lat pulldown", "Back"),

    #Shoulders
    ("Dumbbell shoulder press", "Shoulders"),
    ("Barbell overhead press", "Shoulders"),
    ("Dumbbell lateral raise", "Shoulders"),
    ("Cable lateral raise", "Shoulders"),
    ("Reverse pec deck fly", "Shoulders"),
    ("Face pull", "Shoulders"),
    ("Rear delt dumbbell fly", "Shoulders"),
    ("Arnold press", "Shoulders"),
    ("Front dumbbell raise", "Shoulders"),
    ("Machine shoulder press", "Shoulders"),

    #Biceps
    ("Barbell biceps curl", "Biceps"),
    ("Dumbbell curls", "Biceps"),
    ("Hammer curl", "Biceps"),
    ("Preacher curl", "Biceps"),
    ("Incline dumbbell curl", "Biceps"),
    ("Cable biceps curl", "Biceps"),
    ("Concentration curl", "Biceps"),
    ("EZ-bar curl", "Biceps"),
    ("Reverse grip curl", "Biceps"),
    ("Spider curl", "Biceps"),

    #Triceps
    ("Cable triceps pushdown", "Triceps"),
    ("Overhead triceps extension", "Triceps"),
    ("Skull crushers", "Triceps"),
    ("Close-grip bench press", "Triceps"),
    ("Single-arm cable triceps extension", "Triceps"),
    ("Rope triceps pushdown", "Triceps"),
    ("Dumbbell triceps kickback", "Triceps"),
    ("EZ-bar overhead extension", "Triceps"),
    ("Triceps dip machine", "Triceps"),
    ("Diamond push-ups", "Triceps"),

    #Legs
    ("Barbell back squat", "Legs"),
    ("Front squat", "Legs"),
    ("Leg press", "Legs"),
    ("Bulgarian split squat", "Legs"),
    ("Walking lunges", "Legs"),
    ("Leg extension", "Legs"),
    ("Seated leg curl", "Legs"),
    ("Romanian deadlift", "Legs"),
    ("Hip thrust", "Legs"),
    ("Standing calf raise", "Legs"),

    #Core
    ("Hanging leg raises", "Core"),
    ("Cable crunches", "Core"),
    ("Weighted sit-ups", "Core"),
    ("Russian twists", "Core"),
    ("Ab wheel rollouts", "Core"),
    ("Plank", "Core"),
    ("Side plank", "Core"),
    ("Bicycle crunches", "Core"),
    ("Reverse crunches", "Core"),
    ("Pallof press", "Core")
]

def connect():
    # Helper to grab a db connection. Don't forget to close it!
    conn = sqlite3.connect(DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialise_database():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    
    with closing(connect()) as connection:
        #creating tables... 
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                age INTEGER,
                height REAL,
                body_weight REAL,
                position TEXT,
                goal TEXT
            );

            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS workout_entries (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                exercise_id INTEGER NOT NULL REFERENCES exercises(id),
                date TEXT NOT NULL,
                sets INTEGER NOT NULL CHECK(sets BETWEEN 1 AND 20),
                reps INTEGER NOT NULL CHECK(reps BETWEEN 0 AND 30),
                target_reps INTEGER NOT NULL CHECK(target_reps BETWEEN 1 AND 30),
                weight REAL NOT NULL CHECK(weight BETWEEN 0 AND 500),
                rpe REAL NOT NULL CHECK(rpe BETWEEN 1 AND 10)
            );

            CREATE INDEX IF NOT EXISTS entries_user_date
            ON workout_entries(user_id, date DESC);
        """)
        
        #Insert default exercises if they dont exist yet
        for name, category in EXERCISES:
            connection.execute(
                "INSERT OR IGNORE INTO exercises(name, category) VALUES (?, ?)",
                (name, category),
            )
            
        connection.commit()
    print("Database check complete!") # just a little debug print


def make_password_hash(password, salt):
    # Using 600k iterations as recommended for pbkdf2_hmac nowadays
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), 600_000
    ).hex()


def create_account(username, password):
    username = check_username(username)
    
    #basic password length check
    if not 12 <= len(password) <= 128 or not password.strip():
        raise ValueError("Use a password or passphrase of 12–128 characters.")
        
    salt = secrets.token_hex(16)
    
    with closing(connect()) as connection:
        try:
            connection.execute(
                "INSERT INTO users(username, password_hash, salt) VALUES (?, ?, ?)",
                (username, make_password_hash(password, salt), salt),
            )
            connection.commit()
        except sqlite3.IntegrityError:
            raise ValueError("That username is already taken.") from None


def check_login(username, password):
    if not isinstance(password, str) or not 1 <= len(password) <= 128:
        return None
        
    with closing(connect()) as connection:
        user = connection.execute(
            "SELECT id, password_hash, salt FROM users WHERE username=?",
            (username.strip().lower(),),
        ).fetchone()
        
    if user and hmac.compare_digest(
        user["password_hash"], make_password_hash(password, user["salt"])
    ):
        return user["id"]
        
    return None


def get_profile(user_id):
    with closing(connect()) as connection:
        user = connection.execute(
            "SELECT username, age, height, body_weight, position, goal FROM users WHERE id=?",
            (user_id,),
        ).fetchone()
        
    if user is None:
        raise ValueError("Account not found. Sign in again.")
        
    return dict(user)


def save_profile(user_id, profile):
    profile = check_profile(profile)
    
    with closing(connect()) as connection:
        cursor = connection.execute(
            """UPDATE users SET age=?, height=?, body_weight=?, position=?, goal=?
               WHERE id=?""",
            (
                profile["age"],
                profile["height"],
                profile["body_weight"],
                profile["position"],
                profile["goal"],
                user_id,
            ),
        )
        if cursor.rowcount != 1:
            raise ValueError("Account not found. Sign in again.")
            
        connection.commit()


def get_exercises():
    #returning all exercises so the frontend can populate dropdowns
    with closing(connect()) as connection:
        exercise_rows = connection.execute(
            "SELECT id, name, category FROM exercises ORDER BY id"
        ).fetchall()
        
    #converting rows to dicts manually 
    exercises = []
    for exercise in exercise_rows:
        exercises.append(dict(exercise))
        
    return exercises


def add_workout(user_id, entry):
    entry = check_workout(entry)
    
    #make sure user filled out their profile first
    user_prof = get_profile(user_id)
    if user_prof["age"] is None:
        raise ValueError("Complete your player profile before logging a workout.")
        
    with closing(connect()) as connection:
        exercise = connection.execute(
            "SELECT id FROM exercises WHERE id=?", (entry["exercise_id"],)
        ).fetchone()
        
        if exercise is None:
            raise ValueError("Choose an exercise from the list.")
            
        connection.execute(
            """INSERT INTO workout_entries
               (user_id, exercise_id, date, sets, reps, target_reps, weight, rpe)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                entry["exercise_id"],
                entry["date"],
                entry["sets"],
                entry["reps"],
                entry["target_reps"],
                entry["weight"],
                entry["rpe"],
            ),
        )
        connection.commit()


def get_history(user_id):
    with closing(connect()) as connection:
        workout_rows = connection.execute(
            """SELECT w.*, e.name AS exercise, e.category
               FROM workout_entries AS w
               JOIN exercises AS e ON w.exercise_id=e.id
               WHERE w.user_id=?
               ORDER BY w.date DESC, w.id DESC""",
            (user_id,),
        ).fetchall()
        
    #again, doing a manual loop as it is easy to read when debugging
    history = []
    for workout in workout_rows:
        history.append(dict(workout))
        
    return history


def delete_workout(user_id, entry_id):
    with closing(connect()) as connection:
        cursor = connection.execute(
            "DELETE FROM workout_entries WHERE id=? AND user_id=?", (entry_id, user_id)
        )
        if cursor.rowcount != 1:
            raise ValueError("Workout entry not found for this account.")
            
        connection.commit()
