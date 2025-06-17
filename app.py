# fruit_ninja.py
import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
import os
import random
from PIL import Image
import pygame

import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import cv2
import mediapipe as mp

class HandDetector(VideoTransformerBase):
    def __init__(self):
        self.hands = mp.solutions.hands.Hands()
        self.drawing = mp.solutions.drawing_utils

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        results = self.hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.drawing.draw_landmarks(img, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
        return img

st.title("Fruit Ninja Hand Tracking")

webrtc_streamer(key="example", video_processor_factory=HandDetector)


# Initialize MediaPipe and Pygame
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils
pygame.mixer.init()

# Load assets
asset_path = "assets"
fruit_names = ["apple", "banana", "orange", "pineapple"]
fruit_images = [cv2.imread(os.path.join(asset_path, f"{name}.png"), cv2.IMREAD_UNCHANGED) for name in fruit_names]
bomb_image = cv2.imread(os.path.join(asset_path, "bomb.png"), cv2.IMREAD_UNCHANGED)
slice_sound = pygame.mixer.Sound(os.path.join(asset_path, "slice.mp3"))
bomb_sound = pygame.mixer.Sound(os.path.join(asset_path, "bomb.wav"))

class FallingObject:
    def __init__(self, name, x, y, speed):
        self.name = name
        self.x = x
        self.y = y
        self.speed = speed
        self.size = 80
        self.image = bomb_image if name == "bomb" else fruit_images[fruit_names.index(name)]
        self.image = cv2.resize(self.image, (self.size, self.size))

    def update(self):
        self.y += self.speed

    def draw(self, frame):
        overlay_image_alpha(frame, self.image[:, :, 0:3], (self.x, self.y), self.image[:, :, 3] / 255.0)

def overlay_image_alpha(img, img_overlay, pos, alpha_mask):
    x, y = pos
    h, w = img_overlay.shape[:2]
    if y + h > img.shape[0] or x + w > img.shape[1]:
        return
    img_crop = img[y:y+h, x:x+w]
    img_crop[:] = (alpha_mask[..., None] * img_overlay + (1 - alpha_mask[..., None]) * img_crop)

st.title("Fruit Ninja Hand Edition")
run = st.checkbox("Start Game")

if run:
    cap = cv2.VideoCapture(0)
    score = 0
    lives = 3
    objects = []
    while run:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)
        index_finger = None

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                x = int(hand_landmarks.landmark[8].x * w)
                y = int(hand_landmarks.landmark[8].y * h)
                index_finger = (x, y)
                cv2.circle(frame, index_finger, 10, (0, 255, 0), -1)

        if random.randint(1, 30) == 1:
            name = random.choice(fruit_names + ["bomb"])
            x = random.randint(50, w - 100)
            objects.append(FallingObject(name, x, 0, speed=random.randint(4, 9)))

        for obj in objects[:]:
            obj.update()
            obj.draw(frame)
            if obj.y > h:
                if obj.name != "bomb":
                    lives -= 1
                objects.remove(obj)
            elif index_finger and obj.x < index_finger[0] < obj.x + obj.size and obj.y < index_finger[1] < obj.y + obj.size:
                if obj.name == "bomb":
                    bomb_sound.play()
                    lives -= 1
                else:
                    slice_sound.play()
                    score += 1
                objects.remove(obj)

        cv2.putText(frame, f"Score: {score}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
        cv2.putText(frame, f"Lives: {lives}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (100, 100, 255), 3)

        if lives <= 0:
            cv2.putText(frame, "Game Over", (150, 250), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 5)
            st.image(frame, channels="BGR")
            break

        st.image(frame, channels="BGR")

    cap.release()