from fastapi import WebSocket, WebSocketDisconnect
import jwt, os

connections: dict [int, WebSocket] = {}

async def websocket_endpoint(websocket: WebSocket, token: str):
    
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        user_id: str = payload.get("sub")
    except:
        await websocket.close(code=1008) 
        return

    await websocket.accept()
    connections[int(user_id)] = websocket

    try:
        while True:
            await websocket.receive_text() 
    except WebSocketDisconnect:
         connections.pop(user_id, None)