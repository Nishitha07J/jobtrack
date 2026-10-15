from fastapi import FastAPI

app = FastAPI(title="JobTrack")


@app.get("/health")
def health():
    return {"status": "ok"}