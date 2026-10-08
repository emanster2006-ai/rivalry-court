from fastapi import FastAPI

app = FastAPI(title="Rivalry Court API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
