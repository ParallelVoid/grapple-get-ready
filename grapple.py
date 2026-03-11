import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

from nicegui import ui
import plotly.graph_objects as go

# Data storage
DATA_FILE = Path("combat_sports_data.json")
PREMADE_WORKOUTS_DIR = Path("workouts")


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


def load_premade_workouts():
	if not PREMADE_WORKOUTS_DIR.exists():
		return []
	workouts = []
	for json_file in sorted(PREMADE_WORKOUTS_DIR.glob("*.json")):
		try:
			with open(json_file, "r") as f:
				data = json.load(f)
				# Support both {"workout": {...}} and bare {...} structures
				workout = data.get("workout", data)
				workouts.append(workout)
		except Exception as e:
			print(f"Error loading {json_file}: {e}")
	return workouts


tracker = CombatSportsTracker()


def create_header():
	with ui.header().classes("items-center justify-between bg-red-600 !important text-white"):
		ui.label("Grapple Get Ready 🤼‍♂️").classes("text-2xl font-bold")
		ui.button(
			"Settings",
			icon="settings",
			on_click=lambda: ui.notify("Settings coming soon!"),
		).props("flat")


def create_training_frequency_chart():
	if not tracker.workouts:
		return None

	weekly_data = defaultdict(lambda: defaultdict(int))
	workout_type_counts = defaultdict(int)

	for workout in tracker.workouts:
		date = datetime.strptime(workout["date"], "%Y-%m-%d")
		week_start = date - timedelta(days=date.weekday())
		week_key = week_start.strftime("%Y-%m-%d")
		workout_type = workout["type"]
		weekly_data[week_key][workout_type] += 1
		workout_type_counts[workout_type] += 1

	sorted_weeks = sorted(weekly_data.keys())
	all_types = sorted(workout_type_counts.keys())

	fig = go.Figure()

	colors = {
		"Judo": "#FF6B6B",
		"Sambo": "#4ECDC4",
		"Wrestling": "#F70046",
		"BJJ/Grappling": "#45B7D1",
		"MMA": "#FFA07A",
		"Strength & Conditioning": "#98D8C8",
		"Cardio": "#F7DC6F",
		"Technique Drilling": "#BB8FCE",
	}

	for workout_type in all_types:
		counts = [weekly_data[week].get(workout_type, 0) for week in sorted_weeks]
		fig.add_trace(go.Bar(
			x=sorted_weeks,
			y=counts,
			name=workout_type,
			marker_color=colors.get(workout_type, "#95A5A6"),
		))

	fig.update_layout(
		title="Weekly Training Frequency",
		xaxis_title="Week",
		yaxis_title="Number of Sessions",
		barmode='stack',
		height=400,
		hovermode='x unified',
		plot_bgcolor='rgba(0,0,0,0)',
		paper_bgcolor='rgba(0,0,0,0)',
		font=dict(size=12),
		margin=dict(l=50, r=50, t=50, b=50),
	)

	return fig


def create_weight_tracker_chart():
	if not tracker.workouts:
		return None

	dates = []
	weights = []

	for workout in sorted(tracker.workouts, key=lambda x: x.get("date", "")):
		if workout.get("weight") and workout["weight"] > 0:
			dates.append(workout["date"])
			weights.append(workout["weight"])

	if not dates:
		return None

	fig = go.Figure()

	fig.add_trace(go.Scatter(
		x=dates,
		y=weights,
		mode='lines+markers',
		name='Weight',
		line=dict(color='#3498DB', width=3),
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
				mode='lines',
				name=f'{comp["name"]} Target',
				line=dict(color='#E74C3C', width=2, dash='dash'),
				showlegend=True,
			))
			fig.add_annotation(
				x=comp["date"],
				y=target_weight,
				text=f'{comp["name"]}<br>{comp["weight_class"]}',
				showarrow=True,
				arrowhead=2,
				arrowsize=1,
				arrowwidth=2,
				arrowcolor='#E74C3C',
				bgcolor='#E74C3C',
				font=dict(color='white', size=10),
				bordercolor='#E74C3C',
				borderwidth=2,
				borderpad=4,
			)
		except (ValueError, IndexError):
			pass

	if upcoming_comps and weights:
		current_weight = weights[-1]
		try:
			target_weight = float(upcoming_comps[0]["weight_class"].split()[0])
			weight_diff = current_weight - target_weight
			fig.add_annotation(
				x=dates[-1],
				y=current_weight,
				text=f'Current: {current_weight} kg<br>To cut: {weight_diff:.1f} kg',
				showarrow=True,
				arrowhead=2,
				ax=40,
				ay=-40,
				bgcolor='#3498DB',
				font=dict(color='white', size=10),
				bordercolor='#3498DB',
				borderwidth=2,
				borderpad=4,
			)
		except (ValueError, IndexError):
			pass

	fig.update_layout(
		title="Weight Cut Tracker",
		xaxis_title="Date",
		yaxis_title="Weight (kg)",
		height=400,
		hovermode='x unified',
		plot_bgcolor='rgba(0,0,0,0)',
		paper_bgcolor='rgba(0,0,0,0)',
		font=dict(size=12),
		margin=dict(l=50, r=50, t=50, b=50),
	)

	return fig


