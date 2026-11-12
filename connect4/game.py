#!/usr/bin/env python3
"""
Connect 4 Interactive Game Engine for GitHub Profile README
Supports player moves via GitHub Issues automation and an AI opponent (RamanBot).
"""

import os
import sys
import json
import re
import random
from pathlib import Path

ROWS = 6
COLS = 7
EMPTY = 0
PLAYER = 1  # 🔴
BOT = 2     # 🟡

STATE_FILE = Path(__file__).parent / "state.json"
README_FILE = Path(__file__).parent.parent / "README.md"
REPO_NAME = "raman7072/raman7072"


def get_empty_board():
    return [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]


def get_default_state():
    return {
        "board": get_empty_board(),
        "last_player": "None",
        "last_move": "Game initialized",
        "status": "in_progress",
        "winner": None,
        "moves_count": 0,
        "stats": {
            "player_wins": 0,
            "bot_wins": 0,
            "draws": 0
        }
    }


def load_state():
    if not STATE_FILE.exists():
        state = get_default_state()
        save_state(state)
        return state
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        state = get_default_state()
        save_state(state)
        return state


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def is_valid_column(board, col):
    if not (0 <= col < COLS):
        return False
    return board[0][col] == EMPTY


def get_valid_columns(board):
    return [c for c in range(COLS) if is_valid_column(board, c)]


def drop_piece(board, col, piece):
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == EMPTY:
            board[r][col] = piece
            return r
    return -1


def check_win(board, piece):
    # Check horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            if all(board[r][c + i] == piece for i in range(4)):
                return True

    # Check vertical
    for r in range(ROWS - 3):
        for c in range(COLS):
            if all(board[r + i][c] == piece for i in range(4)):
                return True

    # Check positive diagonal (\)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if all(board[r + i][c + i] == piece for i in range(4)):
                return True

    # Check negative diagonal (/)
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if all(board[r - i][c + i] == piece for i in range(4)):
                return True

    return False


def is_board_full(board):
    return all(board[0][c] != EMPTY for c in range(COLS))


def bot_choose_move(board):
    valid_cols = get_valid_columns(board)
    if not valid_cols:
        return None

    # 1. Check if bot can win in one move
    for col in valid_cols:
        temp_board = [row[:] for row in board]
        drop_piece(temp_board, col, BOT)
        if check_win(temp_board, BOT):
            return col

    # 2. Check if player can win in one move, and block them
    for col in valid_cols:
        temp_board = [row[:] for row in board]
        drop_piece(temp_board, col, PLAYER)
        if check_win(temp_board, PLAYER):
            return col

    # 3. Prefer non-blunder moves (don't give opponent an immediate win above)
    safe_cols = []
    for col in valid_cols:
        temp_board = [row[:] for row in board]
        r = drop_piece(temp_board, col, BOT)
        # If opponent drops on top of this, do they win?
        if r > 0:
            temp_board[r - 1][col] = PLAYER
            if check_win(temp_board, PLAYER):
                continue
        safe_cols.append(col)

    candidates = safe_cols if safe_cols else valid_cols

    # 4. Prefer center columns: [3, 2, 4, 1, 5, 0, 6]
    center_order = [3, 2, 4, 1, 5, 0, 6]
    for pref in center_order:
        if pref in candidates:
            return pref

    return random.choice(candidates)


def render_markdown(state):
    board = state["board"]
    status = state["status"]
    last_player = state.get("last_player", "None")
    last_move = state.get("last_move", "Game in progress")
    stats = state.get("stats", {"player_wins": 0, "bot_wins": 0, "draws": 0})

    piece_symbols = {
        EMPTY: "⚪",
        PLAYER: "🔴",
        BOT: "🟡"
    }

    # Render Board
    lines = []
    lines.append('<div align="center">\n')
    lines.append("### 🔴🟡 Interactive Connect-4: Community vs RamanBot\n")
    lines.append("> **How to Play:** Click any column button below the board to drop your disc! A GitHub Action will execute your move and trigger RamanBot's counterplay.\n")
    lines.append("| 1 | 2 | 3 | 4 | 5 | 6 | 7 |")
    lines.append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    for r in range(ROWS):
        row_str = " | ".join(piece_symbols[board[r][c]] for c in range(COLS))
        lines.append(f"| {row_str} |")

    # Column drop buttons or game over state
    if status == "in_progress":
        drop_buttons = []
        for c in range(COLS):
            if is_valid_column(board, c):
                issue_title = f"connect4|drop|{c+1}"
                issue_body = f"Click+'Submit+new+issue'+to+drop+a+🔴+disc+into+Column+{c+1}!"
                url = f"https://github.com/{REPO_NAME}/issues/new?title={issue_title}&body={issue_body}"
                drop_buttons.append(f"[`⬇️ Drop`]({url})")
            else:
                drop_buttons.append("⛔")
        lines.append(f"| {' | '.join(drop_buttons)} |")
    else:
        lines.append("| 🏁 | 🏁 | 🏁 | GAME OVER | 🏁 | 🏁 | 🏁 |")

    lines.append("\n<br/>\n")

    # Status badge & Last move info
    if status == "player_won":
        status_banner = "🎉 **Result:** The Community (🔴) WON! Congratulations!"
    elif status == "bot_won":
        status_banner = "🤖 **Result:** RamanBot (🟡) won this round! Better luck next time!"
    elif status == "draw":
        status_banner = "🤝 **Result:** It's a DRAW! The board is full!"
    else:
        status_banner = "⚔️ **Status:** Your Turn! Pick an available column above."

    lines.append(f"{status_banner}\n")
    lines.append(f"**Last Action:** {last_move}  \n")
    lines.append(f"**Scoreboard:** 🔴 Community Wins: `{stats.get('player_wins', 0)}` | 🟡 RamanBot Wins: `{stats.get('bot_wins', 0)}` | 🤝 Draws: `{stats.get('draws', 0)}`  \n")

    reset_url = f"https://github.com/{REPO_NAME}/issues/new?title=connect4%7Creset&body=Click+'Submit+new+issue'+to+start+a+fresh+game!"
    lines.append(f"\n[`🔄 Start New Game / Reset Board`]({reset_url})\n")
    lines.append("</div>\n")

    return "\n".join(lines)


