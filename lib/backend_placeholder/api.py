from fastapi import FastAPI

APP: FastAPI = FastAPI()

@APP.get("/")
def placeholder():
  return {"placeholder": "placeholder"}
