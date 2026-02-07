from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import auth_route, execute_route, llm_route, stt_route, tts_route

app = FastAPI(title="Voice Assistant Local API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stt_route.router, prefix="/stt")
app.include_router(llm_route.router, prefix="/llm")
app.include_router(execute_route.router, prefix="/execute")
app.include_router(tts_route.router, prefix="/tts")
app.include_router(auth_route.router, prefix="/auth")  # optional

@app.get("/health")
def health():
    return {"status":"ok"}
