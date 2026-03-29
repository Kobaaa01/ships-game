from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

GRID_SIZE = 10

player_board = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
attack_board = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

messages = []

connected_players = 0


@app.route("/")
def index():
    global connected_players

    if connected_players == 0:
        player = "1"
    else:
        player = "2"

    connected_players += 1

    return render_template("index.html", player=player)


@app.route("/place_ship", methods=["POST"])
def place_ship():
    data = request.json
    row = data["row"]
    col = data["col"]

    player_board[row][col] = "S"

    return jsonify(success=True)


@app.route("/attack", methods=["POST"])
def attack():
    data = request.json
    row = data["row"]
    col = data["col"]

    attack_board[row][col] = "X"

    return jsonify(success=True)


@app.route("/send_message", methods=["POST"])
def send_message():
    data = request.json

    messages.append({
        "player": data["player"],
        "message": data["message"]
    })

    return jsonify(success=True)


@app.route("/get_messages")
def get_messages():
    return jsonify(messages=messages)


if __name__ == "__main__":
    app.run(debug=True)