import cv2
import numpy as np
import mss
import time
import os

def record_screen(filename="assessment_demo.mp4", duration=60, fps=20):
    print(f"Starting screen recording for {duration} seconds...")
    
    sct = mss.mss()
    monitor = sct.monitors[1]  # Capture primary monitor
    
    width = monitor["width"]
    height = monitor["height"]
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    start_time = time.time()
    frames_captured = 0
    
    try:
        while True:
            img = np.array(sct.grab(monitor))
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            out.write(frame)
            frames_captured += 1
            
            elapsed = time.time() - start_time
            if elapsed >= duration:
                break
                
            time.sleep(max(0, 1.0/fps - (time.time() - start_time - frames_captured/fps)))
            
    except KeyboardInterrupt:
        print("\nRecording stopped early by user.")
    finally:
        out.release()
        print(f"Recording saved successfully as: {os.path.abspath(filename)}")

if __name__ == "__main__":
    # Record for exactly 60 seconds to fulfill assessment criteria quickly
    record_screen(filename="assessment_demo.mp4", duration=60, fps=20)
