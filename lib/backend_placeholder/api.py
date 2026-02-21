from fastapi import FastAPI

APP: FastAPI = FastAPI()

@APP.get("/")
def placeholder() -> dict[str, str]:
  return {"placeholder": "placeholder"}
