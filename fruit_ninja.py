import pygame
import cv2
import mediapipe as mp
import random
import os
import sys

pygame.init()

# Window setup
WIDTH, HEIGHT = 800, 800
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fruit Ninja Hand Edition")
font = pygame.font.SysFont("comicsans", 30)
clock = pygame.time.Clock()

# Load images and sounds
FRUIT_IMAGES = ['apple.png', 'banana.png', 'orange.png', 'pineapple.png']
BOMB_IMAGE = 'bomb.png'

def load_image(name, size=(60, 60)):
    img = pygame.image.load(os.path.join('assets', name))
    return pygame.transform.scale(img, size)

fruits_img = [load_image(f) for f in FRUIT_IMAGES]
bomb_img = load_image(BOMB_IMAGE, size=(50, 50))

slice_sound = pygame.mixer.Sound(os.path.join('assets', 'slice.mp3'))
bomb_sound = pygame.mixer.Sound(os.path.join('assets', 'bomb.wav'))

# Buttons
start_button = pygame.Rect(WIDTH//2 - 50, HEIGHT//2 - 25, 100, 50)
end_button = pygame.Rect(WIDTH - 90, 20, 70, 30)

# Mediapipe hand detector setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)

# Initialize webcam
cap = cv2.VideoCapture(0)

# Previous fingertip position
prev_hand_pos = None

# Finger index
INDEX_TIP_ID = 8

# Fruit class
class Fruit:
    def __init__(self):
        self.x = random.randint(50, WIDTH - 50)
        self.y = -100
        self.speed = random.randint(4, 8)
        self.image = random.choice(fruits_img + [bomb_img])
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.is_bomb = self.image == bomb_img

    def move(self):
        self.y += self.speed
        self.rect.center = (self.x, self.y)

    def draw(self):
        screen.blit(self.image, self.rect)

# Drawing buttons
def draw_start_button():
    pygame.draw.rect(screen, (0, 200, 0), start_button)
    screen.blit(font.render("Start", True, (255, 255, 255)), (start_button.x + 20, start_button.y + 10))

def draw_end_button():
    pygame.draw.rect(screen, (200, 0, 0), end_button)
    screen.blit(font.render("End", True, (255, 255, 255)), (end_button.x + 10, end_button.y + 5))

# Hand tracking
def detect_hand():
    global prev_hand_pos
    ret, frame = cap.read()
    if not ret:
        return None

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    hand_pos = None
    if result.multi_hand_landmarks:
        hand_landmarks = result.multi_hand_landmarks[0]

        # Draw landmarks directly on screen via pygame
        for lm in hand_landmarks.landmark:
            x_px = int(lm.x * WIDTH)
            y_px = int(lm.y * HEIGHT)
            pygame.draw.circle(screen, (255, 0, 0), (x_px, y_px), 4)

        # Track fingertip (landmark 8)
        x_game = int(hand_landmarks.landmark[8].x * WIDTH)
        y_game = int(hand_landmarks.landmark[8].y * HEIGHT)

        # Smooth motion
        if prev_hand_pos:
            x_game = int(0.6 * prev_hand_pos[0] + 0.4 * x_game)
            y_game = int(0.6 * prev_hand_pos[1] + 0.4 * y_game)

        hand_pos = (x_game, y_game)
        prev_hand_pos = hand_pos

    return hand_pos

# Main game loop
def main():
    fruits = []
    score = 0
    lives = 3
    playing = False
    spawn_timer = 0

    while True:
        screen.fill((30, 30, 30))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                cap.release()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not playing and start_button.collidepoint(event.pos):
                    playing = True
                    score = 0
                    lives = 3
                    fruits.clear()
                elif playing and end_button.collidepoint(event.pos):
                    pygame.quit()
                    cap.release()
                    sys.exit()

        if playing:
            draw_end_button()

            # Fruit spawning
            spawn_timer += 1
            if spawn_timer > 30:
                fruits.append(Fruit())
                spawn_timer = 0

            hand_pos = detect_hand()
            if hand_pos:
                pygame.draw.circle(screen, (0, 255, 0), hand_pos, 10)

            # Fruit movement and collision
            for fruit in fruits[:]:
                fruit.move()
                fruit.draw()
                if hand_pos and fruit.rect.collidepoint(hand_pos):
                    if fruit.is_bomb:
                        bomb_sound.play()
                        lives -= 1
                    else:
                        slice_sound.play()
                        score += 1
                    fruits.remove(fruit)
                elif fruit.y > HEIGHT + 50:
                    fruits.remove(fruit)
                    if not fruit.is_bomb:
                        lives -= 1

            # Score and lives display
            screen.blit(font.render(f"Score: {score}", True, (255, 255, 255)), (20, 20))
            screen.blit(font.render(f"Lives: {lives}", True, (255, 100, 100)), (20, 60))

            # Game over
            if lives <= 0:
                playing = False
                screen.blit(font.render("Game Over! Click Start to Retry.", True, (255, 255, 255)), (WIDTH // 2 - 180, HEIGHT // 2))

        else:
            draw_start_button()

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
    cap.release()
    cv2.destroyAllWindows()
