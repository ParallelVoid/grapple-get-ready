import json
from datetime import datetime, timedelta
from pathlib import Path

from nicegui import ui

# Data storage
DATA_FILE = Path("combat_sports_data.json")


class CombatSportsTracker:
    def __init__(self):
        self.workouts = []
        self.competitions = []
        self.load_data()

    def load_data(self):
        if DATA_FILE.exists():
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                self.workouts = data.get("workouts", [])
                self.competitions = data.get("competitions", [])

    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(
                {"workouts": self.workouts, "competitions": self.competitions},
                f,
                indent=2,
            )

    def add_workout(self, workout_data):
        self.workouts.append(workout_data)
        self.save_data()

    def add_competition(self, comp_data):
        self.competitions.append(comp_data)
        self.save_data()


tracker = CombatSportsTracker()

# Color scheme for combat sports theme
PRIMARY_COLOR = "#dc2626"  # Red
SECONDARY_COLOR = "#1f2937"  # Dark gray
ACCENT_COLOR = "#f59e0b"  # Orange


def create_header():
    with ui.header().classes("items-center justify-between bg-gray-900 text-white"):
        ui.label("🥊 Combat Sports Training Tracker").classes("text-2xl font-bold")
        ui.button(
            "Settings",
            icon="settings",
            on_click=lambda: ui.notify("Settings coming soon!"),
        ).props("flat")


def create_dashboard():
    with ui.column().classes("w-full gap-4 p-4"):
        # Stats cards
        with ui.row().classes("w-full gap-4"):
            with ui.card().classes(
                "flex-1 bg-gradient-to-br from-red-600 to-red-800 text-white"
            ):
                ui.label("Total Workouts").classes("text-sm opacity-80")
                ui.label(str(len(tracker.workouts))).classes("text-4xl font-bold")

            with ui.card().classes(
                "flex-1 bg-gradient-to-br from-orange-600 to-orange-800 text-white"
            ):
                ui.label("Upcoming Competitions").classes("text-sm opacity-80")
                upcoming = len(
                    [
                        c
                        for c in tracker.competitions
                        if c.get("date", "") >= datetime.now().strftime("%Y-%m-%d")
                    ]
                )
                ui.label(str(upcoming)).classes("text-4xl font-bold")

            with ui.card().classes(
                "flex-1 bg-gradient-to-br from-gray-700 to-gray-900 text-white"
            ):
                ui.label("This Week").classes("text-sm opacity-80")
                week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                week_workouts = len(
                    [w for w in tracker.workouts if w.get("date", "") >= week_ago]
                )
                ui.label(str(week_workouts)).classes("text-4xl font-bold")


def create_workout_log():
    with ui.column().classes("w-full gap-4 p-4"):
        ui.label("Log New Workout").classes("text-2xl font-bold text-gray-800")

        with ui.card().classes("w-full"):
            workout_type = ui.select(
                [
                    "Judo",
                    "Sambo",
                    "BJJ/Grappling",
                    "MMA",
                    "Strength & Conditioning",
                    "Cardio",
                    "Technique Drilling",
                ],
                label="Workout Type",
                value="Judo",
            ).classes("w-full")

            with ui.input("Date").classes("w-full") as date_input:
                workout_date = ui.date().bind_value(date_input)
            date_input.value = datetime.now().strftime("%Y-%m-%d")

            duration = ui.number(label="Duration (minutes)", value=60, min=1).classes(
                "w-full"
            )

            intensity = ui.select(
                ["Light", "Moderate", "Hard", "Very Hard", "Competition Intensity"],
                label="Intensity",
                value="Moderate",
            ).classes("w-full")

            weight = ui.number(label="Weight (lbs/kg)", value=0, step=0.1).classes(
                "w-full"
            )

            notes = ui.textarea(
                label="Notes (techniques, rounds, sparring partners, etc.)",
                placeholder="e.g., 5 rounds sparring, worked on jab-cross combinations",
            ).classes("w-full")

            def log_workout():
                workout_data = {
                    "type": workout_type.value,
                    "date": date_input.value,
                    "duration": duration.value,
                    "intensity": intensity.value,
                    "weight": weight.value,
                    "notes": notes.value,
                    "timestamp": datetime.now().isoformat(),
                }
                tracker.add_workout(workout_data)
                ui.notify("Workout logged successfully! 💪", type="positive")
                notes.value = ""
                workout_list_container.refresh()

            ui.button("Log Workout", on_click=log_workout, icon="add_circle").props(
                "color=red"
            ).classes("w-full")


