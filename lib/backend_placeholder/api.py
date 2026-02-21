from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

APP: FastAPI = FastAPI()

# Allow React frontend to talk to this API
APP.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_methods=["*"],
  allow_headers=["*"]
)

@APP.get("/")
def placeholder() -> dict[str, str]:
  return {"placeholder": "placeholder"}
