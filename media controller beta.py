import cv2
import mediapipe as mp
import pyautogui
import tkinter as tk
from tkinter import ttk
import threading
from PIL import Image, ImageTk


class HandGestureController:
    def __init__(self):
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_hands = mp.solutions.hands
        self.tip_ids = [4, 8, 12, 16, 20]
        self.state = "Stopped"
        self.results = None
        self.cap = None
        self.w_cam, self.h_cam = 640, 480  # Adjusted resolution
        self.start_button_disabled = False
        self.progress_bar = None
        self.canvas = None
        self.after_id = None
        self.img_tk = None

    def finger_position(self, image, hand_no=0):
        lm_list = []
        if self.results.multi_hand_landmarks:
            my_hand = self.results.multi_hand_landmarks[hand_no]
            for id, lm in enumerate(my_hand.landmark):
                h, w, c = image.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lm_list.append([id, cx, cy])
        return lm_list

    def process_video(self):
        loading_text = "Starting gesture recognition..."
        self.loading_label.config(text=loading_text)

        with self.mp_hands.Hands(min_detection_confidence=0.8, min_tracking_confidence=0.5) as hands:
            while self.cap.isOpened():
                success, image = self.cap.read()
                if not success:
                    print("Ignoring empty camera frame.")
                    continue

                image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
                image.flags.writeable = False
                self.results = hands.process(image)
                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                if self.results.multi_hand_landmarks:
                    for hand_landmarks in self.results.multi_hand_landmarks:
                        self.mp_drawing.draw_landmarks(
                            image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                lm_list = self.finger_position(image)
                if len(lm_list) != 0:
                    fingers = []
                    for id in range(1, 5):
                        if lm_list[self.tip_ids[id]][2] < lm_list[self.tip_ids[id] - 2][2]:
                            fingers.append(1)
                        if (lm_list[self.tip_ids[id]][2] > lm_list[self.tip_ids[id] - 2][2]):
                            fingers.append(0)
                    total_fingers = fingers.count(1)

                    if total_fingers == 4:
                        self.state = "Playing"
                    if total_fingers == 0 and self.state == "Playing":
                        self.state = "Paused"
                        pyautogui.press('space')
                    if total_fingers == 1:
                        if lm_list[8][1] < 300:
                            pyautogui.press('left')
                        if lm_list[8][1] > 400:
                            pyautogui.press('Right')
                    if total_fingers == 2:
                        if lm_list[9][2] < 210:
                            pyautogui.press('volumeup')
                        if lm_list[9][2] > 230:
                            pyautogui.press('volumedown')

                cv2.putText(image, f"State: {self.state}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                self.img_tk = ImageTk.PhotoImage(image=Image.fromarray(image))

                if self.canvas is not None:
                    self.canvas.create_image(0, 0, anchor=tk.NW, image=self.img_tk)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            cv2.destroyAllWindows()

    def start_processing(self):
        if not self.start_button_disabled:
            self.start_button_disabled = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)  # Change background color
            self.progress_bar.start(10)  # Start progress bar

            # Start camera initialization in a separate thread
            threading.Thread(target=self.initialize_camera).start()

    def initialize_camera(self):
        self.progress_bar.pack(pady=5)
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.w_cam)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.h_cam)
        self.results = None
        self.loading_label.config(text="Starting gesture recognition...")
        self.progress_bar.stop()
        self.progress_bar.pack_forget()

        # Create a canvas to display video feed
        self.canvas = tk.Canvas(self.root, width=self.w_cam, height=self.h_cam)
        self.canvas.pack()

        # Start processing video frames
        self.process_video()

    def stop_processing(self):
        if self.cap is not None:
            self.is_running = False  # Set the flag to stop the video processing thread
            self.cap.release()
        if self.canvas is not None:
            self.canvas.destroy()  # Destroy the canvas displaying the video feed
            self.canvas = None  # Reset the canvas reference
        self.start_button_disabled = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)  # Change background color
        self.loading_label.config(text="")
        self.progress_bar.stop()  # Stop progress bar

    def create_gui(self):
        self.root = tk.Tk()
        self.root.title("Ai Media Controller")
        self.root.geometry("640x540")
        self.root.configure(bg="#181818")  # Dark theme background color
        self.root.resizable(False, False)  # Disable window resizing

        # Increase space between start button and top
        start_button_padding = (0, 10)
        self.start_button = tk.Button(self.root, text="Start", command=self.start_processing, bg="#0D9276", fg='white',
                                      relief="solid", width=10)  # Off-white color
        self.start_button.pack(pady=20)

        self.stop_button = tk.Button(self.root, text="Stop", command=self.stop_processing, bg="#D05151", fg='white',
                                     state=tk.DISABLED, relief="solid", width=10)  # Dull color
        self.stop_button.pack(pady=5)

        self.loading_label = tk.Label(self.root, text="", bg="#181818", fg="#ffffff")  # Loading label
        self.loading_label.pack(pady=5)

        self.progress_bar = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, length=200, mode='indeterminate')

        # Bind window close event to cleanup function
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.root.mainloop()

    def on_close(self):
        # Release camera and stop processing when window is closed
        if self.cap is not None:
            self.cap.release()
        if self.canvas is not None:
            self.canvas.destroy()  # Destroy the canvas displaying the video feed
            self.canvas = None  # Reset the canvas reference
        self.start_button_disabled = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)  # Change background color
        self.loading_label.config(text="")
        self.progress_bar.stop()  # Stop progress bar
        self.root.destroy()  # Destroy the main window



if __name__ == "__main__":
    controller = HandGestureController()
    controller.create_gui()
