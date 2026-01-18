from fastapi import FastAPI
from routes import stt_route, llm_route, execute_route, tts_route, auth_route

app = FastAPI(title="Voice Assistant Local API")

app.include_router(stt_route.router, prefix="/stt")
app.include_router(llm_route.router, prefix="/llm")
app.include_router(execute_route.router, prefix="/execute")
app.include_router(tts_route.router, prefix="/tts")
app.include_router(auth_route.router, prefix="/auth")  # optional

@app.get("/health")
def health():
    return {"status":"ok"}