def create_dashboard():
	with ui.row().classes("w-full gap-4 p-4"):
		with ui.column().classes("flex-1 gap-4"):
			with ui.card().classes(
				"w-full bg-gradient-to-r from-gray-800 to-gray-900 text-white p-6"
			):
				ui.label("Competition Record").classes("text-2xl font-bold mb-4")

				wins = 0
				losses = 0
				draws = 0

				for comp in tracker.competitions:
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

				with ui.row().classes("w-full gap-8 items-center"):
					with ui.column().classes("items-center"):
						ui.label("Overall Record").classes("text-sm opacity-80")
						ui.label(f"{wins}-{losses}-{draws}").classes("text-5xl font-bold")
						if wins + losses + draws > 0:
							win_rate = (wins / (wins + losses + draws) * 100)
							ui.label(f"{win_rate:.1f}% Win Rate").classes("text-sm opacity-80 mt-2")

					ui.separator().props("vertical").classes("bg-white opacity-20")

					with ui.column().classes("flex-1"):
						ui.label("By Sport").classes("text-sm opacity-80 mb-2")

						sports_stats = {}
						for comp in tracker.competitions:
							sport = comp.get("sport", "Unknown")
							if comp.get("type") == "tournament" and comp.get("matches"):
								for match in comp["matches"]:
									if sport not in sports_stats:
										sports_stats[sport] = {"wins": 0, "losses": 0, "draws": 0}
									if match["result"] == "Win":
										sports_stats[sport]["wins"] += 1
									elif match["result"] == "Loss":
										sports_stats[sport]["losses"] += 1
									elif match["result"] == "Draw":
										sports_stats[sport]["draws"] += 1
							else:
								result = comp.get("result", "Upcoming")
								if result not in ("Upcoming", "No Contest"):
									if sport not in sports_stats:
										sports_stats[sport] = {"wins": 0, "losses": 0, "draws": 0}
									if result == "Win":
										sports_stats[sport]["wins"] += 1
									elif result == "Loss":
										sports_stats[sport]["losses"] += 1
									elif result == "Draw":
										sports_stats[sport]["draws"] += 1

						if sports_stats:
							with ui.grid(columns=2).classes("w-full gap-4"):
								for sport, stats in sorted(sports_stats.items()):
									with ui.card().classes("bg-gray-700 p-3"):
										ui.label(sport).classes("text-sm font-semibold")
										record_str = f"{stats['wins']}-{stats['losses']}"
										if stats["draws"] > 0:
											record_str += f"-{stats['draws']}"
										ui.label(record_str).classes("text-lg font-bold")
						else:
							ui.label("No completed competitions yet").classes("text-sm opacity-60 italic")

			with ui.row().classes("w-full gap-4"):
				with ui.card().classes("flex-1 bg-gradient-to-br from-red-600 to-red-800 text-white"):
					ui.label("Total Workouts").classes("text-sm opacity-80")
					ui.label(str(len(tracker.workouts))).classes("text-4xl font-bold")

				with ui.card().classes("flex-1 bg-gradient-to-br from-orange-600 to-orange-800 text-white"):
					ui.label("Upcoming Competitions").classes("text-sm opacity-80")
					today = datetime.now().strftime("%Y-%m-%d")
					upcoming = len([c for c in tracker.competitions if c.get("result", "Upcoming") == "Upcoming" and c.get("date", "") >= today])
					ui.label(str(upcoming)).classes("text-4xl font-bold")

				with ui.card().classes("flex-1 bg-gradient-to-br from-gray-700 to-gray-900 text-white"):
					ui.label("This Week").classes("text-sm opacity-80")
					week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
					week_workouts = len([w for w in tracker.workouts if w.get("date", "") >= week_ago])
					ui.label(str(week_workouts)).classes("text-4xl font-bold")

		with ui.column().classes("w-80 gap-4"):
			with ui.card().classes("w-80 p-6 bg-gradient-to-br from-amber-50 to-yellow-100"):
				ui.label("Medal Collection").classes("text-xl font-bold mb-4 text-gray-800")

				medals = {"Gold": 0, "Silver": 0, "Bronze": 0}
				for comp in tracker.competitions:
					if comp.get("type") == "tournament" and comp.get("medal") and comp["medal"] != "None":
						medals[comp["medal"]] = medals.get(comp["medal"], 0) + 1

				with ui.column().classes("w-full gap-3"):
					with ui.row().classes("w-full items-center justify-between p-3 bg-white rounded-lg"):
						with ui.row().classes("items-center gap-3"):
							ui.label("🥇").classes("text-3xl")
							ui.label("Gold").classes("text-lg font-semibold text-gray-800")
						ui.label(str(medals["Gold"])).classes("text-2xl font-bold text-yellow-600")

					with ui.row().classes("w-full items-center justify-between p-3 bg-white rounded-lg"):
						with ui.row().classes("items-center gap-3"):
							ui.label("🥈").classes("text-3xl")
							ui.label("Silver").classes("text-lg font-semibold text-gray-800")
						ui.label(str(medals["Silver"])).classes("text-2xl font-bold text-gray-500")

					with ui.row().classes("w-full items-center justify-between p-3 bg-white rounded-lg"):
						with ui.row().classes("items-center gap-3"):
							ui.label("🥉").classes("text-3xl")
							ui.label("Bronze").classes("text-lg font-semibold text-gray-800")
						ui.label(str(medals["Bronze"])).classes("text-2xl font-bold text-orange-700")

				if sum(medals.values()) == 0:
					ui.label("No medals yet - keep training!").classes("text-sm text-gray-600 text-center mt-2 italic")

	with ui.row().classes("w-full gap-4 px-4"):
		freq_chart = create_training_frequency_chart()
		if freq_chart:
			with ui.card().classes("flex-1"):
				ui.plotly(freq_chart).classes("w-full")

		weight_chart = create_weight_tracker_chart()
		if weight_chart:
			with ui.card().classes("flex-1"):
				ui.plotly(weight_chart).classes("w-full")


