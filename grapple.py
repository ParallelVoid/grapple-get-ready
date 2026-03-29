import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

from nicegui import app, ui
import asyncio
import plotly.graph_objects as go


DATA_FILE = Path("combat_sports_data.json")
PREMADE_WORKOUTS_DIR = Path("workouts")

WORKOUT_TYPES = [
	"Judo",
	"Sambo",
	"Wrestling",
	"BJJ/Grappling",
	"MMA",
	"Strength & Conditioning",
	"Cardio",
	"Technique Drilling",
]

COMPETITION_SPORTS = ["Judo", "Sambo", "BJJ/Grappling", "MMA", "Kickboxing", "Wrestling"]

INTENSITY_LEVELS = ["Light", "Moderate", "Hard", "Very Hard", "Competition Intensity"]

WORKOUT_ICONS = {
	"Judo": "🥋",
	"Sambo": "🦅",
	"Wrestling": "🤼",
	"BJJ/Grappling": "🐙",
	"MMA": "🥊",
	"Strength & Conditioning": "💪",
	"Cardio": "🏃",
	"Technique Drilling": "🎯",
}

WORKOUT_COLORS = {
	"Judo": "#FF6B6B",
	"Sambo": "#4ECDC4",
	"Wrestling": "#F70046",
	"BJJ/Grappling": "#45B7D1",
	"MMA": "#FFA07A",
	"Strength & Conditioning": "#98D8C8",
	"Cardio": "#F7DC6F",
	"Technique Drilling": "#BB8FCE",
}

# Maps premade workout JSON types to internal tracker types
PREMADE_TYPE_MAP = {
	"Judo Technique Practice": "Judo",
	"Strength and Conditioning": "Strength & Conditioning",
	"BJJ/Grappling": "BJJ/Grappling",
	"MMA": "MMA",
	"Cardio": "Cardio",
}

PREMADE_ICONS = {
	"Judo Technique Practice": "🥋",
	"Strength and Conditioning": "💪",
	"BJJ/Grappling": "🐙",
	"MMA": "🥊",
	"Cardio": "🏃",
}

PREMADE_GRADIENTS = {
	"Judo Technique Practice": "from-red-500 to-red-700",
	"Strength and Conditioning": "from-blue-500 to-blue-700",
	"BJJ/Grappling": "from-purple-500 to-purple-700",
	"MMA": "from-orange-500 to-orange-700",
	"Cardio": "from-green-500 to-green-700",
}

MEDAL_EMOJI = {"Gold": "🥇", "Silver": "🥈", "Bronze": "🥉"}

RESULT_CARD_COLORS = {
	"Win": "bg-green-100 border-green-500",
	"Loss": "bg-red-100 border-red-500",
	"Draw": "bg-yellow-100 border-yellow-500",
	"No Contest": "bg-gray-100 border-gray-500",
	"Upcoming": "bg-blue-100 border-blue-500",
}


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

	def get_most_recent_weight(self):
		weight_entries = [w for w in self.workouts if w.get("weight") and w["weight"] > 0]
		if not weight_entries:
			return 0
		return max(weight_entries, key=lambda w: w.get("date", ""))["weight"]

	def get_competition_record(self):
		"""Return (wins, losses, draws) across all competitions."""
		wins = losses = draws = 0
		for comp in self.competitions:
			if comp.get("type") == "tournament" and comp.get("matches"):
				for match in comp["matches"]:
					if match["result"] == "Win":
						wins += 1
					elif match["result"] == "Loss":
						losses += 1
					elif match["result"] == "Draw":
						draws += 1
			else:
				result = comp.get("result", "Upcoming")
				if result == "Win":
					wins += 1
				elif result == "Loss":
					losses += 1
				elif result == "Draw":
					draws += 1
		return wins, losses, draws

	def get_record_by_sport(self):
		"""Return {sport: {wins, losses, draws}} for all completed competitions."""
		sports_stats = {}
		for comp in self.competitions:
			sport = comp.get("sport", "Unknown")
			if comp.get("type") == "tournament" and comp.get("matches"):
				for match in comp["matches"]:
					stats = sports_stats.setdefault(sport, {"wins": 0, "losses": 0, "draws": 0})
					if match["result"] == "Win":
						stats["wins"] += 1
					elif match["result"] == "Loss":
						stats["losses"] += 1
					elif match["result"] == "Draw":
						stats["draws"] += 1
			else:
				result = comp.get("result", "Upcoming")
				if result not in ("Upcoming", "No Contest"):
					stats = sports_stats.setdefault(sport, {"wins": 0, "losses": 0, "draws": 0})
					if result == "Win":
						stats["wins"] += 1
					elif result == "Loss":
						stats["losses"] += 1
					elif result == "Draw":
						stats["draws"] += 1
		return sports_stats

	def get_medal_counts(self):
		medals = {"Gold": 0, "Silver": 0, "Bronze": 0}
		for comp in self.competitions:
			if comp.get("type") == "tournament" and comp.get("medal") and comp["medal"] != "None":
				medals[comp["medal"]] = medals.get(comp["medal"], 0) + 1
		return medals

	def get_upcoming_competitions(self):
		today = datetime.now().strftime("%Y-%m-%d")
		return [
			c for c in self.competitions
			if c.get("result", "Upcoming") == "Upcoming" and c.get("date", "") >= today
		]

	def get_workouts_this_week(self):
		week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
		return [w for w in self.workouts if w.get("date", "") >= week_ago]


