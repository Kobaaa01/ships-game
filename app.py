from flask import Flask, render_template, request, jsonify
from threading import Lock
import threading
import time

app = Flask(__name__)
MAX_SHIPS = 10

players = {
    "1": {"ships": set(), "ready": False},
    "2": {"ships": set(), "ready": False}
}

game_started = False
current_turn = "1"
winner = None
attacks = []
messages = []

lock = Lock()

# 🔹 Kontrola wątków
cleanup_event = threading.Event()
cleanup_event.set()

moderator_event = threading.Event()
moderator_event.set()

# Lista słów do moderacji
FORBIDDEN_WORDS = ["bad", "lose", "stupid", "error"]

def coord(r, c):
    return f"{r},{c}"

def chat_manager_worker():
    last_cleanup_time = time.time()
    
    while True:
        time.sleep(0.1)  # Częstotliwość sprawdzania moderatora
        current_time = time.time()
        
        with lock:
            # 1. MODERACJA (Działa prawie w czasie rzeczywistym)
            if moderator_event.is_set():
                for m in messages:
                    msg_text = m["message"].lower()
                    for word in FORBIDDEN_WORDS:
                        if word in msg_text:
                            m["message"] = m["message"].replace(word, "***")
            
            # 2. CLEANUP (Działa co 5 sekund)
            if cleanup_event.is_set() and (current_time - last_cleanup_time > 5):
                if len(messages) > 10:
                    messages[:] = messages[-10:]
                last_cleanup_time = current_time

# -------------------
# TOGGLE CONTROLS
# -------------------
@app.route("/toggle_cleanup", methods=["POST"])
def toggle_cleanup():
    if cleanup_event.is_set():
        cleanup_event.clear()
        return jsonify(status="OFF")
    else:
        cleanup_event.set()
        return jsonify(status="ON")

@app.route("/toggle_moderator", methods=["POST"])
def toggle_moderator():
    if moderator_event.is_set():
        moderator_event.clear()
        return jsonify(status="OFF")
    else:
        moderator_event.set()
        return jsonify(status="ON")

# -------------------
# INDEX
# -------------------
@app.route("/")
def index():
    player = request.args.get("player")
    if player not in ["1", "2"]:
        return "Use /?player=1 or /?player=2"
    return render_template("index.html", player=player)

# -------------------
# PLACE SHIP
# -------------------
@app.route("/place_ship", methods=["POST"])
def place_ship():
    with lock:
        data = request.json
        player = data["player"]
        if game_started:
            return jsonify(success=False, error="Game already started")
        if players[player]["ready"]:
            return jsonify(success=False, error="Already ready")
        ships = players[player]["ships"]
        if len(ships) >= MAX_SHIPS:
            return jsonify(success=False, error="Max 10 ships")
        ships.add(coord(data["row"], data["col"]))
        return jsonify(success=True)

# -------------------
# READY
# -------------------
@app.route("/ready", methods=["POST"])
def ready():
    global game_started, current_turn
    with lock:
        player = request.json["player"]
        if len(players[player]["ships"]) != MAX_SHIPS:
            return jsonify(success=False, error="Place 10 ships first")
        players[player]["ready"] = True
        if players["1"]["ready"] and players["2"]["ready"]:
            game_started = True
            current_turn = "1"
        return jsonify(success=True)

# -------------------
# ATTACK
# -------------------

@app.route("/attack", methods=["POST"])
def attack():
    global current_turn, winner
    with lock:
        if not game_started:
            return jsonify(success=False, error="Game not started")
        if winner:
            return jsonify(success=False, error=f"Game over! Winner: Player {winner}")
            
        data = request.json
        player = data["player"]
        if player != current_turn:
            return jsonify(success=False, error="Not your turn")
            
        enemy = "2" if player == "1" else "1"
        target = coord(data["row"], data["col"])
        
        # Zapobieganie strzelaniu dwa razy w to samo miejsce
        if any(a["row"] == data["row"] and a["col"] == data["col"] and a["player"] == player for a in attacks):
            return jsonify(success=False, error="Already attacked here")

        result = "hit" if target in players[enemy]["ships"] else "miss"
        attacks.append({
            "player": player,
            "row": data["row"],
            "col": data["col"],
            "result": result
        })

        # Sprawdzenie warunku wygranej
        hits = len([a for a in attacks if a["player"] == player and a["result"] == "hit"])
        if hits >= MAX_SHIPS:
            winner = player

        current_turn = enemy
        return jsonify(success=True, result=result)
# -------------------
# STATE
# -------------------

@app.route("/state")
def state():
    player_id = request.args.get("player") # Pobieramy id gracza z query params
    with lock:
        return jsonify({
            "started": game_started,
            "turn": current_turn,
            "players": {
                "1": {
                    "ready": players["1"]["ready"],
                    "ships_count": len(players["1"]["ships"])
                },
                "2": {
                    "ready": players["2"]["ready"],
                    "ships_count": len(players["2"]["ships"])
                }
            },
            # Dodajemy listę statków gracza, aby mógł je odtworzyć na planszy
            "my_ships": list(players[player_id]["ships"]) if player_id in players else [],
            "attacks": attacks
        })
# -------------------
# CHAT
# -------------------
@app.route("/send_message", methods=["POST"])
def send_message():
    with lock:
        messages.append(request.json)
    return jsonify(success=True)

@app.route("/get_messages")
def get_messages():
    with lock:
        return jsonify(messages=messages)

# -------------------
# RUN
# -------------------
if __name__ == "__main__":
    # Start Unified Manager Thread
    manager_thread = threading.Thread(target=chat_manager_worker, daemon=True)
    manager_thread.start()

    app.run(debug=True, threaded=True)