def create_workout_log():
	with ui.column().classes("w-full gap-4 p-4"):
		ui.label("Log New Workout").classes("text-2xl font-bold text-gray-800")

		with ui.card().classes("w-full"):
			workout_type = ui.select(
				["Judo", "Sambo", "Wrestling", "BJJ/Grappling", "MMA", "Strength & Conditioning", "Cardio", "Technique Drilling"],
				label="Workout Type",
				value="Judo",
			).classes("w-full")

			date_input = ui.input("Date", value=datetime.now().strftime("%Y-%m-%d")).classes("w-full").props("readonly")
			with date_input.add_slot("append"):
				ui.icon("edit_calendar").on("click", lambda: date_dialog.open()).classes("cursor-pointer")

			with ui.dialog() as date_dialog, ui.card():
				ui.date().bind_value(date_input).props("minimal")
				ui.button("Close", on_click=date_dialog.close)

			duration = ui.number(label="Duration (minutes)", value=60, min=1).classes("w-full")
			intensity = ui.select(
				["Light", "Moderate", "Hard", "Very Hard", "Competition Intensity"],
				label="Intensity",
				value="Moderate",
			).classes("w-full")
			weight = ui.number(label="Weight (kg)", value=0, step=0.1).classes("w-full")
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

			ui.button("Log Workout", on_click=log_workout, icon="add_circle").props("color=red").classes("w-full")