def load_premade_workouts():
	if not PREMADE_WORKOUTS_DIR.exists():
		return []
	workouts = []
	for json_file in sorted(PREMADE_WORKOUTS_DIR.glob("*.json")):
		try:
			with open(json_file, "r") as f:
				data = json.load(f)
				workout = data.get("workout", data)
				workouts.append(workout)
		except Exception as e:
			print(f"Error loading {json_file}: {e}")
	return workouts


tracker = CombatSportsTracker()


def build_training_frequency_chart():
	if not tracker.workouts:
		return None

	weekly_data = defaultdict(lambda: defaultdict(int))
	workout_type_counts = defaultdict(int)

	for workout in tracker.workouts:
		date = datetime.strptime(workout["date"], "%Y-%m-%d")
		week_start = date - timedelta(days=date.weekday())
		week_key = week_start.strftime("%Y-%m-%d")
		weekly_data[week_key][workout["type"]] += 1
		workout_type_counts[workout["type"]] += 1

	sorted_weeks = sorted(weekly_data.keys())
	all_types = sorted(workout_type_counts.keys())

	fig = go.Figure()
	for workout_type in all_types:
		counts = [weekly_data[week].get(workout_type, 0) for week in sorted_weeks]
		fig.add_trace(go.Bar(
			x=sorted_weeks,
			y=counts,
			name=workout_type,
			marker_color=WORKOUT_COLORS.get(workout_type, "#95A5A6"),
		))

	fig.update_layout(
		title="Weekly Training Frequency",
		xaxis_title="Week",
		yaxis_title="Number of Sessions",
		barmode="stack",
		height=400,
		hovermode="x unified",
		plot_bgcolor="rgba(0,0,0,0)",
		paper_bgcolor="rgba(0,0,0,0)",
		font=dict(size=12),
		margin=dict(l=50, r=50, t=50, b=50),
	)
	return fig


def build_weight_tracker_chart():
	weight_entries = [
		(w["date"], w["weight"])
		for w in sorted(tracker.workouts, key=lambda x: x.get("date", ""))
		if w.get("weight") and w["weight"] > 0
	]
	if not weight_entries:
		return None

	dates, weights = zip(*weight_entries)

	fig = go.Figure()
	fig.add_trace(go.Scatter(
		x=dates,
		y=weights,
		mode="lines+markers",
		name="Weight",
		line=dict(color="#3498DB", width=3),
		marker=dict(size=8),
	))

	today = datetime.now().strftime("%Y-%m-%d")
	upcoming_comps = [
		c for c in tracker.competitions
		if c.get("date", "") >= today and c.get("weight_class")
	]

	for comp in upcoming_comps:
		try:
			target_weight = float(comp["weight_class"].split()[0])
			fig.add_trace(go.Scatter(
				x=[dates[0], comp["date"]],
				y=[target_weight, target_weight],
				mode="lines",
				name=f'{comp["name"]} Target',
				line=dict(color="#E74C3C", width=2, dash="dash"),
			))
			fig.add_annotation(
				x=comp["date"], y=target_weight,
				text=f'{comp["name"]}<br>{comp["weight_class"]}',
				showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2,
				arrowcolor="#E74C3C", bgcolor="#E74C3C",
				font=dict(color="white", size=10),
				bordercolor="#E74C3C", borderwidth=2, borderpad=4,
			)
		except (ValueError, IndexError):
			pass

	if upcoming_comps:
		current_weight = weights[-1]
		try:
			target_weight = float(upcoming_comps[0]["weight_class"].split()[0])
			weight_diff = current_weight - target_weight
			fig.add_annotation(
				x=dates[-1], y=current_weight,
				text=f"Current: {current_weight} kg<br>To cut: {weight_diff:.1f} kg",
				showarrow=True, arrowhead=2, ax=40, ay=-40,
				bgcolor="#3498DB", font=dict(color="white", size=10),
				bordercolor="#3498DB", borderwidth=2, borderpad=4,
			)
		except (ValueError, IndexError):
			pass

	fig.update_layout(
		title="Weight Cut Tracker",
		xaxis_title="Date",
		yaxis_title="Weight (kg)",
		height=400,
		hovermode="x unified",
		plot_bgcolor="rgba(0,0,0,0)",
		paper_bgcolor="rgba(0,0,0,0)",
		font=dict(size=12),
		margin=dict(l=50, r=50, t=50, b=50),
	)
	return fig