def update_readme(markdown_content):
    if not README_FILE.exists():
        print(f"Error: {README_FILE} not found.")
        return False

    with open(README_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    start_tag = "<!-- CONNECT4_START -->"
    end_tag = "<!-- CONNECT4_END -->"

    pattern = re.compile(f"{re.escape(start_tag)}.*?{re.escape(end_tag)}", re.DOTALL)
    replacement = f"{start_tag}\n{markdown_content}\n{end_tag}"

    if pattern.search(content):
        new_content = pattern.sub(replacement, content)
    else:
        # Append before footer or at the end
        new_content = content + f"\n\n{replacement}\n"

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)

    return True


def handle_move(command, user="Anonymous"):
    state = load_state()
    command = command.strip()

    # Reset command
    if command.lower() == "connect4|reset":
        stats = state.get("stats", {"player_wins": 0, "bot_wins": 0, "draws": 0})
        state = get_default_state()
        state["stats"] = stats
        state["last_move"] = f"Game was restarted by @{user}"
        save_state(state)
        md = render_markdown(state)
        update_readme(md)
        return f"Game board has been reset by @{user}! Ready for a new round."

    match = re.match(r"^connect4\|drop\|([1-7])$", command, re.IGNORECASE)
    if not match:
        return f"Invalid command: `{command}`. Must match `connect4|drop|[1-7]` or `connect4|reset`."

    col = int(match.group(1)) - 1  # 0-indexed

    # Check if game is already over
    if state["status"] != "in_progress":
        return f"This game is already over ({state['status']}). Click 'Start New Game' to play again!"

    board = state["board"]

    if not is_valid_column(board, col):
        return f"Column {col + 1} is already full! Please pick another column."

    # 1. Player move
    drop_piece(board, col, PLAYER)
    state["moves_count"] = state.get("moves_count", 0) + 1
    state["last_player"] = user

    # Check if player won
    if check_win(board, PLAYER):
        state["status"] = "player_won"
        state["winner"] = "player"
        state["last_move"] = f"🏆 @{user} dropped in Col {col + 1} and WON the game!"
        state["stats"]["player_wins"] += 1
        save_state(state)
        md = render_markdown(state)
        update_readme(md)
        return f"Incredible move, @{user}! You connected 4 and won the game! 🏆"

    # Check for draw
    if is_board_full(board):
        state["status"] = "draw"
        state["winner"] = "draw"
        state["last_move"] = f"Board full after move in Col {col + 1} by @{user}"
        state["stats"]["draws"] += 1
        save_state(state)
        md = render_markdown(state)
        update_readme(md)
        return "It's a draw! The board is completely filled. 🤝"

    # 2. Bot counter-move
    bot_col = bot_choose_move(board)
    if bot_col is not None:
        drop_piece(board, bot_col, BOT)
        state["moves_count"] += 1

        if check_win(board, BOT):
            state["status"] = "bot_won"
            state["winner"] = "bot"
            state["last_move"] = f"@{user} played Col {col + 1}; RamanBot counter-dropped in Col {bot_col + 1} and won!"
            state["stats"]["bot_wins"] += 1
            save_state(state)
            md = render_markdown(state)
            update_readme(md)
            return f"@{user} dropped in Col {col + 1}. RamanBot played Col {bot_col + 1} and won the round! 🤖"

        if is_board_full(board):
            state["status"] = "draw"
            state["winner"] = "draw"
            state["last_move"] = f"Board filled after RamanBot played Col {bot_col + 1}"
            state["stats"]["draws"] += 1
            save_state(state)
            md = render_markdown(state)
            update_readme(md)
            return f"@{user} dropped in Col {col + 1}. RamanBot played Col {bot_col + 1}. It's a draw! 🤝"

        state["last_move"] = f"@{user} dropped in Col {col + 1} • RamanBot countered in Col {bot_col + 1}"
    else:
        state["last_move"] = f"@{user} dropped in Col {col + 1}"

    save_state(state)
    md = render_markdown(state)
    update_readme(md)
    return f"Move registered: @{user} dropped in Col {col + 1}. RamanBot answered in Col {bot_col + 1 if bot_col is not None else 'N/A'}. Your turn!"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Connect-4 Game Runner")
    parser.add_argument("--command", type=str, default="connect4|render", help="Command (e.g. connect4|drop|3 or connect4|reset or connect4|render)")
    parser.add_argument("--user", type=str, default="Anonymous", help="GitHub username of the player")
    args = parser.parse_args()

    if args.command == "connect4|render":
        s = load_state()
        md = render_markdown(s)
        update_readme(md)
        print("Rendered current board to README.")
    else:
        msg = handle_move(args.command, args.user)
        print(msg)