def create_competition_prep():
	with ui.column().classes("w-full gap-4 p-4"):
		ui.label("Competition Preparation").classes("text-2xl font-bold text-gray-800")

		with ui.card().classes("w-full"):
			ui.label("Add/Update Competition").classes("text-lg font-semibold mb-2")
			ui.label("For tournaments with multiple matches, add each match separately or use the match tracker below.").classes("text-xs text-gray-600 mb-3 italic")

			comp_name = ui.input(label="Competition Name", placeholder="e.g., State Championships").classes("w-full")
			comp_sport = ui.select(["Judo", "Sambo", "BJJ/Grappling", "MMA", "Kickboxing", "Wrestling"], label="Sport", value="Judo").classes("w-full")
			comp_type = ui.select(["Single Match", "Tournament (Multiple Matches)"], label="Competition Type", value="Single Match").classes("w-full")

			comp_date_input = ui.input("Competition Date").classes("w-full").props("readonly")
			with comp_date_input.add_slot("append"):
				ui.icon("edit_calendar").on("click", lambda: comp_date_dialog.open()).classes("cursor-pointer")

			with ui.dialog() as comp_date_dialog, ui.card():
				ui.date().bind_value(comp_date_input).props("minimal")
				ui.button("Close", on_click=comp_date_dialog.close)

			weight_class = ui.input(label="Weight Class", placeholder="e.g., 73 kgs").classes("w-full")
			current_weight = ui.number(label="Current Weight", value=0, step=0.1).classes("w-full")

			with ui.column().classes("w-full") as single_match_section:
				comp_result = ui.select(["Upcoming", "Win", "Loss", "Draw", "No Contest"], label="Result", value="Upcoming").classes("w-full")
				result_notes = ui.textarea(label="Result Notes (optional)", placeholder="e.g., TKO Round 2, Decision, Submission").classes("w-full")

			matches_list = []

			@ui.refreshable
			def matches_container():
				if matches_list:
					ui.label("Matches").classes("text-sm font-semibold mt-2")
					for i, match in enumerate(matches_list):
						with ui.card().classes("bg-gray-50 p-2 mb-2"):
							with ui.row().classes("w-full justify-between items-center"):
								ui.label(f"Match {i + 1}: {match['result']} - {match['notes']}").classes("text-sm")
								ui.button(icon="delete", on_click=lambda idx=i: remove_match(idx)).props("flat dense")

			def remove_match(idx):
				matches_list.pop(idx)
				matches_container.refresh()

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

			def update_visibility():
				if comp_type.value == "Single Match":
					single_match_section.set_visibility(True)
					tournament_section.set_visibility(False)
				else:
					single_match_section.set_visibility(False)
					tournament_section.set_visibility(True)

			comp_type.on("update:model-value", update_visibility)
			update_visibility()

			def add_comp():
				if comp_type.value == "Single Match":
					comp_data = {
						"name": comp_name.value,
						"sport": comp_sport.value,
						"type": "single",
						"date": comp_date_input.value,
						"weight_class": weight_class.value,
						"current_weight": current_weight.value,
						"result": comp_result.value,
						"result_notes": result_notes.value,
						"created": datetime.now().isoformat(),
					}
				else:
					comp_data = {
						"name": comp_name.value,
						"sport": comp_sport.value,
						"type": "tournament",
						"date": comp_date_input.value,
						"weight_class": weight_class.value,
						"current_weight": current_weight.value,
						"matches": matches_list.copy(),
						"medal": tournament_medal.value,
						"result": "Completed" if matches_list else "Upcoming",
						"created": datetime.now().isoformat(),
					}

				tracker.add_competition(comp_data)
				ui.notify("Competition added! 🥇", type="positive")
				comp_name.value = ""
				weight_class.value = ""
				result_notes.value = ""
				matches_list.clear()
				matches_container.refresh()
				comp_list_container.refresh()

			ui.button("Add Competition", on_click=add_comp, icon="emoji_events").props("color=orange").classes("w-full")

		@ui.refreshable
		def comp_list_container():
			if tracker.competitions:
				ui.label("Competitions").classes("text-xl font-bold mt-4")

				def edit_competition(comp_idx):
					comp = tracker.competitions[comp_idx]
					with ui.dialog() as edit_dialog, ui.card().classes("w-full max-w-2xl"):
						ui.label(f"Edit: {comp['name']}").classes("text-xl font-bold mb-4")

						if comp.get("type") == "tournament":
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

							def save_tournament():
								tracker.competitions[comp_idx]["matches"] = edit_matches
								tracker.competitions[comp_idx]["medal"] = edit_medal.value
								tracker.save_data()
								ui.notify("Tournament updated! 🏆", type="positive")
								edit_dialog.close()
								comp_list_container.refresh()

							with ui.row().classes("w-full gap-2 mt-4"):
								ui.button("Save", on_click=save_tournament, icon="save").props("color=green")
								ui.button("Cancel", on_click=edit_dialog.close).props("flat")
						else:
							edit_result = ui.select(["Upcoming", "Win", "Loss", "Draw", "No Contest"], label="Result", value=comp.get("result", "Upcoming")).classes("w-full")
							edit_notes = ui.textarea(label="Result Notes", value=comp.get("result_notes", "")).classes("w-full")

							def save_single():
								tracker.competitions[comp_idx]["result"] = edit_result.value
								tracker.competitions[comp_idx]["result_notes"] = edit_notes.value
								tracker.save_data()
								ui.notify("Competition updated! ✅", type="positive")
								edit_dialog.close()
								comp_list_container.refresh()

							with ui.row().classes("w-full gap-2 mt-4"):
								ui.button("Save", on_click=save_single, icon="save").props("color=green")
								ui.button("Cancel", on_click=edit_dialog.close).props("flat")

					edit_dialog.open()

				def delete_competition(comp_idx):
					cname = tracker.competitions[comp_idx]["name"]
					tracker.competitions.pop(comp_idx)
					tracker.save_data()
					ui.notify(f"Deleted {cname}", type="warning")
					comp_list_container.refresh()

				for idx, comp in enumerate(sorted(enumerate(tracker.competitions), key=lambda x: x[1].get("date", ""), reverse=True)):
					original_idx = idx
					comp = comp[1]

					if comp.get("type") == "tournament":
						card_color = "bg-purple-100 border-purple-500" if comp.get("matches") else "bg-blue-100 border-blue-500"
					else:
						result_colors = {
							"Win": "bg-green-100 border-green-500",
							"Loss": "bg-red-100 border-red-500",
							"Draw": "bg-yellow-100 border-yellow-500",
							"No Contest": "bg-gray-100 border-gray-500",
							"Upcoming": "bg-blue-100 border-blue-500",
						}
						card_color = result_colors.get(comp.get("result", "Upcoming"), "bg-white")

					with ui.card().classes(f"w-full border-l-4 {card_color}"):
						with ui.row().classes("w-full items-start justify-between gap-4"):
							with ui.column().classes("flex-1"):
								with ui.row().classes("items-center gap-2"):
									ui.label(comp["name"]).classes("text-lg font-bold")
									if comp.get("type") == "tournament" and comp.get("medal") and comp["medal"] != "None":
										medal_emoji = {"Gold": "🥇", "Silver": "🥈", "Bronze": "🥉"}
										ui.label(medal_emoji.get(comp["medal"], "")).classes("text-xl")

								ui.label(f"{comp.get('sport', 'N/A')} | 📅 {comp['date']} | ⚖️ {comp['weight_class']}").classes("text-sm text-gray-600")
								if comp.get("current_weight"):
									ui.label(f"Current: {comp['current_weight']} kg").classes("text-sm")

								if comp.get("type") == "tournament" and comp.get("matches"):
									t_wins = sum(1 for m in comp["matches"] if m["result"] == "Win")
									t_losses = sum(1 for m in comp["matches"] if m["result"] == "Loss")
									t_draws = sum(1 for m in comp["matches"] if m["result"] == "Draw")
									ui.label(f"🏆 Tournament: {t_wins}-{t_losses}-{t_draws}").classes("text-sm font-semibold mt-1")
									for i, match in enumerate(comp["matches"]):
										match_color = "text-green-700" if match["result"] == "Win" else "text-red-700" if match["result"] == "Loss" else "text-yellow-700"
										match_text = f"  Match {i + 1}: {match['result']}"
										if match.get("notes"):
											match_text += f" - {match['notes']}"
										ui.label(match_text).classes(f"text-xs {match_color}")
								elif comp.get("result") and comp["result"] != "Upcoming":
									result_label = comp["result"]
									if comp.get("result_notes"):
										result_label += f" - {comp['result_notes']}"
									ui.label(result_label).classes("text-sm font-semibold mt-1")

							with ui.column().classes("gap-1"):
								ui.button(icon="edit", on_click=lambda idx=original_idx: edit_competition(idx)).props("flat dense color=blue").classes("w-8 h-8")
								ui.button(icon="delete", on_click=lambda idx=original_idx: delete_competition(idx)).props("flat dense color=red").classes("w-8 h-8")

		comp_list_container()


