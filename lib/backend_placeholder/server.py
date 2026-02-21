from backend_placeholder.api import APP
import uvicorn

def serve(host="0.0.0.0", port=8000):
  uvicorn.run(APP, host=host, port=port)
