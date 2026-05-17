# Ships - Multi-threaded Flask Web Game

A simple web-based two-player battleship game implemented in Python using the **Flask** framework. This project demonstrates the practical application of **concurrency (threading)**, thread synchronization mechanisms (`Lock`, `Event`), and asynchronous frontend-backend communication using AJAX/Fetch API.

The application also features a built-in live chat with an automated background worker for message cleanup and profanity moderation.

---

## Key Features

- **Two-Player Support**: Independent game views for Player 1 and Player 2 via clean URL query parameters.
- **Asynchronous State Synchronization**: Real-time frontend updates (ship placements, firing results, and system turns) using JavaScript's `setInterval`.
- **Multi-threaded Chat Manager**:
  - **Real-time Moderation**: Automatically censors forbidden words (`"bad"`, `"lose"`, `"stupid"`, `"error"`) by replacing them with asterisks (`***`).
  - **Memory Cleanup**: Automatically prunes the chat history down to the last 10 messages every 5 seconds to prevent memory leaks.
- **Dynamic Thread Controls**: Toggle moderation and cleanup features on the fly directly from the user interface using thread-safe `threading.Event` flags.

---

## Architecture & Concurrency Control

The application utilizes a concurrent architecture to cleanly separate HTTP request handling from background maintenance tasks:

1. **Flask Main Thread**: Manages standard HTTP endpoints (`/attack`, `/place_ship`, `/state`, etc.). Since Flask runs in a multi-threaded mode (`threaded=True`), requests from both players can be processed in parallel.
2. **Background Worker (`chat_manager_worker`)**: A daemon thread running continuously in the background. It periodically checks the message stack to apply censorship and memory cleanup.
3. **Synchronization (`Lock`)**: A global `threading.Lock` ensures that data structures (`players`, `messages`, `attacks`) are safely modified without causing *Race Conditions* between Flask's request threads and the background manager.
4. **Signal Flagging (`Event`)**: `cleanup_event` and `moderator_event` serve as atomic, thread-safe switches to alter the background worker's routine logic instantly without restarting the server.

---

## Requirements & Installation

### Prerequisites
- Python 3.8 or higher
- A modern web browser with JavaScript enabled (Fetch API support)

### Installation Steps

1. Clone or download this repository to your local machine.
2. Install the required dependency:
   ```bash
   pip install Flask