def date_picker_input(label: str, initial_value: str = "") -> ui.input:
	"""Input with a calendar icon that opens a date picker dialog."""
	date_input = ui.input(label, value=initial_value).classes("w-full").props("readonly")
	with date_input.add_slot("append"):
		with ui.dialog() as dialog, ui.card():
			ui.date().bind_value(date_input).props("minimal")
			ui.button("Close", on_click=dialog.close)
		ui.icon("edit_calendar").on("click", dialog.open).classes("cursor-pointer")
	return date_input


def record_string(wins: int, losses: int, draws: int) -> str:
	base = f"{wins}-{losses}"
	return base if draws == 0 else f"{base}-{draws}"


def create_header(on_refresh=None):
	with ui.header().classes("items-center justify-between bg-red-600 !important text-white"):
		ui.label("Grapple Get Ready 🤼‍♂️").classes("text-2xl font-bold")
		with ui.row().classes("gap-2"):
			if on_refresh:
				ui.button("Refresh", icon="refresh", on_click=on_refresh).props("flat").tooltip("Reload data from disk")
			ui.button("Settings", icon="settings",
					  on_click=lambda: ui.notify("Settings coming soon!")).props("flat")


@ui.refreshable
def create_dashboard():
	with ui.row().classes("w-full gap-4 p-4"):
		_dashboard_left_column()
		_dashboard_medal_panel()

	with ui.row().classes("w-full gap-4 px-4"):
		freq_chart = build_training_frequency_chart()
		if freq_chart:
			with ui.card().classes("flex-1"):
				ui.plotly(freq_chart).classes("w-full")

		weight_chart = build_weight_tracker_chart()
		if weight_chart:
			with ui.card().classes("flex-1"):
				ui.plotly(weight_chart).classes("w-full")


def _dashboard_left_column():
	with ui.column().classes("flex-1 gap-4"):
		_competition_record_card()
		_summary_stat_cards()


def _competition_record_card():
	wins, losses, draws = tracker.get_competition_record()
	sports_stats = tracker.get_record_by_sport()
	total = wins + losses + draws

	with ui.card().classes("w-full bg-gradient-to-r from-gray-800 to-gray-900 text-white p-6"):
		ui.label("Competition Record").classes("text-2xl font-bold mb-4")

		with ui.row().classes("w-full gap-8 items-center"):
			with ui.column().classes("items-center"):
				ui.label("Overall Record").classes("text-sm opacity-80")
				ui.label(record_string(wins, losses, draws)).classes("text-5xl font-bold")
				if total > 0:
					ui.label(f"{wins / total * 100:.1f}% Win Rate").classes("text-sm opacity-80 mt-2")

			ui.separator().props("vertical").classes("bg-white opacity-20")

			with ui.column().classes("flex-1"):
				ui.label("By Sport").classes("text-sm opacity-80 mb-2")
				if sports_stats:
					with ui.grid(columns=2).classes("w-full gap-4"):
						for sport, stats in sorted(sports_stats.items()):
							with ui.card().classes("bg-gray-700 p-3"):
								ui.label(sport).classes("text-sm font-semibold")
								ui.label(record_string(stats["wins"], stats["losses"], stats["draws"])).classes("text-lg font-bold")
				else:
					ui.label("No completed competitions yet").classes("text-sm opacity-60 italic")


def _summary_stat_cards():
	with ui.row().classes("w-full gap-4"):
		with ui.card().classes("flex-1 bg-gradient-to-br from-red-600 to-red-800 text-white"):
			ui.label("Total Workouts").classes("text-sm opacity-80")
			ui.label(str(len(tracker.workouts))).classes("text-4xl font-bold")

		with ui.card().classes("flex-1 bg-gradient-to-br from-orange-600 to-orange-800 text-white"):
			ui.label("Upcoming Competitions").classes("text-sm opacity-80")
			ui.label(str(len(tracker.get_upcoming_competitions()))).classes("text-4xl font-bold")

		with ui.card().classes("flex-1 bg-gradient-to-br from-gray-700 to-gray-900 text-white"):
			ui.label("This Week").classes("text-sm opacity-80")
			ui.label(str(len(tracker.get_workouts_this_week()))).classes("text-4xl font-bold")


