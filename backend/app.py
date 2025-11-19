import os
import json
import time
from urllib.parse import urlencode

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
import httpx
from dotenv import load_dotenv

load_dotenv()  # loads .env

GOOGLE_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
PORT = int(os.getenv("PORT", 5000))
RATE_LIMIT = os.getenv("RATE_LIMIT", "60/minute")
CACHE_TIMEOUT = int(os.getenv("CACHE_TIMEOUT_SECS", 300))

if not GOOGLE_KEY:
    raise RuntimeError("Missing GOOGLE_MAPS_API_KEY in env")

app = Flask(__name__)
CORS(app)  # allow frontend (adjust in prod to specific origins)
limiter = Limiter(app, key_func=get_remote_address, default_limits=[RATE_LIMIT])
cache = Cache(app, config={"CACHE_TYPE": "SimpleCache"})

# ---------- Helper: call Ollama ----------
async def call_ollama_async(prompt: str, model: str = "llama3"):
    """
    Call local Ollama. Adjust payload to the Ollama API on your system.
    We use httpx AsyncClient for robustness.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(OLLAMA_URL, json=payload)
        r.raise_for_status()
        j = r.json()
        # Ollama response shape may vary; common field: "response" or "text"
        if "response" in j:
            return j["response"]
        if "text" in j:
            return j["text"]
        if "choices" in j and len(j["choices"]) > 0:
            return j["choices"][0].get("text", "")
        return json.dumps(j)

def call_ollama(prompt: str, model: str = "llama3"):
    # sync wrapper
    import asyncio
    return asyncio.run(call_ollama_async(prompt, model))

# ---------- Utilities ----------
def build_embed_src_by_place(place_id: str):
    base = "https://www.google.com/maps/embed/v1/place"
    params = {"key": GOOGLE_KEY, "q": f"place_id:{place_id}"}
    return f"{base}?{urlencode(params)}"

def build_directions_url(lat: float, lng: float):
    params = {"api": "1", "destination": f"{lat},{lng}", "travelmode": "driving"}
    return "https://www.google.com/maps/dir/?" + urlencode(params)

# ---------- Endpoints ----------
@app.route("/api/llm", methods=["POST"])
@limiter.limit("30/minute")
def llm_endpoint():
    """
    Body: { prompt: "..." }
    Returns: { text: "..." }
    """
    data = request.get_json() or {}
    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"error": "missing prompt"}), 400
    try:
        text = call_ollama(prompt)
        return jsonify({"text": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/search", methods=["POST"])
@limiter.limit("100/minute")
def search_places():
    """
    Body: { query: "...", location: "lat,lng" (optional), limit: int (optional) }
    Uses Google Places Text Search endpoint (server side) to protect API key.
    Caches results for CACHE_TIMEOUT seconds.
    """
    data = request.get_json() or {}
    query = data.get("query")
    if not query:
        return jsonify({"error": "missing query"}), 400
    location = data.get("location")  # optional
    limit = int(data.get("limit", 5))

    cache_key = f"places::{query}::{location}::{limit}"
    cached = cache.get(cache_key)
    if cached:
        return jsonify({"source": "cache", "results": cached})

    # Optionally: refine query via Ollama (shorten / normalize)
    try:
        refine_prompt = f"Normalize this user search to a concise Google Places query: \"{query}\". Output short phrase only."
        refined = call_ollama(refine_prompt)
        refined = (refined or query).strip()
        # Use refined if it looks reasonable; otherwise original query
        if 3 <= len(refined) <= 200:
            use_query = refined
        else:
            use_query = query
    except Exception:
        use_query = query

    # Build Places Text Search request
    params = {"query": use_query, "key": GOOGLE_KEY}
    if location:
        params["query"] = f"{use_query} near {location}"
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    try:
        r = httpx.get(url, params=params, timeout=15)
        r.raise_for_status()
        js = r.json()
        results = js.get("results", [])[:limit]
        out = []
        for r0 in results:
            loc = r0["geometry"]["location"]
            pid = r0.get("place_id")
            out.append({
                "name": r0.get("name"),
                "address": r0.get("formatted_address"),
                "place_id": pid,
                "lat": loc.get("lat"),
                "lng": loc.get("lng"),
                "embed_src": build_embed_src_by_place(pid) if pid else None,
                "directions_url": build_directions_url(loc.get("lat"), loc.get("lng"))
            })
        cache.set(cache_key, out, timeout=CACHE_TIMEOUT)
        return jsonify({"source": "api", "results": out})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": int(time.time())})

if __name__ == "__main__":
    # For local dev
    app.run(host="0.0.0.0", port=PORT, debug=True)
