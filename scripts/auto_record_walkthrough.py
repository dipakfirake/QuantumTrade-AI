import time
import os
import threading
import cv2
import numpy as np
import mss
import pyautogui
import webbrowser
from PIL import ImageGrab

pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = False

RECORDING_FILE = "assessment_demo.mp4"
DURATION_SECONDS = 65
FPS = 20

stop_recording = False

def record_screen_worker(output_path, duration, fps):
    global stop_recording
    print(f"[Recorder] Initializing screen capture to {output_path} ({duration}s @ {fps}fps)...")
    
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except Exception:
            pass

    screen_w, screen_h = pyautogui.size()
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (screen_w, screen_h))
    
    start_time = time.time()
    frame_interval = 1.0 / fps
    frames_written = 0
    
    use_mss = True
    sct = None
    try:
        sct = mss.mss()
        monitor = sct.monitors[1]
    except Exception as e:
        print(f"[Recorder] MSS init error ({e}), falling back to PIL.ImageGrab")
        use_mss = False

    try:
        while not stop_recording and (time.time() - start_time < duration):
            loop_start = time.time()
            frame = None
            
            if use_mss and sct:
                try:
                    img = np.array(sct.grab(monitor))
                    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                except Exception:
                    use_mss = False
            
            if frame is None:
                try:
                    img = ImageGrab.grab()
                    frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                except Exception:
                    pass
            
            if frame is not None:
                if frame.shape[1] != screen_w or frame.shape[0] != screen_h:
                    frame = cv2.resize(frame, (screen_w, screen_h))
                out.write(frame)
                frames_written += 1
            
            elapsed_loop = time.time() - loop_start
            sleep_time = max(0.001, frame_interval - elapsed_loop)
            time.sleep(sleep_time)
    finally:
        out.release()
        if sct:
            try:
                sct.close()
            except Exception:
                pass
        print(f"[Recorder] Screen recording saved ({frames_written} frames) to: {os.path.abspath(output_path)}")

def run_automated_walkthrough():
    global stop_recording
    print("[Walkthrough] Starting QuantumTrade AI Automated Interactive Walkthrough...")
    
    # 1. Open dashboard in browser
    url = "http://localhost:8501"
    print(f"[Walkthrough] Opening {url}...")
    webbrowser.open(url)
    time.sleep(5)  # Wait for browser to open and render
    
    # Start screen recording in background thread
    rec_thread = threading.Thread(target=record_screen_worker, args=(RECORDING_FILE, DURATION_SECONDS, FPS))
    rec_thread.start()
    
    screen_w, screen_h = pyautogui.size()
    center_x, center_y = screen_w // 2, screen_h // 2
    
    # Give initial 4 seconds on Tab 1
    print("[Walkthrough] Tab 1: Live Screening Dashboard - Top Metrics & Header")
    pyautogui.click(center_x, center_y)
    time.sleep(4)
    
    # Scroll down to showcase live table
    print("[Walkthrough] Scrolling through 165 qualified stocks and real-time ETQ/Depth...")
    for _ in range(6):
        pyautogui.scroll(-300)
        time.sleep(1.2)
    
    time.sleep(2)
    
    # Scroll back up
    for _ in range(6):
        pyautogui.scroll(300)
        time.sleep(0.8)
    
    time.sleep(1.5)
    
    # Switch to Tab 2: AI/ML Signal Analysis
    print("[Walkthrough] Switching to Tab 2: AI/ML Signal Analysis...")
    tab_y = int(screen_h * 0.28)
    tab2_x = int(screen_w * 0.42)
    pyautogui.click(tab2_x, tab_y)
    time.sleep(2.5)
    
    # Scroll through AI/ML signal cards
    print("[Walkthrough] Showcasing XGBoost predictions, confidence levels, and SHAP reasoning...")
    for _ in range(5):
        pyautogui.scroll(-250)
        time.sleep(1.5)
    
    time.sleep(2)
    for _ in range(5):
        pyautogui.scroll(250)
        time.sleep(0.8)
    
    # Switch to Tab 3: Trade Log
    print("[Walkthrough] Switching to Tab 3: Trade Log...")
    tab3_x = int(screen_w * 0.52)
    pyautogui.click(tab3_x, tab_y)
    time.sleep(2.5)
    
    print("[Walkthrough] Showcasing Open Positions & Trade Tracker...")
    for _ in range(4):
        pyautogui.scroll(-250)
        time.sleep(1.5)
    
    time.sleep(1.5)
    for _ in range(4):
        pyautogui.scroll(250)
        time.sleep(0.8)
    
    # Switch to Tab 4: Model Performance
    print("[Walkthrough] Switching to Tab 4: Model Performance...")
    tab4_x = int(screen_w * 0.62)
    pyautogui.click(tab4_x, tab_y)
    time.sleep(2.5)
    
    print("[Walkthrough] Showcasing XGBoost Feature Importance Chart...")
    for _ in range(3):
        pyautogui.scroll(-200)
        time.sleep(1.5)
    
    time.sleep(3)
    
    # Switch back to Tab 1
    print("[Walkthrough] Returning to Tab 1...")
    tab1_x = int(screen_w * 0.32)
    pyautogui.click(tab1_x, tab_y)
    time.sleep(3)
    
    print("[Walkthrough] Automation sequence complete. Finalizing recording...")
    stop_recording = True
    rec_thread.join()
    print(f"[Complete] Walkthrough video generated successfully: {os.path.abspath(RECORDING_FILE)}")

if __name__ == "__main__":
    run_automated_walkthrough()