def _dashboard_medal_panel():
	medals = tracker.get_medal_counts()
	with ui.column().classes("w-80 gap-4"):
		with ui.card().classes("w-80 p-6 bg-gradient-to-br from-amber-50 to-yellow-100"):
			ui.label("Medal Collection").classes("text-xl font-bold mb-4 text-gray-800")
			with ui.column().classes("w-full gap-3"):
				for medal, color_class in [("Gold", "text-yellow-600"), ("Silver", "text-gray-500"), ("Bronze", "text-orange-700")]:
					with ui.row().classes("w-full items-center justify-between p-3 bg-white rounded-lg"):
						with ui.row().classes("items-center gap-3"):
							ui.label(MEDAL_EMOJI[medal]).classes("text-3xl")
							ui.label(medal).classes("text-lg font-semibold text-gray-800")
						ui.label(str(medals[medal])).classes(f"text-2xl font-bold {color_class}")
			if sum(medals.values()) == 0:
				ui.label("No medals yet - keep training!").classes("text-sm text-gray-600 text-center mt-2 italic")


def create_workout_log():
	with ui.column().classes("w-full gap-4 p-4"):
		ui.label("Log New Workout").classes("text-2xl font-bold text-gray-800")

		with ui.card().classes("w-full"):
			workout_type = ui.select(WORKOUT_TYPES, label="Workout Type", value="Judo").classes("w-full")
			date_input = date_picker_input("Date", datetime.now().strftime("%Y-%m-%d"))
			duration = ui.number(label="Duration (minutes)", value=60, min=1).classes("w-full")
			intensity = ui.select(INTENSITY_LEVELS, label="Intensity", value="Moderate").classes("w-full")
			weight = ui.number(label="Weight (kg)", value=0, step=0.1).classes("w-full")
			notes = ui.textarea(
				label="Notes (techniques, rounds, sparring partners, etc.)",
				placeholder="e.g., 5 rounds sparring, worked on jab-cross combinations",
			).classes("w-full")

			def log_workout():
				tracker.add_workout({
					"type": workout_type.value,
					"date": date_input.value,
					"duration": duration.value,
					"intensity": intensity.value,
					"weight": weight.value,
					"notes": notes.value,
					"timestamp": datetime.now().isoformat(),
				})
				create_dashboard.refresh()
				create_workout_history.refresh()
				ui.notify("Workout logged successfully! 💪", type="positive")
				notes.value = ""

			ui.button("Log Workout", on_click=log_workout, icon="add_circle").props("color=red").classes("w-full")


def create_competition_prep():
	with ui.column().classes("w-full gap-4 p-4"):
		ui.label("Competition Preparation").classes("text-2xl font-bold text-gray-800")
		_add_competition_form()


def _add_competition_form():
	with ui.card().classes("w-full"):
		ui.label("Add/Update Competition").classes("text-lg font-semibold mb-2")
		ui.label("For tournaments with multiple matches, add each match separately or use the match tracker below.").classes("text-xs text-gray-600 mb-3 italic")

		comp_name = ui.input(label="Competition Name", placeholder="e.g., State Championships").classes("w-full")
		comp_sport = ui.select(COMPETITION_SPORTS, label="Sport", value="Judo").classes("w-full")
		comp_type = ui.select(["Single Match", "Tournament (Multiple Matches)"], label="Competition Type", value="Single Match").classes("w-full")
		comp_date_input = date_picker_input("Competition Date")
		weight_class = ui.input(label="Weight Class", placeholder="e.g., 73 kgs").classes("w-full")
		current_weight = ui.number(label="Current Weight", value=0, step=0.1).classes("w-full")

		# Single match fields
		with ui.column().classes("w-full") as single_match_section:
			comp_result = ui.select(["Upcoming", "Win", "Loss", "Draw", "No Contest"], label="Result", value="Upcoming").classes("w-full")
			result_notes = ui.textarea(label="Result Notes (optional)", placeholder="e.g., TKO Round 2, Decision, Submission").classes("w-full")

		# Tournament fields
		matches_list = []

		@ui.refreshable
		def matches_container():
			if matches_list:
				ui.label("Matches").classes("text-sm font-semibold mt-2")
				for i, match in enumerate(matches_list):
					with ui.card().classes("bg-gray-50 p-2 mb-2"):
						with ui.row().classes("w-full justify-between items-center"):
							ui.label(f"Match {i + 1}: {match['result']} - {match['notes']}").classes("text-sm")
							ui.button(icon="delete", on_click=lambda idx=i: (matches_list.pop(idx), matches_container.refresh())).props("flat dense")

		with ui.column().classes("w-full") as tournament_section:
			matches_container()
			tournament_medal = ui.select(["None", "Gold", "Silver", "Bronze"], label="Medal Placement (optional)", value="None").classes("w-full")

			with ui.row().classes("w-full gap-2"):
				match_result = ui.select(["Win", "Loss", "Draw"], value="Win").classes("flex-1")
				match_notes = ui.input(placeholder="e.g., Submission, Points").classes("flex-1")

				def add_match():
					if match_notes.value or match_result.value:
						matches_list.append({"result": match_result.value, "notes": match_notes.value})
						match_notes.value = ""
						matches_container.refresh()

				ui.button("Add Match", on_click=add_match, icon="add").props("flat")

		def update_section_visibility():
			is_single = comp_type.value == "Single Match"
			single_match_section.set_visibility(is_single)
			tournament_section.set_visibility(not is_single)

		comp_type.on("update:model-value", update_section_visibility)
		update_section_visibility()

		def add_comp():
			base = {
				"name": comp_name.value,
				"sport": comp_sport.value,
				"date": comp_date_input.value,
				"weight_class": weight_class.value,
				"current_weight": current_weight.value,
				"created": datetime.now().isoformat(),
			}
			if comp_type.value == "Single Match":
				comp_data = {**base, "type": "single", "result": comp_result.value, "result_notes": result_notes.value}
			else:
				comp_data = {
					**base,
					"type": "tournament",
					"matches": matches_list.copy(),
					"medal": tournament_medal.value,
					"result": "Completed" if matches_list else "Upcoming",
				}

			tracker.add_competition(comp_data)
			ui.notify("Competition added! 🥇", type="positive")
			comp_name.value = weight_class.value = result_notes.value = ""
			matches_list.clear()
			matches_container.refresh()
			comp_list_container.refresh()

		ui.button("Add Competition", on_click=add_comp, icon="emoji_events").props("color=orange").classes("w-full")

	@ui.refreshable
	def comp_list_container():
		if not tracker.competitions:
			return
		ui.label("Competitions").classes("text-xl font-bold mt-4")
		sorted_comps = sorted(enumerate(tracker.competitions), key=lambda x: x[1].get("date", ""), reverse=True)
		for original_idx, comp in sorted_comps:
			_competition_card(comp, original_idx, comp_list_container)

	comp_list_container()


