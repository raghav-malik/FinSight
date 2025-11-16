"""
FinSight FastAPI WebSocket Server
Connects the frontend to the LangChain agent backend
"""

import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Import the pre-configured agent from agent_runner
from app.agent_runner import agent_executor, api_key

# Initialize FastAPI app
app = FastAPI(title="FinSight API")

# Store conversation history per connection
conversations = {}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time agent communication"""
    await websocket.accept()
    print("✅ WebSocket client connected")
    
    # Initialize conversation history for this connection
    connection_id = id(websocket)
    conversations[connection_id] = []
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get('type')
            content = message_data.get('content', '')
            
            print(f"📩 Received: {message_type} - {content[:50]}...")
            
            if message_type == 'clear':
                # Clear conversation history
                conversations[connection_id] = []
                await websocket.send_json({
                    'type': 'system',
                    'content': 'Chat history cleared'
                })
                continue
            
            if message_type == 'message':
                # Add user message to history
                conversations[connection_id].append({
                    'role': 'user',
                    'content': content
                })
                
                # LIMIT HISTORY: Keep only last 6 messages (3 exchanges)
                # This prevents token overflow with large CSV data
                if len(conversations[connection_id]) > 6:
                    conversations[connection_id] = conversations[connection_id][-6:]
                
                # Send thinking indicator
                await websocket.send_json({
                    'type': 'thinking',
                    'content': ''
                })
                
                try:
                    # Run agent with conversation history
                    response_content = ""
                    
                    # Stream agent response
                    async for step in agent_executor.astream(
                        {"messages": conversations[connection_id]},
                        stream_mode="values"
                    ):
                        # Get the last message
                        last_msg = step["messages"][-1]
                        
                        # Only send final AI response (not tool calls)
                        if (hasattr(last_msg, 'type') and 
                            last_msg.type == "ai" and 
                            not (hasattr(last_msg, 'tool_calls') and last_msg.tool_calls)):
                            
                            response_content = last_msg.content
                    
                    # Add assistant response to history
                    if response_content:
                        conversations[connection_id].append({
                            'role': 'assistant',
                            'content': response_content
                        })
                        
                        # Send response to client
                        await websocket.send_json({
                            'type': 'message',
                            'content': response_content
                        })
                        print(f"📤 Sent response: {response_content[:100]}...")
                    else:
                        await websocket.send_json({
                            'type': 'error',
                            'content': 'No response generated from agent'
                        })
                
                except Exception as e:
                    error_msg = f"Agent error: {str(e)}"
                    print(f"❌ {error_msg}")
                    await websocket.send_json({
                        'type': 'error',
                        'content': error_msg
                    })
    
    except WebSocketDisconnect:
        print("🔌 WebSocket client disconnected")
        # Clean up conversation history
        if connection_id in conversations:
            del conversations[connection_id]
    
    except Exception as e:
        print(f"❌ WebSocket error: {str(e)}")
        if connection_id in conversations:
            del conversations[connection_id]


# Serve static files (frontend)
app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")
app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")


@app.get("/")
async def read_root():
    """Serve the main HTML page"""
    return FileResponse("frontend/index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agent": "ready"}


if __name__ == "__main__":
    import uvicorn
    import os
    
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not found in .env file")
        exit(1)
    
    # Get port from environment (Render sets this automatically)
    port = int(os.getenv("PORT", 8000))
    
    print("🚀 Starting FinSight server...")
    print(f"🌐 Port: {port}")
    print("📁 Serving frontend from: frontend/")
    print("🔧 Agent imported from: app.agent_runner")
    
    uvicorn.run(
        app,
        host="0.0.0.0",  # Important: 0.0.0.0 allows external connections
        port=port,
        log_level="info"
    )