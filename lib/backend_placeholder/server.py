from backend_placeholder.api import APP
import uvicorn

def runner(host: str = "0.0.0.0", port: int = 8000) -> None:
  uvicorn.run(APP, host=host, port=port)