def _competition_card(comp, original_idx, refresh_fn):
	if comp.get("type") == "tournament":
		card_color = "bg-purple-100 border-purple-500" if comp.get("matches") else "bg-blue-100 border-blue-500"
	else:
		card_color = RESULT_CARD_COLORS.get(comp.get("result", "Upcoming"), "bg-white")

	with ui.card().classes(f"w-full border-l-4 {card_color}"):
		with ui.row().classes("w-full items-start justify-between gap-4"):
			with ui.column().classes("flex-1"):
				with ui.row().classes("items-center gap-2"):
					ui.label(comp["name"]).classes("text-lg font-bold")
					if comp.get("type") == "tournament" and comp.get("medal") and comp["medal"] != "None":
						ui.label(MEDAL_EMOJI.get(comp["medal"], "")).classes("text-xl")

				ui.label(f"{comp.get('sport', 'N/A')} | 📅 {comp['date']} | ⚖️ {comp['weight_class']}").classes("text-sm text-gray-600")
				if comp.get("current_weight"):
					ui.label(f"Current: {comp['current_weight']} kg").classes("text-sm")

				if comp.get("type") == "tournament" and comp.get("matches"):
					t_wins = sum(1 for m in comp["matches"] if m["result"] == "Win")
					t_losses = sum(1 for m in comp["matches"] if m["result"] == "Loss")
					t_draws = sum(1 for m in comp["matches"] if m["result"] == "Draw")
					ui.label(f"🏆 Tournament: {record_string(t_wins, t_losses, t_draws)}").classes("text-sm font-semibold mt-1")
					for i, match in enumerate(comp["matches"]):
						color = "text-green-700" if match["result"] == "Win" else "text-red-700" if match["result"] == "Loss" else "text-yellow-700"
						text = f"  Match {i + 1}: {match['result']}"
						if match.get("notes"):
							text += f" - {match['notes']}"
						ui.label(text).classes(f"text-xs {color}")
				elif comp.get("result") and comp["result"] != "Upcoming":
					label = comp["result"]
					if comp.get("result_notes"):
						label += f" - {comp['result_notes']}"
					ui.label(label).classes("text-sm font-semibold mt-1")

			with ui.column().classes("gap-1"):
				ui.button(icon="edit", on_click=lambda: _open_edit_dialog(comp, original_idx, refresh_fn)).props("flat dense color=blue").classes("w-8 h-8")
				ui.button(icon="delete", on_click=lambda: _delete_competition(original_idx, refresh_fn)).props("flat dense color=red").classes("w-8 h-8")