def create_competition_prep():
    with ui.column().classes("w-full gap-4 p-4"):
        ui.label("Competition Preparation").classes("text-2xl font-bold text-gray-800")

        with ui.card().classes("w-full"):
            comp_name = ui.input(
                label="Competition Name", placeholder="e.g., State Championships"
            ).classes("w-full")
            with ui.input("Competition Date").classes("w-full") as comp_date_input:
                comp_date = ui.date().bind_value(comp_date_input)
            weight_class = ui.input(
                label="Weight Class", placeholder="e.g., 155 lbs"
            ).classes("w-full")
            current_weight = ui.number(
                label="Current Weight", value=0, step=0.1
            ).classes("w-full")

            def add_comp():
                comp_data = {
                    "name": comp_name.value,
                    "date": comp_date_input.value,
                    "weight_class": weight_class.value,
                    "current_weight": current_weight.value,
                    "created": datetime.now().isoformat(),
                }
                tracker.add_competition(comp_data)
                ui.notify("Competition added! 🥇", type="positive")
                comp_name.value = ""
                weight_class.value = ""
                comp_list_container.refresh()

            ui.button("Add Competition", on_click=add_comp, icon="emoji_events").props(
                "color=orange"
            ).classes("w-full")

        # Competitions list
        @ui.refreshable
        def comp_list_container():
            if tracker.competitions:
                ui.label("Upcoming Competitions").classes("text-xl font-bold mt-4")
                for comp in sorted(
                    tracker.competitions, key=lambda x: x.get("date", ""), reverse=False
                ):
                    with ui.card().classes("w-full"):
                        with ui.row().classes("w-full items-center justify-between"):
                            with ui.column():
                                ui.label(comp["name"]).classes("text-lg font-bold")
                                ui.label(
                                    f"📅 {comp['date']} | ⚖️ {comp['weight_class']}"
                                ).classes("text-sm text-gray-600")
                                if comp.get("current_weight"):
                                    ui.label(
                                        f"Current: {comp['current_weight']} lbs/kg"
                                    ).classes("text-sm")

        comp_list_container()


def create_workout_history():
    with ui.column().classes("w-full gap-4 p-4"):
        ui.label("Training History").classes("text-2xl font-bold text-gray-800")

        @ui.refreshable
        def workout_list_container():
            if not tracker.workouts:
                ui.label("No workouts logged yet. Start training! 🥊").classes(
                    "text-gray-500"
                )
            else:
                for workout in sorted(
                    tracker.workouts, key=lambda x: x.get("date", ""), reverse=True
                )[:20]:
                    with ui.card().classes("w-full hover:shadow-lg transition-shadow"):
                        with ui.row().classes("w-full items-center gap-4"):
                            # Icon based on workout type
                            icon_map = {
                                "Judo": "🥋",
                                "Sambo": "🇷🇺",
                                "BJJ/Grappling": "🤼",
                                "MMA": "🥊",
                                "Strength & Conditioning": "💪",
                                "Cardio": "🏃",
                                "Technique Drilling": "🎯",
                            }
                            ui.label(icon_map.get(workout["type"], "🥊")).classes(
                                "text-3xl"
                            )

                            with ui.column().classes("flex-1"):
                                ui.label(workout["type"]).classes("text-lg font-bold")
                                ui.label(
                                    f"{workout['date']} | {workout['duration']} min | {workout['intensity']}"
                                ).classes("text-sm text-gray-600")
                                if workout.get("weight"):
                                    ui.label(
                                        f"Weight: {workout['weight']} lbs/kg"
                                    ).classes("text-sm text-gray-500")
                                if workout.get("notes"):
                                    ui.label(workout["notes"]).classes(
                                        "text-sm text-gray-700 mt-1"
                                    )

        workout_list_container()


@ui.page("/")
def main_page():
    create_header()

    with ui.tabs().classes("w-full") as tabs:
        tab_dashboard = ui.tab("Dashboard", icon="dashboard")
        tab_workout = ui.tab("Log Workout", icon="fitness_center")
        tab_competition = ui.tab("Competition Prep", icon="emoji_events")
        tab_history = ui.tab("History", icon="history")

    with ui.tab_panels(tabs, value=tab_dashboard).classes("w-full"):
        with ui.tab_panel(tab_dashboard):
            create_dashboard()

        with ui.tab_panel(tab_workout):
            create_workout_log()

        with ui.tab_panel(tab_competition):
            create_competition_prep()

        with ui.tab_panel(tab_history):
            create_workout_history()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Combat Sports Tracker", dark=False, reload=False)
