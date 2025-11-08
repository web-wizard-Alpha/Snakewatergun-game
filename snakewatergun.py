import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import random, os, json, time
from collections import Counter
import pygame
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# ---------------- PATH SETUP ----------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(SCRIPT_DIR, "icons")
MEMORY_FILE = os.path.join(SCRIPT_DIR, "ai_memory.json")

# ---------------- SOUND SETUP ----------------
pygame_audio_available = False
try:
    pygame.mixer.init()
    pygame_audio_available = True
except Exception:
    pygame_audio_available = False

SOUND_CLICK = os.path.join(SCRIPT_DIR, "click.wav")
SOUND_WIN = os.path.join(SCRIPT_DIR, "win.wav")
SOUND_LOSE = os.path.join(SCRIPT_DIR, "lose.wav")
SOUND_DRAW = os.path.join(SCRIPT_DIR, "draw.wav")

def play_sound(path):
    """Play a sound if available."""
    try:
        if pygame_audio_available and os.path.exists(path):
            pygame.mixer.Sound(path).play()
    except Exception:
        pass

# ---------------- GAME SETUP ----------------
MOVES = ["Snake", "Water", "Gun"]
BEATS = {"Snake": "Water", "Water": "Gun", "Gun": "Snake"}

# Load AI memory
if os.path.exists(MEMORY_FILE):
    try:
        with open(MEMORY_FILE, "r") as f:
            ai_memory = json.load(f)
    except Exception:
        ai_memory = {"user_moves": [], "ai_confidence": 0.5, "confidence_history": []}
else:
    ai_memory = {"user_moves": [], "ai_confidence": 0.5, "confidence_history": []}

user_history = ai_memory.get("user_moves", [])
ai_confidence = ai_memory.get("ai_confidence", 0.5)
confidence_history = ai_memory.get("confidence_history", [])

user_score = 0
ai_score = 0
draws = 0
mode = "AI"

# ---------------- CREATE PLACEHOLDER ICONS ----------------
def create_placeholder_icon(path, letter, color):
    img = Image.new("RGB", (70, 70), color)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except:
        font = ImageFont.load_default()
    
    # ✅ Use getbbox() instead of textsize()
    bbox = font.getbbox(letter)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    draw.text(((70 - w) / 2, (70 - h) / 2), letter, fill="white", font=font)
    img.save(path)

# ---------------- LOAD ICON SAFELY ----------------
def load_icon(filename, fallback_color):
    path = os.path.join(ICONS_DIR, filename)
    if not os.path.exists(path):
        os.makedirs(ICONS_DIR, exist_ok=True)
        create_placeholder_icon(path, filename[0].upper(), fallback_color)
    try:
        return Image.open(path).convert("RGBA")
    except:
        img = Image.new("RGBA", (70, 70), fallback_color)
        return img

# ---------------- ROOT WINDOW ----------------
root = tk.Tk()
root.title("🐍💧🔫 Snake–Water–Gun Intelligent AI Game")
root.geometry("850x650")
root.configure(bg="#1E1E1E")
root.resizable(False, False)

style = ttk.Style()
style.configure("TButton", font=("Helvetica", 12, "bold"), padding=8)
style.configure("TLabel", background="#1E1E1E", foreground="white", font=("Helvetica", 11))

# ---------------- AI LOGIC ----------------
def ai_move():
    global ai_confidence
    if not user_history:
        return random.choice(MOVES)
    counter = Counter(user_history)
    most_common = counter.most_common(1)[0][0]
    predicted = BEATS.get(most_common, random.choice(MOVES))
    confidence = min(1.0, 0.5 + len(user_history) / 20)
    ai_confidence = (ai_confidence * 0.7) + (confidence * 0.3)
    confidence_history.append(ai_confidence)
    update_confidence_visuals()
    return predicted if random.random() < ai_confidence else random.choice(MOVES)

def determine_winner(p1, p2):
    if p1 == p2:
        play_sound(SOUND_DRAW)
        return "Draw"
    elif BEATS[p1] == p2:
        play_sound(SOUND_WIN)
        return "Player 1"
    else:
        play_sound(SOUND_LOSE)
        return "Player 2"

def save_memory():
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump({
                "user_moves": user_history[-200:],
                "ai_confidence": ai_confidence,
                "confidence_history": confidence_history[-200:]
            }, f)
    except:
        pass

# ---------------- TRAINING MODE ----------------
training_running = False

def train_ai(rounds=200):
    global training_running
    training_running = True
    result_label_var.set("🤖 Training AI… Please wait…")
    root.update()

    for _ in range(rounds):
        if not training_running:
            break
        p1 = random.choice(MOVES)
        p2 = ai_move()
        determine_winner(p1, p2)
        user_history.append(p1)
        if len(user_history) > 100:
            user_history.pop(0)
        time.sleep(0.01)
        root.update()

    training_running = False
    result_label_var.set("✅ AI Training Complete! Ready to Play.")
    save_memory()

def stop_training():
    global training_running
    training_running = False
    result_label_var.set("🛑 Training stopped.")
    root.update()

# ---------------- GRAPH ----------------
fig = Figure(figsize=(4, 2), facecolor="#1E1E1E")
ax = fig.add_subplot(111)
ax.set_facecolor("#2E2E2E")
ax.tick_params(colors="white")
ax.set_title("AI Confidence Over Time", color="white")
ax.set_ylim(0, 1)