def _open_edit_dialog(comp, comp_idx, refresh_fn):
	with ui.dialog() as dialog, ui.card().classes("w-full max-w-2xl"):
		ui.label(f"Edit: {comp['name']}").classes("text-xl font-bold mb-4")

		if comp.get("type") == "tournament":
			_edit_tournament_dialog(comp, comp_idx, dialog, refresh_fn)
		else:
			_edit_single_match_dialog(comp, comp_idx, dialog, refresh_fn)

	dialog.open()


def _edit_tournament_dialog(comp, comp_idx, dialog, refresh_fn):
	edit_medal = ui.select(["None", "Gold", "Silver", "Bronze"], label="Medal Placement", value=comp.get("medal", "None")).classes("w-full")
	ui.label("Matches").classes("text-sm font-semibold mt-3")
	edit_matches = comp.get("matches", []).copy()

	@ui.refreshable
	def edit_matches_container():
		for i, match in enumerate(edit_matches):
			with ui.card().classes("bg-gray-50 p-2 mb-2"):
				with ui.row().classes("w-full gap-2 items-center"):
					ui.label(f"Match {i + 1}:").classes("text-sm font-semibold")
					match_res = ui.select(["Win", "Loss", "Draw"], value=match["result"]).classes("flex-1")
					match_note = ui.input(value=match.get("notes", "")).classes("flex-1")

					def update_match(idx=i, res=match_res, note=match_note):
						edit_matches[idx] = {"result": res.value, "notes": note.value}

					match_res.on("update:model-value", lambda e, idx=i, res=match_res, note=match_note: update_match(idx, res, note))
					match_note.on("update:model-value", lambda e, idx=i, res=match_res, note=match_note: update_match(idx, res, note))
					ui.button(icon="delete", on_click=lambda idx=i: (edit_matches.pop(idx), edit_matches_container.refresh())).props("flat dense color=red")

	edit_matches_container()

	with ui.row().classes("w-full gap-2 mt-2"):
		new_match_result = ui.select(["Win", "Loss", "Draw"], value="Win").classes("flex-1")
		new_match_notes = ui.input(placeholder="Match notes").classes("flex-1")

		def add_new_match():
			edit_matches.append({"result": new_match_result.value, "notes": new_match_notes.value})
			new_match_notes.value = ""
			edit_matches_container.refresh()

		ui.button("Add Match", on_click=add_new_match, icon="add").props("flat")

	def save():
		tracker.competitions[comp_idx]["matches"] = edit_matches
		tracker.competitions[comp_idx]["medal"] = edit_medal.value
		tracker.save_data()
		ui.notify("Tournament updated! 🏆", type="positive")
		dialog.close()
		refresh_fn.refresh()

	with ui.row().classes("w-full gap-2 mt-4"):
		ui.button("Save", on_click=save, icon="save").props("color=green")
		ui.button("Cancel", on_click=dialog.close).props("flat")


def _edit_single_match_dialog(comp, comp_idx, dialog, refresh_fn):
	edit_result = ui.select(["Upcoming", "Win", "Loss", "Draw", "No Contest"], label="Result", value=comp.get("result", "Upcoming")).classes("w-full")
	edit_notes = ui.textarea(label="Result Notes", value=comp.get("result_notes", "")).classes("w-full")

	def save():
		tracker.competitions[comp_idx]["result"] = edit_result.value
		tracker.competitions[comp_idx]["result_notes"] = edit_notes.value
		tracker.save_data()
		ui.notify("Competition updated! ✅", type="positive")
		dialog.close()
		refresh_fn.refresh()

	with ui.row().classes("w-full gap-2 mt-4"):
		ui.button("Save", on_click=save, icon="save").props("color=green")
		ui.button("Cancel", on_click=dialog.close).props("flat")


def _delete_competition(comp_idx, refresh_fn):
	name = tracker.competitions[comp_idx]["name"]
	tracker.competitions.pop(comp_idx)
	tracker.save_data()
	ui.notify(f"Deleted {name}", type="warning")
	refresh_fn.refresh()


@ui.refreshable
def create_workout_history():
	with ui.column().classes("w-full gap-4 p-4"):
		ui.label("Training History").classes("text-2xl font-bold text-gray-800")

		if not tracker.workouts:
			ui.label("No workouts logged yet. Start training! 🥊").classes("text-gray-500")
			return

		recent_workouts = sorted(tracker.workouts, key=lambda x: x.get("date", ""), reverse=True)[:20]
		for workout in recent_workouts:
			_workout_history_card(workout)


