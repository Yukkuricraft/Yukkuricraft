
from src.api import create_app

from src.api.lib.sockets import socketio

def main():
    app = create_app()
    socketio.run(app, debug=True, host="0.0.0.0", port=5001)

if __name__ == "__main__":
    main()