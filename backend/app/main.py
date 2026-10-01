from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"message": "FPL Forge API is running"}