def _workout_history_card(workout):
	with ui.card().classes("w-full hover:shadow-lg transition-shadow"):
		with ui.row().classes("w-full items-center gap-4"):
			ui.label(WORKOUT_ICONS.get(workout["type"], "🥊")).classes("text-3xl")
			with ui.column().classes("flex-1"):
				ui.label(workout["type"]).classes("text-lg font-bold")
				ui.label(f"{workout['date']} | {workout['duration']} min | {workout['intensity']}").classes("text-sm text-gray-600")
				if workout.get("weight"):
					ui.label(f"Weight: {workout['weight']} kg").classes("text-sm text-gray-500")
				if workout.get("notes"):
					ui.label(workout["notes"]).classes("text-sm text-gray-700 mt-1")


def log_premade_workout(workout):
	workout_type = PREMADE_TYPE_MAP.get(workout.get("type", ""), workout.get("type", "Judo"))
	tracker.add_workout({
		"type": workout_type,
		"date": datetime.now().strftime("%Y-%m-%d"),
		"duration": workout.get("duration_minutes", 60),
		"intensity": "Moderate",
		"weight": tracker.get_most_recent_weight(),
		"notes": f"Premade workout: {workout['name']}",
		"timestamp": datetime.now().isoformat(),
	})


def create_premade_workouts():
	premade_workouts = load_premade_workouts()

	with ui.column().classes("w-full gap-4 p-4"):
		ui.label("Premade Workouts").classes("text-2xl font-bold text-gray-800")
		ui.label("Select a workout to view details and exercises.").classes("text-sm text-gray-500 -mt-2 mb-2")

		if not premade_workouts:
			ui.label("No premade workouts found. Add JSON files to the workouts/ folder.").classes("text-gray-500 italic")
			return

		with ui.row().classes("w-full flex-wrap gap-4"):
			for workout in premade_workouts:
				_premade_workout_card(workout)


def _premade_workout_card(workout):
	wtype = workout.get("type", "")
	icon = PREMADE_ICONS.get(wtype, "🏋️")
	gradient = PREMADE_GRADIENTS.get(wtype, "from-gray-500 to-gray-700")
	duration = workout.get("duration_minutes")

	with ui.card().classes("w-72 hover:shadow-xl transition-all duration-200 overflow-hidden"):
		with ui.element("div").classes(f"bg-gradient-to-r {gradient} p-4 text-white w-full"):
			ui.label(icon).classes("text-4xl mb-1")
			ui.label(workout["name"]).classes("text-base font-bold leading-tight")
			ui.label(wtype).classes("text-xs opacity-80 mt-1")

		with ui.element("div").classes("p-4"):
			ui.label(f"👤 Inspired by: {workout.get('inspired_by', 'N/A')}").classes("text-sm text-gray-600")
			ui.label(f"🏋️ {len(workout.get('exercises', []))} exercises").classes("text-sm text-gray-600 mt-1")
			if duration:
				ui.label(f"⏱ ~{duration} min").classes("text-sm text-gray-600 mt-1")

			with ui.row().classes("w-full gap-2 mt-3"):
				ui.button("View Workout →", on_click=lambda w=workout: _open_premade_workout_dialog(w)).props("flat color=red").classes("flex-1")
				ui.button(icon="check_circle", on_click=lambda w=workout: _quick_log_premade(w)).props("flat color=green").tooltip("Quick log this workout")


def _open_premade_workout_dialog(workout):
	wtype = workout.get("type", "")
	gradient = PREMADE_GRADIENTS.get(wtype, "from-gray-500 to-gray-700")
	icon = PREMADE_ICONS.get(wtype, "🏋️")
	duration = workout.get("duration_minutes")

	with ui.dialog() as dialog, ui.card().classes("w-full max-w-2xl max-h-screen overflow-y-auto"):
		# Header banner
		with ui.element("div").classes(f"bg-gradient-to-r {gradient} p-6 text-white -mx-6 -mt-6 mb-4"):
			ui.label(icon).classes("text-5xl mb-2")
			ui.label(workout["name"]).classes("text-2xl font-bold")
			ui.label(wtype).classes("text-sm opacity-80 mt-1")
			ui.label(f"Inspired by {workout.get('inspired_by', '')}").classes("text-sm opacity-70")
			if duration:
				ui.label(f"⏱ ~{duration} minutes").classes("text-sm opacity-80 mt-1")

		# Log prompt
		recent_weight = tracker.get_most_recent_weight()
		weight_note = f"using your most recent weight ({recent_weight} kg)" if recent_weight else "no weight on record — will log as 0 kg"
		with ui.card().classes("w-full bg-green-50 border border-green-200 mb-4"):
			with ui.row().classes("items-center justify-between gap-2"):
				with ui.column().classes("flex-1"):
					ui.label("Ready to train?").classes("text-sm font-bold text-green-800")
					ui.label(f"Will log as {duration or 60} min · {weight_note}").classes("text-xs text-green-700")
				ui.button("Log Workout", icon="check_circle",
						  on_click=lambda w=workout, d=dialog: (_quick_log_premade(w), d.close())).props("color=green").classes("shrink-0")

		# Coach's notes
		if workout.get("notes"):
			with ui.card().classes("w-full bg-amber-50 border border-amber-200 mb-4"):
				with ui.row().classes("items-center gap-2 mb-2"):
					ui.label("📋").classes("text-xl")
					ui.label("Coach's Notes").classes("text-base font-bold text-amber-800")
				for note in workout["notes"]:
					with ui.row().classes("items-start gap-2 mb-1"):
						ui.label("•").classes("text-amber-600 font-bold mt-0.5")
						ui.label(note).classes("text-sm text-amber-900 flex-1")

		# Exercise list
		ui.label("Exercises").classes("text-lg font-bold text-gray-800 mb-3")
		for ex in workout.get("exercises", []):
			_exercise_card(ex, gradient)

		ui.button("Close", on_click=dialog.close, icon="close").props("flat color=gray").classes("w-full mt-2")

	dialog.open()


