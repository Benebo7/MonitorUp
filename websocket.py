from fastapi import WebSocket, WebSocketDisconnect
import jwt, os, json
import redis.asyncio as aioredis

connections: dict[str, WebSocket] = {}

async def websocket_endpoint(websocket: WebSocket, token: str):

    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        user_id: str = payload.get("sub")
    except Exception:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    connections[user_id] = websocket

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
         connections.pop(user_id, None)


async def redis_subscriber():
    r = aioredis.from_url(os.getenv("REDIS_URL"))
    pubsub = r.pubsub()
    await pubsub.subscribe("monitor_updates")
    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        data = json.loads(message["data"])
        user_id = data.get("user_id")
        if user_id in connections:
            try:
                await connections[user_id].send_json(data)
            except Exception:
                connections.pop(user_id, None)