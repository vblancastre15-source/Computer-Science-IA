# Desktop interface for the rugby gym progression app

import sqlite3
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

import database as db
from algorithms import (
    TARGET_REPS,
    build_next_workout,
    calculate_statistics,
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
                bg=self.SIDEBAR,
                fg="white",
                activebackground="#245b4e",
                activeforeground="white",
                font=("Arial", 11),
                padx=22,
                pady=11,
                cursor="hand2",
            ).pack(fill="x")

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
            bg="#245b4e",
            fg="white",
            activebackground="#2d6b5c",
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

    def show_log_workout(self):
        if not self.require_profile():
            return
            
        self.clear_content()
        self.heading(
            "Log workout",
            "Save one exercise at a time. The same date represents one session.",
        )
        
        form = ttk.Frame(self.content, style="Card.TFrame", padding=22)
        form.pack(fill="x")
        
        self.workout_vars = {
            "date": tk.StringVar(value=date.today().isoformat()),
            "exercise": tk.StringVar(value=self.exercises[0]["name"]),
            "sets": tk.StringVar(value="1"),
            "target_reps": tk.StringVar(value=str(TARGET_REPS[self.profile["goal"]])),
            "reps": tk.StringVar(value=str(TARGET_REPS[self.profile["goal"]])),
            "weight": tk.StringVar(),
            "rpe": tk.StringVar(value="7"),
        }
        
        labels = [
            ("Workout date (YYYY-MM-DD)", "date"),
            ("Sets with identical results", "sets"),
            ("Planned reps per set", "target_reps"),
            ("Completed reps per set", "reps"),
            ("External load (kg)", "weight"),
            ("RPE (1–10)", "rpe"),
        ]
        
        self.labelled_entry(form, labels[0][0], self.workout_vars["date"], 0)
        
        ttk.Label(form, text="Exercise", style="Card.TLabel").grid(
            row=1, column=0, sticky="w", pady=7
        )
        
        # Pull exercise names out for the dropdown menu
        exercise_names = []
        for e in self.exercises:
            exercise_names.append(e["name"])
            
        ttk.Combobox(
            form,
            values=exercise_names,
            textvariable=self.workout_vars["exercise"],
            state="readonly",
            width=29,
        ).grid(row=1, column=1, sticky="ew", pady=7)
        
        for row_num, (lbl, k) in enumerate(labels[1:], start=2):
            self.labelled_entry(form, lbl, self.workout_vars[k], row_num)
            
        ttk.Button(
            form,
            text="Save exercise",
            style="Primary.TButton",
            command=self.save_workout,
        ).grid(row=7, column=0, columnspan=2, sticky="ew", pady=(15, 3))
        
        form.columnconfigure(1, weight=1)
        
        ttk.Label(
            self.content,
            text="Only group sets when load, reps, target and RPE are identical. Otherwise save separate one-set entries. RPE 8 ≈ two reps left; 9 ≈ one; 10 ≈ none.",
            style="Muted.TLabel",
            wraplength=760,
        ).pack(anchor="w", pady=14)

    def save_workout(self):
        try:
            exercise_id = None
            selected_name = self.workout_vars["exercise"].get()
            
            # find matching id
            for e in self.exercises:
                if e["name"] == selected_name:
                    exercise_id = e["id"]
                    break
                    
            if exercise_id is None:
                raise ValueError("Choose an exercise from the list.")

            entry = {}
            for k, val in self.workout_vars.items():
                if k != "exercise":
                    entry[k] = val.get()
            entry["exercise_id"] = exercise_id
            
            db.add_workout(self.user_id, entry)
            messagebox.showinfo(
                "Workout saved", "The exercise was added to your history."
            )
            self.show_recommendations()
        except (ValueError, sqlite3.Error) as err:
            messagebox.showerror("Cannot save workout", str(err))

    def make_tree(self, columns, widths):
        holder = ttk.Frame(self.content)
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

    def show_history(self):
        if not self.require_profile():
            return
            
        self.clear_content()
        history = db.get_history(self.user_id)
        
        self.heading(
            "Workout history",
            "Saved entries and calculated text statistics. No graphs are used.",
        )
        
        statistics = calculate_statistics(history)
        
        summary = ttk.Frame(self.content, style="Card.TFrame", padding=14)
        summary.pack(fill="x", pady=(0, 16))
        
        summary_values = [
            ("Sessions", statistics["sessions"]),
            ("Working sets", statistics["sets"]),
            ("Total volume", f"{statistics['volume']:,.0f} kg"),
            ("Average RPE", statistics["average_rpe"] or "—"),
            (
                "Best est. 1RM",
                f"{statistics['best_estimated_1rm']:g} kg"
                if statistics["best_estimated_1rm"]
                else "—",
            ),
        ]
        
        for idx, (label, val) in enumerate(summary_values):
            card = ttk.Frame(summary, style="Card.TFrame", padding=8)
            card.grid(row=0, column=idx, sticky="nsew")
            ttk.Label(card, text=str(val), style="CardHeading.TLabel").pack()
            ttk.Label(card, text=label, style="Card.TLabel").pack()
            summary.columnconfigure(idx, weight=1)

        columns = ("ID", "Date", "Exercise", "Sets", "Target", "Reps", "Load", "RPE")
        self.history_tree = self.make_tree(columns, (55, 100, 160, 65, 70, 65, 80, 65))
        
        for row in history:
            self.history_tree.insert(
                "",
                "end",
                iid=str(row["id"]),
                values=(
                    row["id"],
                    row["date"],
                    row["exercise"],
                    row["sets"],
                    row["target_reps"],
                    row["reps"],
                    f"{row['weight']:g}",
                    f"{row['rpe']:g}",
                ),
            )
            
        ttk.Button(
            self.content, text="Delete selected entry", command=self.delete_selected
        ).pack(anchor="e", pady=(12, 0))
        
        if not history:
            ttk.Label(
                self.content, text="No workouts saved yet.", style="Muted.TLabel"
            ).pack(pady=20)

    def delete_selected(self):
        selected = self.history_tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Select one history row first.")
            return
            
        if messagebox.askyesno(
            "Delete entry", "Permanently delete the selected workout entry?"
        ):
            try:
                db.delete_workout(self.user_id, int(selected[0]))
                self.show_history()
            except (ValueError, sqlite3.Error) as err:
                messagebox.showerror("Cannot delete entry", str(err))

    def show_recommendations(self):
        if not self.require_profile():
            return
            
        self.clear_content()
        history = db.get_history(self.user_id)
        history_by_exercise = group_history_by_exercise(history)
        
        self.heading(
            "Load guidance",
            "Current recommendations are recalculated from your saved history.",
        )
        
        columns = ("Exercise", "Action", "Suggested load", "Reason")
        tree = self.make_tree(columns, (150, 105, 115, 430))
        
        for e in self.exercises:
            weight, action, reason = progressive_overload(
                history_by_exercise.get(e["id"], []), self.profile
            )
            displayed_weight = "—" if weight is None else f"{weight:g} kg"
            tree.insert(
                "", "end", values=(e["name"], action, displayed_weight, reason)
            )
            
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
        history = db.get_history(self.user_id)
        plan = build_next_workout(self.exercises, history, self.profile)
        
        self.heading(
            "Next workout plan",
            "Four exercises selected from position priorities, recency, RPE and progression status.",
        )
        
        columns = (
            "Exercise",
            "Category",
            "Score",
            "Target reps",
            "Load guidance",
            "Why selected",
        )
        
        tree = self.make_tree(columns, (140, 100, 60, 85, 125, 310))
        
        for item in plan:
            load = (
                item["action"]
                if item["next_weight"] is None
                else f"{item['next_weight']:g} kg · {item['action']}"
            )
            tree.insert(
                "",
                "end",
                values=(
                    item["exercise"],
                    item["category"],
                    item["score"],
                    item["target_reps"],
                    load,
                    item["reason"],
                ),
            )
            
        ttk.Label(
            self.content,
            text="The score is a transparent design rule: position priority +3, training gap +1/+2, recent training −3, high RPE −2, and progression status +1 or −2. At most two exercises are selected per category.",
            style="Muted.TLabel",
            wraplength=780,
        ).pack(anchor="w", pady=12)


def main():
    root = tk.Tk()
    app = RugbyApp(root) # saving ref to app just in case, though python doesn't strictly need it here
    root.mainloop()


if __name__ == "__main__":
    main()
