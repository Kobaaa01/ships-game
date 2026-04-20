from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

MAX_SHIPS = 10

players = {
    "1": {"ships": set(), "ready": False},
    "2": {"ships": set(), "ready": False}
}

connected_players = 0
game_started = False
current_turn = "1"

attacks = []
messages = []


def coord(r, c):
    return f"{r},{c}"


@app.route("/")
def index():
    global connected_players

    player = "1" if connected_players == 0 else "2"
    connected_players += 1

    return render_template("index.html", player=player)


@app.route("/place_ship", methods=["POST"])
def place_ship():
    data = request.json
    player = data["player"]

    if game_started:
        return jsonify(success=False, error="Game already started")

    ships = players[player]["ships"]

    if len(ships) >= MAX_SHIPS:
        return jsonify(success=False, error="Max 10 ships")

    ships.add(coord(data["row"], data["col"]))
    return jsonify(success=True)


@app.route("/ready", methods=["POST"])
def ready():
    global game_started, current_turn

    player = request.json["player"]

    if len(players[player]["ships"]) != MAX_SHIPS:
        return jsonify(success=False, error="Place 10 ships first")

    players[player]["ready"] = True

    if players["1"]["ready"] and players["2"]["ready"]:
        game_started = True
        current_turn = "1"

    return jsonify(success=True)


@app.route("/attack", methods=["POST"])
def attack():
    global current_turn

    if not game_started:
        return jsonify(success=False, error="Game not started")

    data = request.json
    player = data["player"]

    if player != current_turn:
        return jsonify(success=False, error="Not your turn")

    enemy = "2" if player == "1" else "1"
    target = coord(data["row"], data["col"])

    result = "hit" if target in players[enemy]["ships"] else "miss"

    attacks.append({
        "player": player,
        "row": data["row"],
        "col": data["col"],
        "result": result
    })

    current_turn = enemy

    return jsonify(success=True, result=result)


@app.route("/state")
def state():
    return jsonify({
        "started": game_started,
        "turn": current_turn,
        "players": {
            "1": {
                "ready": players["1"]["ready"],
                "ships": len(players["1"]["ships"])
            },
            "2": {
                "ready": players["2"]["ready"],
                "ships": len(players["2"]["ships"])
            }
        },
        "attacks": attacks
    })


@app.route("/send_message", methods=["POST"])
def send_message():
    messages.append(request.json)
    return jsonify(success=True)


@app.route("/get_messages")
def get_messages():
    return jsonify(messages=messages)


if __name__ == "__main__":
    app.run(debug=True)