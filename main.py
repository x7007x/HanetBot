from fastapi import FastAPI, Request, HTTPException, Response
import redis
import json

r = redis.from_url(
    'redis://default:LszSeLOwYQd6A6nGeinRuY0TrJlRR9nx@redis-17683.c263.us-east-1-2.ec2.redns.redis-cloud.com:17683'
)
app = FastAPI()

@app.get("/ping")
async def ping():
    return {"status": "ok"}

@app.post("/save_data")
async def save_data(request: Request):
    json_data = await request.json()
    try:
        r.set("bot_data", json.dumps(json_data))
        return {"status": "success", "message": "Data saved to Redis"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving data: {e}")

@app.get("/get_data")
async def get_data():
    raw = r.get("bot_data")
    if not raw:
        raise HTTPException(status_code=404, detail="No data found in Redis")
    data = json.loads(raw)
    return data