canvas_fig = FigureCanvasTkAgg(fig, master=root)
canvas_fig.get_tk_widget().place(x=420, y=370)

def update_confidence_visuals():
    ax.clear()
    ax.set_facecolor("#2E2E2E")
    ax.tick_params(colors="white")
    ax.set_title("AI Confidence Over Time", color="white")
    ax.set_ylim(0, 1)
    if confidence_history:
        ax.plot(confidence_history[-50:], color="#00FFAB", linewidth=2)
    canvas_fig.draw()
    bar_length = int(ai_confidence * 200)
    confidence_canvas.delete("all")
    confidence_canvas.create_rectangle(0, 0, bar_length, 20, fill="#00FFAB", width=0)
    confidence_canvas.create_text(100, 10, text=f"{int(ai_confidence*100)}%", fill="black", font=("Helvetica", 10, "bold"))

# ---------------- ANIMATION ----------------
def animate_icon(label, pil_image):
    for size in range(60, 81, 4):
        frame = pil_image.resize((size, size))
        frame = ImageTk.PhotoImage(frame)
        label.config(image=frame)
        label.image = frame
        root.update()
        time.sleep(0.015)

# ---------------- GAMEPLAY ----------------
player1_choice = None

def play_game(choice):
    global user_score, ai_score, draws, player1_choice
    play_sound(SOUND_CLICK)

    if mode == "AI":
        user_choice = choice
        ai_choice = ai_move()
        result = determine_winner(user_choice, ai_choice)
        user_history.append(user_choice)
        if len(user_history) > 50:
            user_history.pop(0)

        if result == "Player 1":
            user_score += 1
            result_text = "🎉 You Win!"
        elif result == "Player 2":
            ai_score += 1
            result_text = "🤖 AI Wins!"
        else:
            draws += 1
            result_text = "It's a Draw!"

        ai_label_var.set(f"AI Move: {ai_choice}")
        animate_icon(ai_icon_label, icons_map[ai_choice])

    else:
        if player1_choice is None:
            player1_choice = choice
            result_label_var.set("Player 1 has chosen... Waiting for Player 2")
            return
        else:
            p2_choice = choice
            result = determine_winner(player1_choice, p2_choice)
            if result == "Player 1":
                user_score += 1
                result_text = "Player 1 Wins!"
            elif result == "Player 2":
                ai_score += 1
                result_text = "Player 2 Wins!"
            else:
                draws += 1
                result_text = "It's a Draw!"
            player1_choice = None
            ai_label_var.set(f"P2 Move: {p2_choice}")

    result_label_var.set(result_text)
    score_label_var.set(f"Score → P1: {user_score} | P2/AI: {ai_score} | Draws: {draws}")
    save_memory()
    update_confidence_visuals()

# ---------------- MODE SELECTION ----------------
def set_mode(selected_mode):
    global mode, user_score, ai_score, draws, player1_choice
    mode = selected_mode
    user_score = ai_score = draws = 0
    player1_choice = None
    user_label_var.set("Your Move: -")
    ai_label_var.set("Opponent Move: -")
    result_label_var.set(f"Mode set to {mode}")
    score_label_var.set("Score → P1: 0 | P2/AI: 0 | Draws: 0")
    play_sound(SOUND_CLICK)

# ---------------- GUI COMPONENTS ----------------
tk.Label(root, text="🐍 Snake 💧 Water 🔫 Gun", font=("Helvetica", 22, "bold"), bg="#1E1E1E", fg="#FFD369").pack(pady=15)

mode_frame = tk.Frame(root, bg="#1E1E1E")
mode_frame.pack(pady=10)
ttk.Button(mode_frame, text="Play vs AI", command=lambda: set_mode("AI")).grid(row=0, column=0, padx=10)
ttk.Button(mode_frame, text="Play vs Player", command=lambda: set_mode("Player")).grid(row=0, column=1, padx=10)
ttk.Button(mode_frame, text="Train AI 🤖", command=lambda: train_ai(200)).grid(row=0, column=2, padx=10)
ttk.Button(mode_frame, text="Stop Training", command=stop_training).grid(row=0, column=3, padx=10)

frame = tk.Frame(root, bg="#1E1E1E")
frame.pack(pady=20)

# Load all icons from "icons" folder
icons_map = {}
for move, color in zip(MOVES, [(0,150,0), (0,100,255), (200,0,0)]):
    filename = f"{move.lower()}.png"
    pil_img = load_icon(filename, color)
    icons_map[move] = pil_img
    tk_img = ImageTk.PhotoImage(pil_img.resize((70, 70)))
    btn = ttk.Button(frame, text=move, image=tk_img, compound="top", command=lambda m=move: play_game(m))
    btn.image = tk_img
    btn.grid(row=0, column=MOVES.index(move), padx=15)

user_label_var = tk.StringVar(value="Your Move: -")
ai_label_var = tk.StringVar(value="Opponent Move: -")
result_label_var = tk.StringVar(value="Result: -")
score_label_var = tk.StringVar(value="Score → P1: 0 | P2/AI: 0 | Draws: 0")

for var in [user_label_var, ai_label_var, result_label_var, score_label_var]:
    ttk.Label(root, textvariable=var).pack(pady=3)

confidence_canvas = tk.Canvas(root, width=200, height=20, bg="white", highlightthickness=0)
confidence_canvas.pack(pady=10)
ai_icon_label = tk.Label(root, bg="#1E1E1E")
ai_icon_label.pack(pady=10)

update_confidence_visuals()

root.mainloop()



