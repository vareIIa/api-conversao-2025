import os
from Conversor import app

if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.getenv("APP_PORT", 6000))
    debug = os.getenv("FLASK_ENV", "production") == "development"

    try:
        app.run(host=host, port=port, debug=debug)
    except Exception as e:
        print(f"An error occurred: {e}")