def create_workout_history():
	with ui.column().classes("w-full gap-4 p-4"):
		ui.label("Training History").classes("text-2xl font-bold text-gray-800")

		@ui.refreshable
		def workout_list_container():
			if not tracker.workouts:
				ui.label("No workouts logged yet. Start training! 🥊").classes("text-gray-500")
			else:
				for workout in sorted(tracker.workouts, key=lambda x: x.get("date", ""), reverse=True)[:20]:
					with ui.card().classes("w-full hover:shadow-lg transition-shadow"):
						with ui.row().classes("w-full items-center gap-4"):
							icon_map = {
								"Judo": "🥋",
								"Sambo": "🦅",
								"Wrestling": "🤼",
								"BJJ/Grappling": "🐙",
								"MMA": "🥊",
								"Strength & Conditioning": "💪",
								"Cardio": "🏃",
								"Technique Drilling": "🎯",
							}
							ui.label(icon_map.get(workout["type"], "🥊")).classes("text-3xl")

							with ui.column().classes("flex-1"):
								ui.label(workout["type"]).classes("text-lg font-bold")
								ui.label(f"{workout['date']} | {workout['duration']} min | {workout['intensity']}").classes("text-sm text-gray-600")
								if workout.get("weight"):
									ui.label(f"Weight: {workout['weight']} kg").classes("text-sm text-gray-500")
								if workout.get("notes"):
									ui.label(workout["notes"]).classes("text-sm text-gray-700 mt-1")

		workout_list_container()


