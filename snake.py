import random
import curses
import asyncio
from fastapi import FastAPI, WebSocket

app = FastAPI()

# Dictionary to store WebSocket connections for each client
connections = {}

def game_loop():
    """
    Main game loop that handles the Snake game logic.
    """
    try:
        stdscr = curses.initscr()
        curses.curs_set(0)
        sh, sw = stdscr.getmaxyx()
        w = stdscr.subwin(sh, sw, 0, 0)
        w.keypad(1)
        w.timeout(100)

        snake_x = sw // 4
        snake_y = sh // 2
        snake = [
            [snake_y, snake_x],
            [snake_y, snake_x - 1],
            [snake_y, snake_x - 2]
        ]

        food = [sh // 2, sw // 2]
        w.addch(food[0], food[1], curses.ACS_PI)

        key = curses.KEY_RIGHT

        while True:
            next_key = w.getch()
            key = key if next_key == -1 else next_key

            new_head = [snake[0][0], snake[0][1]]

            if key == curses.KEY_DOWN:
                new_head[0] += 1
            if key == curses.KEY_UP:
                new_head[0] -= 1
            if key == curses.KEY_LEFT:
                new_head[1] -= 1
            if key == curses.KEY_RIGHT:
                new_head[1] += 1

            snake.insert(0, new_head)

            if snake[0] == food:
                food = None
                while food is None:
                    nf = [
                        random.randint(1, sh - 1),
                        random.randint(1, sw - 1)
                    ]
                    food = nf if nf not in snake else None
                w.addch(food[0], food[1], curses.ACS_PI)
            else:
                tail = snake.pop()
                w.addch(tail[0], tail[1], ' ')

            w.addch(snake[0][0], snake[0][1], curses.ACS_CKBOARD)

            # Send game state to all connected clients
            for connection in connections.values():
                asyncio.create_task(connection.send_text(f"{snake[0][1]},{snake[0][0]},{food[1]},{food[0]}"))

    finally:
        curses.endwin()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    """
    WebSocket endpoint for handling client connections.
    """
    await websocket.accept()
    connections[client_id] = websocket

    try:
        await websocket.receive_text()
    except WebSocketDisconnect:
        del connections[client_id]

if __name__ == "__main__":
    asyncio.create_task(game_loop())