def _exercise_card(ex, gradient):
	with ui.card().classes("w-full mb-3 border border-gray-100 hover:border-gray-300 transition-colors"):
		with ui.row().classes("items-center gap-3 mb-2"):
			with ui.element("div").classes(f"bg-gradient-to-br {gradient} text-white rounded-full w-8 h-8 flex items-center justify-center font-bold text-sm"):
				ui.label(str(ex["id"]))
			ui.label(ex["name"]).classes("text-base font-bold text-gray-800 flex-1")

		with ui.row().classes("flex-wrap gap-2 mb-2"):
			with ui.element("div").classes("bg-gray-100 rounded px-2 py-1"):
				ui.label(f"📦 {ex['sets']} set{'s' if ex['sets'] != 1 else ''}").classes("text-xs text-gray-700")

			if "reps_min" in ex:
				rep_str = str(ex["reps_min"]) if ex["reps_min"] == ex.get("reps_max") else f"{ex['reps_min']}–{ex.get('reps_max', ex['reps_min'])}"
				with ui.element("div").classes("bg-red-100 rounded px-2 py-1"):
					ui.label(f"🔁 {rep_str} reps").classes("text-xs text-red-700")
			elif "distance_min_meters" in ex:
				dist_str = f"{ex['distance_min_meters']}–{ex.get('distance_max_meters', ex['distance_min_meters'])}m"
				with ui.element("div").classes("bg-green-100 rounded px-2 py-1"):
					ui.label(f"📏 {dist_str}").classes("text-xs text-green-700")

			with ui.element("div").classes("bg-blue-100 rounded px-2 py-1"):
				ui.label(f"🛠 {ex['equipment']}").classes("text-xs text-blue-700")

		if ex.get("description"):
			ui.label(ex["description"]).classes("text-sm text-gray-600 mb-1")
		if ex.get("cue"):
			with ui.element("div").classes("bg-yellow-50 border-l-4 border-yellow-400 pl-3 py-1 mt-1"):
				ui.label(f"💡 {ex['cue']}").classes("text-xs italic text-yellow-800")


def _quick_log_premade(workout):
	log_premade_workout(workout)
	create_dashboard.refresh()
	create_workout_history.refresh()
	ui.notify(f"✅ {workout['name']} logged!", type="positive")


@ui.page("/")
def main_page():
	async def handle_disconnect():
		await asyncio.sleep(2)  # small grace period in case of accidental refresh
		app.shutdown()

	app.on_disconnect(handle_disconnect)

	def reload_all():
		tracker.load_data()
		create_dashboard.refresh()
		create_workout_history.refresh()
		ui.notify("Data refreshed! 🔄", type="positive")

	create_header(on_refresh=reload_all)

	with ui.tabs().classes("w-full") as tabs:
		tab_dashboard = ui.tab("Dashboard", icon="dashboard")
		tab_workout = ui.tab("Log Workout", icon="fitness_center")
		tab_competition = ui.tab("Competition Prep", icon="emoji_events")
		tab_history = ui.tab("History", icon="history")
		tab_premade = ui.tab("Premade Workouts", icon="menu_book")

	with ui.tab_panels(tabs, value=tab_dashboard).classes("w-full"):
		with ui.tab_panel(tab_dashboard):
			create_dashboard()
		with ui.tab_panel(tab_workout):
			create_workout_log()
		with ui.tab_panel(tab_competition):
			create_competition_prep()
		with ui.tab_panel(tab_history):
			create_workout_history()
		with ui.tab_panel(tab_premade):
			create_premade_workouts()


if __name__ in {"__main__", "__mp_main__"}:
	ui.run(title="Combat Sports Tracker", host="0.0.0.0", port=8080, dark=True, reload=True)