def get_most_recent_weight():
	"""Return the most recent weight logged, or 0 if none."""
	weight_entries = [
		w for w in tracker.workouts
		if w.get("weight") and w["weight"] > 0
	]
	if not weight_entries:
		return 0
	latest = max(weight_entries, key=lambda w: w.get("date", ""))
	return latest["weight"]


def log_premade_workout(workout):
	"""Log a premade workout using the workout type, duration estimate, and most recent weight."""
	recent_weight = get_most_recent_weight()
	# Map premade workout type to tracker workout types
	type_map = {
		"Judo Technique Practice": "Judo",
		"Strength and Conditioning": "Strength & Conditioning",
		"BJJ/Grappling": "BJJ/Grappling",
		"MMA": "MMA",
		"Cardio": "Cardio",
	}
	workout_type = type_map.get(workout.get("type", ""), workout.get("type", "Judo"))
	duration = workout.get("duration_minutes", 60)

	workout_data = {
		"type": workout_type,
		"date": datetime.now().strftime("%Y-%m-%d"),
		"duration": duration,
		"intensity": "Moderate",
		"weight": recent_weight,
		"notes": f"Premade workout: {workout['name']}",
		"timestamp": datetime.now().isoformat(),
	}
	tracker.add_workout(workout_data)


def create_premade_workouts():
	premade_workouts = load_premade_workouts()

	type_icons = {
		"Judo Technique Practice": "🥋",
		"Strength and Conditioning": "💪",
		"BJJ/Grappling": "🤼",
		"MMA": "🥊",
		"Cardio": "🏃",
	}

	type_colors = {
		"Judo Technique Practice": "from-red-500 to-red-700",
		"Strength and Conditioning": "from-blue-500 to-blue-700",
		"BJJ/Grappling": "from-purple-500 to-purple-700",
		"MMA": "from-orange-500 to-orange-700",
		"Cardio": "from-green-500 to-green-700",
	}

	with ui.column().classes("w-full gap-4 p-4"):
		ui.label("Premade Workouts").classes("text-2xl font-bold text-gray-800")
		ui.label("Select a workout to view details and exercises.").classes("text-sm text-gray-500 -mt-2 mb-2")

		if not premade_workouts:
			ui.label("No premade workouts found. Add JSON files to the workouts/ folder.").classes("text-gray-500 italic")
			return

		with ui.row().classes("w-full flex-wrap gap-4"):
			for workout in premade_workouts:
				wtype = workout.get("type", "")
				icon = type_icons.get(wtype, "🏋️")
				gradient = type_colors.get(wtype, "from-gray-500 to-gray-700")
				duration = workout.get("duration_minutes", None)

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
							def open_workout_dialog(w=workout):
								wt = w.get("type", "")
								grad = type_colors.get(wt, "from-gray-500 to-gray-700")
								ic = type_icons.get(wt, "🏋️")
								dur = w.get("duration_minutes", None)

								with ui.dialog() as dlg, ui.card().classes("w-full max-w-2xl max-h-screen overflow-y-auto"):
									with ui.element("div").classes(f"bg-gradient-to-r {grad} p-6 text-white -mx-6 -mt-6 mb-4"):
										ui.label(ic).classes("text-5xl mb-2")
										ui.label(w["name"]).classes("text-2xl font-bold")
										ui.label(wt).classes("text-sm opacity-80 mt-1")
										ui.label(f"Inspired by {w.get('inspired_by', '')}").classes("text-sm opacity-70")
										if dur:
											ui.label(f"⏱ ~{dur} minutes").classes("text-sm opacity-80 mt-1")

									# Log button at top of dialog
									recent_weight = get_most_recent_weight()
									weight_note = f"using your most recent weight ({recent_weight} kg)" if recent_weight else "no weight on record — will log as 0 kg"

									with ui.card().classes("w-full bg-green-50 border border-green-200 mb-4"):
										with ui.row().classes("items-center justify-between gap-2"):
											with ui.column().classes("flex-1"):
												ui.label("Ready to train?").classes("text-sm font-bold text-green-800")
												ui.label(f"Will log as {dur or 60} min · {weight_note}").classes("text-xs text-green-700")

											def do_log(w=w, d=dlg):
												log_premade_workout(w)
												ui.notify(f"✅ {w['name']} logged!", type="positive")
												d.close()

											ui.button("Log Workout", on_click=do_log, icon="check_circle").props("color=green").classes("shrink-0")

									# Coach's Notes
									if w.get("notes"):
										with ui.card().classes("w-full bg-amber-50 border border-amber-200 mb-4"):
											with ui.row().classes("items-center gap-2 mb-2"):
												ui.label("📋").classes("text-xl")
												ui.label("Coach's Notes").classes("text-base font-bold text-amber-800")
											for note in w["notes"]:
												with ui.row().classes("items-start gap-2 mb-1"):
													ui.label("•").classes("text-amber-600 font-bold mt-0.5")
													ui.label(note).classes("text-sm text-amber-900 flex-1")

									# Exercises
									ui.label("Exercises").classes("text-lg font-bold text-gray-800 mb-3")

									for ex in w.get("exercises", []):
										with ui.card().classes("w-full mb-3 border border-gray-100 hover:border-gray-300 transition-colors"):
											with ui.row().classes("items-center gap-3 mb-2"):
												with ui.element("div").classes(f"bg-gradient-to-br {grad} text-white rounded-full w-8 h-8 flex items-center justify-center font-bold text-sm"):
													ui.label(str(ex["id"]))
												ui.label(ex["name"]).classes("text-base font-bold text-gray-800 flex-1")

											with ui.row().classes("flex-wrap gap-2 mb-2"):
												with ui.element("div").classes("bg-gray-100 rounded px-2 py-1"):
													ui.label(f"📦 {ex['sets']} set{'s' if ex['sets'] != 1 else ''}").classes("text-xs text-gray-700")

												if "reps_min" in ex:
													rep_str = f"{ex['reps_min']}" if ex["reps_min"] == ex.get("reps_max") else f"{ex['reps_min']}–{ex.get('reps_max', ex['reps_min'])}"
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

									ui.button("Close", on_click=dlg.close, icon="close").props("flat color=gray").classes("w-full mt-2")

								dlg.open()

							ui.button("View Workout →", on_click=open_workout_dialog).props("flat color=red").classes("flex-1")

							def quick_log(w=workout):
								log_premade_workout(w)
								ui.notify(f"✅ {w['name']} logged!", type="positive")

							ui.button(icon="check_circle", on_click=quick_log).props("flat color=green").tooltip("Quick log this workout")


@ui.page("/")
def main_page():
	create_header()

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
	ui.run(title="Combat Sports Tracker", dark=False, reload=False)
