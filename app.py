# Desktop interface for the rugby gym progression app

import sqlite3
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

import database as db
from algorithms import (
    TARGET_REPS,
    WORKOUT_TYPES,
    build_next_workout,
    calculate_statistics,
    estimated_1rm,
    group_history_by_exercise,
    progressive_overload,
)
from validation import GOALS, POSITIONS

# Main app class - keeping it all together
class RugbyApp:
    BACKGROUND = "#f4f7f6"
    SIDEBAR = "#173f35"
    GREEN = "#087f5b"
    DARK = "#16332b"
    MUTED = "#60746e"

    def __init__(self, root):
        self.root = root
        self.user_id = None
        self.profile = None
        self.exercises = []
        self.content = None # will be set up later
        
        # Window setup
        self.root.title("Rugby Gym Progression")
        self.root.geometry("1100x720")
        self.root.minsize(900, 620)
        self.root.configure(bg=self.BACKGROUND)
        
        self.set_styles()
        
        #Making sure that the database tables exists before adding anything else
        db.initialise_database()
        
        self.show_login()

    def set_styles(self):
        #UI styling using standard Tkinter
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=self.BACKGROUND)
        style.configure("Card.TFrame", background="white")
        style.configure(
            "TLabel",
            background=self.BACKGROUND,
            foreground=self.DARK,
            font=("Arial", 11),
        )
        style.configure(
            "Title.TLabel", font=("Arial", 25, "bold"), foreground=self.DARK
        )
        style.configure(
            "Heading.TLabel", font=("Arial", 15, "bold"), foreground=self.DARK
        )
        style.configure("Muted.TLabel", foreground=self.MUTED)
        style.configure("Card.TLabel", background="white", foreground=self.DARK)
        style.configure(
            "CardHeading.TLabel", background="white", font=("Arial", 14, "bold")
        )
        style.configure("TButton", font=("Arial", 11), padding=(14, 9))
        style.configure("Primary.TButton", background=self.GREEN, foreground="white")
        style.map("Primary.TButton", background=[("active", "#076c4e")])
        style.configure("Treeview", rowheight=28, font=("Arial", 10))
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

    def clear_root(self):
        #Nukes everything in root to redraw screens
        for w in self.root.winfo_children():
            w.destroy()

    def heading(self, title, explanation):
        #Helper to keep page titles consistent
        ttk.Label(self.content, text=title, style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            self.content,
            text=explanation,
            style="Muted.TLabel",
            wraplength=760,
        ).pack(anchor="w", pady=(5, 20))

    def labelled_entry(self, parent, label, variable, row, show=None):
        #Helper to make rows
        ttk.Label(parent, text=label, style="Card.TLabel").grid(
            row=row, column=0, sticky="w", pady=7, padx=(0, 16)
        )
        entry = ttk.Entry(parent, textvariable=variable, show=show, width=32)
        entry.grid(row=row, column=1, sticky="ew", pady=7)
        return entry

    def show_login(self):
        self.clear_root()
        self.login_mode = "login"
        
        outer = ttk.Frame(self.root, padding=45)
        outer.pack(fill="both", expand=True)
        
        panel = ttk.Frame(outer, style="Card.TFrame", padding=36)
        panel.place(relx=0.5, rely=0.5, anchor="center", width=480)
        
        ttk.Label(
            panel,
            text="XV",
            font=("Arial", 18, "bold"),
            foreground=self.GREEN,
            background="white",
        ).pack()
        
        ttk.Label(panel, text="Rugby Gym Progression", style="CardHeading.TLabel").pack(
            pady=(8, 4)
        )
        
        ttk.Label(
            panel,
            text="Record your work. Understand your next step.",
            style="Card.TLabel",
        ).pack(pady=(0, 22))

        mode_row = ttk.Frame(panel, style="Card.TFrame")
        mode_row.pack(fill="x")
        
        ttk.Button(
            mode_row, text="Sign in", command=lambda: self.set_login_mode("login")
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))
        
        ttk.Button(
            mode_row,
            text="Create account",
            command=lambda: self.set_login_mode("register"),
        ).pack(side="left", expand=True, fill="x", padx=(4, 0))
        
        self.form_area = ttk.Frame(panel, style="Card.TFrame")
        self.form_area.pack(fill="x", pady=(20, 0))
        
        self.draw_login_form()

    def set_login_mode(self, mode):
        self.login_mode = mode
        self.draw_login_form()

    def draw_login_form(self):
        for widget in self.form_area.winfo_children():
            widget.destroy()
            
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.confirm_var = tk.StringVar()
        
        username = self.labelled_entry(self.form_area, "Username", self.username_var, 0)
        self.labelled_entry(self.form_area, "Password", self.password_var, 1, show="•")
        
        if self.login_mode == "register":
            self.labelled_entry(
                self.form_area, "Confirm password", self.confirm_var, 2, show="•"
            )
            text = "Use a unique passphrase of at least 12 characters."
            command = self.register
        else:
            text = "Your saved data remains on this computer."
            command = self.login
            
        ttk.Label(self.form_area, text=text, style="Card.TLabel", wraplength=360).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(10, 12)
        )
        
        ttk.Button(
            self.form_area,
            text="Create account" if self.login_mode == "register" else "Sign in",
            style="Primary.TButton",
            command=command,
        ).grid(row=4, column=0, columnspan=2, sticky="ew")
        
        self.form_area.columnconfigure(1, weight=1)
        username.focus_set()

    def register(self):
        try:
            if self.password_var.get() != self.confirm_var.get():
                raise ValueError("The passwords do not match.")
            db.create_account(self.username_var.get(), self.password_var.get())
            messagebox.showinfo(
                "Account created", "Your account was created. Sign in to continue."
            )
            self.set_login_mode("login")
        except (ValueError, sqlite3.Error) as err: # Changed variable name to something shorter
            messagebox.showerror("Cannot create account", str(err))

    def login(self):
        try:
            uid = db.check_login(self.username_var.get(), self.password_var.get())
            if uid is None:
                raise ValueError("Username or password is incorrect.")
            
            self.user_id = uid
            self.profile = db.get_profile(uid)
            self.exercises = db.get_exercises()
            
            self.build_main_window()
            self.show_profile()
        except (ValueError, sqlite3.Error) as err:
            messagebox.showerror("Cannot sign in", str(err))

    def build_main_window(self):
        self.clear_root()
        
        #Sidebar navigation
        sidebar = tk.Frame(self.root, bg=self.SIDEBAR, width=225)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        
        tk.Label(
            sidebar,
            text="XV",
            bg=self.SIDEBAR,
            fg="#a8db63",
            font=("Arial", 20, "bold"),
        ).pack(anchor="w", padx=24, pady=(28, 3))
        
        tk.Label(
            sidebar,
            text="RUGBY PROGRESSION",
            bg=self.SIDEBAR,
            fg="white",
            font=("Arial", 11, "bold"),
        ).pack(anchor="w", padx=24, pady=(0, 24))

        pages = [
            ("Player profile", self.show_profile),
            ("Log workout", self.show_log_workout),
            ("Workout history", self.show_history),
            ("Load guidance", self.show_recommendations),
            ("Next workout plan", self.show_planner),
        ]
        
        for text, command in pages:
            tk.Button(
                sidebar,
                text=text,
                command=command,
                anchor="w",
                relief="flat",
                bg="#a8db63",
                fg="black",
                activebackground="#c7ed98",
                activeforeground="black",
                font=("Arial", 11),
                padx=22,
                pady=11,
                cursor="hand2",
            ).pack(fill="x", pady=2)

        tk.Label(
            sidebar,
            text=f"Signed in as\n{self.profile['username']}",
            bg=self.SIDEBAR,
            fg="#c9d8d3",
            justify="left",
            font=("Arial", 10),
        ).pack(side="bottom", anchor="w", padx=24, pady=(0, 14))
        
        tk.Button(
            sidebar,
            text="Sign out",
            command=self.sign_out,
            relief="flat",
            bg="#a8db63",
            fg="black",
            activebackground="#c7ed98",
            activeforeground="black",
            font=("Arial", 10),
            padx=16,
            pady=8,
        ).pack(side="bottom", fill="x", padx=20, pady=(10, 12))

        # Main content area pane
        self.content = ttk.Frame(self.root, padding=(34, 28))
        self.content.pack(side="left", fill="both", expand=True)

    def clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def sign_out(self):
        self.user_id = None
        self.profile = None
        self.exercises = []
        self.show_login()

    def show_profile(self):
        self.clear_content()
        self.profile = db.get_profile(self.user_id)
        
        self.heading(
            "Player profile",
            "These values give context to your training recommendations.",
        )
        
        form = ttk.Frame(self.content, style="Card.TFrame", padding=24)
        form.pack(fill="x")
        
        self.profile_vars = {
            "age": tk.StringVar(value=self.profile["age"] or ""),
            "height": tk.StringVar(value=self.profile["height"] or ""),
            "body_weight": tk.StringVar(value=self.profile["body_weight"] or ""),
            "position": tk.StringVar(value=self.profile["position"] or POSITIONS[0]),
            "goal": tk.StringVar(value=self.profile["goal"] or GOALS[0]),
        }
        
        self.labelled_entry(form, "Age", self.profile_vars["age"], 0)
        self.labelled_entry(form, "Height (cm)", self.profile_vars["height"], 1)
        self.labelled_entry(
            form, "Body weight (kg)", self.profile_vars["body_weight"], 2
        )
        
        ttk.Label(form, text="Rugby position", style="Card.TLabel").grid(
            row=3, column=0, sticky="w", pady=7
        )
        ttk.Combobox(
            form,
            values=POSITIONS,
            textvariable=self.profile_vars["position"],
            state="readonly",
            width=29,
        ).grid(row=3, column=1, sticky="ew", pady=7)
        
        ttk.Label(form, text="Training goal", style="Card.TLabel").grid(
            row=4, column=0, sticky="w", pady=7
        )
        ttk.Combobox(
            form,
            values=GOALS,
            textvariable=self.profile_vars["goal"],
            state="readonly",
            width=29,
        ).grid(row=4, column=1, sticky="ew", pady=7)
        
        ttk.Button(
            form,
            text="Save profile",
            style="Primary.TButton",
            command=self.save_profile,
        ).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(16, 4))
        
        form.columnconfigure(1, weight=1)
        
        ttk.Label(
            self.content,
            text="Height is recorded, not used to guess a load. Position affects exercise priority, not load size.",
            style="Muted.TLabel",
            wraplength=760,
        ).pack(anchor="w", pady=14)

    def save_profile(self):
        try:
            profile_values = {}
            for key, value in self.profile_vars.items():
                profile_values[key] = value.get()
            db.save_profile(self.user_id, profile_values)
            self.profile = db.get_profile(self.user_id)
            messagebox.showinfo("Profile saved", "Your profile was saved successfully.")
        except (ValueError, sqlite3.Error) as err:
            messagebox.showerror("Cannot save profile", str(err))

    def require_profile(self):
        # makes sure user filled out profile before accessing workout tools
        self.profile = db.get_profile(self.user_id)
        if self.profile["age"] is None:
            messagebox.showwarning(
                "Profile required", "Complete your player profile first."
            )
            self.show_profile()
            return False
        return True

    def get_muscle_groups(self):
        groups = []
        for exercise in self.exercises:
            if exercise["category"] not in groups:
                groups.append(exercise["category"])
        return groups

    def get_exercises_for_group(self, muscle_group):
        exercise_names = []
        for exercise in self.exercises:
            if exercise["category"] == muscle_group:
                exercise_names.append(exercise["name"])
        return exercise_names

    def show_log_workout(self):
        if not self.require_profile():
            return

        self.clear_content()
        self.heading(
            "Log workout",
            "Choose how many exercises you completed, then enter each exercise below.",
        )

        setup = ttk.Frame(self.content, style="Card.TFrame", padding=14)
        setup.pack(fill="x", pady=(0, 14))

        self.workout_date_var = tk.StringVar(value=date.today().isoformat())
        self.exercise_count_var = tk.StringVar(value="1")

        ttk.Label(setup, text="Workout date", style="Card.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 8)
        )
        ttk.Entry(setup, textvariable=self.workout_date_var, width=14).grid(
            row=0, column=1, sticky="w", padx=(0, 24)
        )
        ttk.Label(setup, text="Number of exercises", style="Card.TLabel").grid(
            row=0, column=2, sticky="w", padx=(0, 8)
        )
        ttk.Combobox(
            setup,
            values=list(range(1, 11)),
            textvariable=self.exercise_count_var,
            state="readonly",
            width=5,
        ).grid(row=0, column=3, sticky="w", padx=(0, 14))
        ttk.Button(
            setup, text="Create form", command=self.create_workout_rows
        ).grid(row=0, column=4, sticky="w")

        self.workout_rows_frame = ttk.Frame(self.content, style="Card.TFrame", padding=12)
        self.workout_rows_frame.pack(fill="x")
        self.workout_rows = []
        self.create_workout_rows()

        ttk.Button(
            self.content,
            text="Save whole workout",
            style="Primary.TButton",
            command=self.save_workout,
        ).pack(fill="x", pady=(14, 0))

        ttk.Label(
            self.content,
            text="Each row is one exercise. Only group sets when load, reps, target and RPE are identical. RPE 8 ≈ two reps left; 9 ≈ one; 10 ≈ none.",
            style="Muted.TLabel",
            wraplength=760,
        ).pack(anchor="w", pady=14)

    def create_workout_rows(self):
        for widget in self.workout_rows_frame.winfo_children():
            widget.destroy()

        self.workout_rows = []
        headers = ("#", "Muscle group", "Exercise", "Sets", "Target", "Reps", "Load kg", "RPE")
        for column, heading in enumerate(headers):
            ttk.Label(
                self.workout_rows_frame,
                text=heading,
                style="Card.TLabel",
                font=("Arial", 9, "bold"),
            ).grid(row=0, column=column, padx=3, pady=(0, 7))

        number_of_exercises = int(self.exercise_count_var.get())
        muscle_groups = self.get_muscle_groups()
        target_reps = str(TARGET_REPS[self.profile["goal"]])

        for index in range(number_of_exercises):
            values = {
                "muscle_group": tk.StringVar(value=muscle_groups[0]),
                "exercise": tk.StringVar(),
                "sets": tk.StringVar(value="1"),
                "target_reps": tk.StringVar(value=target_reps),
                "reps": tk.StringVar(value=target_reps),
                "weight": tk.StringVar(),
                "rpe": tk.StringVar(value="7"),
            }

            ttk.Label(
                self.workout_rows_frame, text=str(index + 1), style="Card.TLabel"
            ).grid(row=index + 1, column=0, padx=3, pady=4)

            group_dropdown = ttk.Combobox(
                self.workout_rows_frame,
                values=muscle_groups,
                textvariable=values["muscle_group"],
                state="readonly",
                width=11,
            )
            group_dropdown.grid(row=index + 1, column=1, padx=3, pady=4)

            exercise_dropdown = ttk.Combobox(
                self.workout_rows_frame,
                textvariable=values["exercise"],
                state="readonly",
                width=22,
            )
            exercise_dropdown.grid(row=index + 1, column=2, padx=3, pady=4)

            fields = ("sets", "target_reps", "reps", "weight", "rpe")
            for field_column, field in enumerate(fields, start=3):
                ttk.Entry(
                    self.workout_rows_frame,
                    textvariable=values[field],
                    width=7,
                ).grid(row=index + 1, column=field_column, padx=3, pady=4)

            self.workout_rows.append(
                {"values": values, "exercise_dropdown": exercise_dropdown}
            )
            group_dropdown.bind(
                "<<ComboboxSelected>>",
                lambda event, row_index=index: self.update_workout_row(row_index),
            )
            self.update_workout_row(index)

    def update_workout_row(self, row_index):
        row = self.workout_rows[row_index]
        muscle_group = row["values"]["muscle_group"].get()
        exercise_names = self.get_exercises_for_group(muscle_group)
        row["exercise_dropdown"]["values"] = exercise_names
        if exercise_names:
            row["values"]["exercise"].set(exercise_names[0])
        else:
            row["values"]["exercise"].set("")

    def save_workout(self):
        try:
            workout_date = self.workout_date_var.get()
            entries = []

            for row in self.workout_rows:
                values = row["values"]
                selected_name = values["exercise"].get()
                exercise_id = None

                for exercise in self.exercises:
                    if exercise["name"] == selected_name:
                        exercise_id = exercise["id"]
                        break

                if exercise_id is None:
                    raise ValueError("Choose an exercise for every row.")

                entries.append(
                    {
                        "date": workout_date,
                        "exercise_id": exercise_id,
                        "sets": values["sets"].get(),
                        "target_reps": values["target_reps"].get(),
                        "reps": values["reps"].get(),
                        "weight": values["weight"].get(),
                        "rpe": values["rpe"].get(),
                    }
                )

            db.add_workout_session(self.user_id, entries)
            messagebox.showinfo(
                "Workout saved", "The complete workout was added to your history."
            )
            self.show_history(workout_date)
        except (ValueError, sqlite3.Error) as err:
            messagebox.showerror("Cannot save workout", str(err))

    def make_tree(self, columns, widths, parent=None):
        if parent is None:
            parent = self.content
        holder = ttk.Frame(parent)
        holder.pack(fill="both", expand=True)
        
        tree = ttk.Treeview(
            holder, columns=columns, show="headings", selectmode="browse"
        )
        
        for col, w in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, minwidth=60, anchor="center")
            
        v_scroll = ttk.Scrollbar(
            holder, orient="vertical", command=tree.yview
        )
        h_scroll = ttk.Scrollbar(
            holder, orient="horizontal", command=tree.xview
        )
        
        tree.configure(
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set,
        )
        
        tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        holder.rowconfigure(0, weight=1)
        holder.columnconfigure(0, weight=1)
        return tree

    def show_history(self, selected_date=None):
        if not self.require_profile():
            return

        self.clear_content()
        self.all_history = db.get_history(self.user_id)

        self.heading(
            "Workout history",
            "Choose a workout date to view its exercises and calculated results.",
        )

        workout_dates = []
        for entry in self.all_history:
            if entry["date"] not in workout_dates:
                workout_dates.append(entry["date"])

        if not workout_dates:
            ttk.Label(
                self.content, text="No workouts saved yet.", style="Muted.TLabel"
            ).pack(pady=20)
            return

        if selected_date not in workout_dates:
            selected_date = workout_dates[0]

        date_row = ttk.Frame(self.content)
        date_row.pack(fill="x", pady=(0, 16))
        ttk.Label(date_row, text="Workout date").pack(side="left", padx=(0, 12))

        self.history_date_var = tk.StringVar(value=selected_date)
        date_dropdown = ttk.Combobox(
            date_row,
            values=workout_dates,
            textvariable=self.history_date_var,
            state="readonly",
            width=18,
        )
        date_dropdown.pack(side="left")
        date_dropdown.bind("<<ComboboxSelected>>", self.update_history_view)
        ttk.Button(
            date_row, text="View workout", command=self.update_history_view
        ).pack(side="left", padx=(10, 0))

        self.history_details = ttk.Frame(self.content)
        self.history_details.pack(fill="both", expand=True)
        self.update_history_view()

    def update_history_view(self, event=None):
        for widget in self.history_details.winfo_children():
            widget.destroy()

        selected_date = self.history_date_var.get()
        workout = []
        for entry in self.all_history:
            if entry["date"] == selected_date:
                workout.append(entry)

        statistics = calculate_statistics(workout)
        exercise_names = set()
        for entry in workout:
            exercise_names.add(entry["exercise"])

        summary = ttk.Frame(self.history_details, style="Card.TFrame", padding=14)
        summary.pack(fill="x", pady=(0, 16))
        summary_values = [
            ("Exercises", len(exercise_names)),
            ("Working sets", statistics["sets"]),
            ("Total volume", f"{statistics['volume']:,.0f} kg"),
            ("Average RPE", statistics["average_rpe"] or "—"),
        ]

        for index, (label, value) in enumerate(summary_values):
            card = ttk.Frame(summary, style="Card.TFrame", padding=8)
            card.grid(row=0, column=index, sticky="nsew")
            ttk.Label(card, text=str(value), style="CardHeading.TLabel").pack()
            ttk.Label(card, text=label, style="Card.TLabel").pack()
            summary.columnconfigure(index, weight=1)

        columns = (
            "ID",
            "Exercise",
            "Sets",
            "Target",
            "Reps",
            "Load",
            "RPE",
            "Est. 1RM",
        )
        widths = (50, 180, 60, 65, 60, 75, 60, 90)
        self.history_tree = self.make_tree(columns, widths, self.history_details)

        for entry in workout:
            one_rep_max = estimated_1rm(entry["weight"], entry["reps"])
            displayed_max = "—" if one_rep_max is None else f"{one_rep_max:g} kg"
            self.history_tree.insert(
                "",
                "end",
                iid=str(entry["id"]),
                values=(
                    entry["id"],
                    entry["exercise"],
                    entry["sets"],
                    entry["target_reps"],
                    entry["reps"],
                    f"{entry['weight']:g} kg",
                    f"{entry['rpe']:g}",
                    displayed_max,
                ),
            )

        ttk.Button(
            self.history_details,
            text="Delete selected exercise",
            command=self.delete_selected,
        ).pack(anchor="e", pady=(12, 0))

    def delete_selected(self):
        selected = self.history_tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Select one history row first.")
            return
            
        if messagebox.askyesno(
            "Delete entry", "Permanently delete the selected workout entry?"
        ):
            try:
                selected_date = self.history_date_var.get()
                db.delete_workout(self.user_id, int(selected[0]))
                self.show_history(selected_date)
            except (ValueError, sqlite3.Error) as err:
                messagebox.showerror("Cannot delete entry", str(err))

    def update_guidance_table(self, event=None):
        for row_id in self.guidance_tree.get_children():
            self.guidance_tree.delete(row_id)

        selected_group = self.guidance_group_var.get()
        for exercise in self.exercises:
            if exercise["category"] == selected_group:
                weight, action, reason = progressive_overload(
                    self.guidance_history.get(exercise["id"], []), self.profile
                )
                displayed_weight = "—" if weight is None else f"{weight:g} kg"
                self.guidance_tree.insert(
                    "",
                    "end",
                    values=(exercise["name"], action, displayed_weight, reason),
                )

    def show_recommendations(self, selected_group=None):
        if not self.require_profile():
            return
            
        self.clear_content()
        history = db.get_history(self.user_id)
        self.guidance_history = group_history_by_exercise(history)
        
        self.heading(
            "Load guidance",
            "Current recommendations are recalculated from your saved history.",
        )

        muscle_groups = self.get_muscle_groups()
        if selected_group not in muscle_groups:
            selected_group = muscle_groups[0]

        category_row = ttk.Frame(self.content)
        category_row.pack(fill="x", pady=(0, 16))
        ttk.Label(category_row, text="Muscle group").pack(side="left", padx=(0, 12))

        self.guidance_group_var = tk.StringVar(value=selected_group)
        guidance_dropdown = ttk.Combobox(
            category_row,
            values=muscle_groups,
            textvariable=self.guidance_group_var,
            state="readonly",
            width=24,
        )
        guidance_dropdown.pack(side="left")
        guidance_dropdown.bind("<<ComboboxSelected>>", self.update_guidance_table)
        
        columns = ("Exercise", "Action", "Suggested load", "Reason")
        self.guidance_tree = self.make_tree(columns, (150, 105, 115, 430))
        self.update_guidance_table()
            
        ttk.Label(
            self.content,
            text="These rules are training guidance, not medical advice or a validated rugby programme. Never continue through pain or poor technique.",
            style="Muted.TLabel",
            wraplength=780,
        ).pack(anchor="w", pady=12)

    def show_planner(self):
        if not self.require_profile():
            return

        self.clear_content()
        self.planner_history = db.get_history(self.user_id)

        self.heading(
            "Next workout plan",
            "Choose a workout type to receive five exercise suggestions.",
        )

        option_row = ttk.Frame(self.content)
        option_row.pack(fill="x", pady=(0, 16))
        ttk.Label(option_row, text="Workout type").pack(side="left", padx=(0, 12))

        self.workout_type_var = tk.StringVar(value=WORKOUT_TYPES[0])
        workout_dropdown = ttk.Combobox(
            option_row,
            values=WORKOUT_TYPES,
            textvariable=self.workout_type_var,
            state="readonly",
            width=22,
        )
        workout_dropdown.pack(side="left")
        workout_dropdown.bind("<<ComboboxSelected>>", self.update_planner_table)
        ttk.Button(
            option_row, text="Show workout", command=self.update_planner_table
        ).pack(side="left", padx=(10, 0))

        columns = (
            "Exercise",
            "Category",
            "Sets",
            "Target reps",
            "Load guidance",
            "Why selected",
        )

        self.planner_tree = self.make_tree(columns, (160, 100, 60, 85, 125, 290))
        self.update_planner_table()

        ttk.Label(
            self.content,
            text="Sets and target reps are based on your training goal. Exercise choice also considers training recency, recent RPE and load guidance.",
            style="Muted.TLabel",
            wraplength=780,
        ).pack(anchor="w", pady=12)

    def update_planner_table(self, event=None):
        for row_id in self.planner_tree.get_children():
            self.planner_tree.delete(row_id)

        workout_type = self.workout_type_var.get()
        plan = build_next_workout(
            self.exercises,
            self.planner_history,
            self.profile,
            workout_type,
        )

        for item in plan:
            load = (
                item["action"]
                if item["next_weight"] is None
                else f"{item['next_weight']:g} kg · {item['action']}"
            )
            self.planner_tree.insert(
                "",
                "end",
                values=(
                    item["exercise"],
                    item["category"],
                    item["sets"],
                    item["target_reps"],
                    load,
                    item["reason"],
                ),
            )


def main():
    root = tk.Tk()
    RugbyApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
