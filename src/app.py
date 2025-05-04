from src.config.server import app

if __name__ == "__main__":
    app.run(transport="sse")
