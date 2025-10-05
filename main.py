import os
from typing import List, Optional, Literal

from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel
import httpx
from starlette.staticfiles import StaticFiles


# ---------- Config ----------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro-latest")
ALLOWED_IPS = {ip.strip() for ip in os.getenv("ALLOWED_IPS", "127.0.0.1,::1").split(",") if ip.strip()}


# ---------- Schemas ----------
class InlineData(BaseModel):
    mime_type: str
    data: str


class Part(BaseModel):
    text: Optional[str] = None
    inline_data: Optional[InlineData] = None


class Content(BaseModel):
    role: Literal["user", "model"]
    parts: List[Part]


class ChatRequest(BaseModel):
    model: Optional[str] = None
    systemInstruction: Optional[str] = None
    temperature: Optional[float] = 1.0
    maxOutputTokens: Optional[int] = 2048
    contents: List[Content]


class ChatResponse(BaseModel):
    text: str


# ---------- App ----------
app = FastAPI(title="Gemini Proxy", version="1.0.0")


def client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # Use first hop
        return xff.split(",")[0].strip()
    return request.client.host if request.client else ""


def enforce_ip_allowlist(request: Request):
    ip = client_ip(request)
    # Always allow empty (shouldn't happen), and localhost variants by default
    allowed = ALLOWED_IPS or {"127.0.0.1", "::1"}
    if ip not in allowed:
        raise HTTPException(status_code=403, detail=f"IP no permitida: {ip}")


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request, _: None = Depends(enforce_ip_allowlist)):
    api_key = GEMINI_API_KEY
    if not api_key:
        raise HTTPException(status_code=500, detail="Falta GEMINI_API_KEY en variables de entorno")

    model = req.model or DEFAULT_MODEL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    # Build payload according to API spec
    payload = {
        "systemInstruction": {"role": "system", "parts": [{"text": req.systemInstruction}]} if req.systemInstruction else None,
        "contents": [c.model_dump() for c in req.contents],
        "generationConfig": {
            "temperature": req.temperature if req.temperature is not None else 1.0,
            "maxOutputTokens": req.maxOutputTokens if req.maxOutputTokens is not None else 2048,
        },
        # Use valid categories (v1beta)
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_CIVIC_INTEGRITY", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ],
    }

    # Remove None keys
    payload = {k: v for k, v in payload.items() if v is not None}

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            r = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        data = r.json()
        cand = (data.get("candidates") or [None])[0]
        if not cand:
            raise HTTPException(status_code=502, detail="Respuesta vacía del modelo")
        if cand.get("finishReason") == "SAFETY":
            raise HTTPException(status_code=400, detail="Bloqueado por seguridad del modelo")
        parts = (cand.get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts)
        return ChatResponse(text=text or "(sin contenido)")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Error de red hacia Gemini: {e}")


# Mount static last so API routes take precedence
app.mount("/", StaticFiles(directory=".", html=True), name="static")

