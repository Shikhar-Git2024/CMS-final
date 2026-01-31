import cv2
from ultralytics import YOLO
import numpy as np

model = YOLO("yolov8n.pt")

FRAME_WINDOW = 30   # rolling average window

def count_people(video_path, output_path=None):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise Exception("Cannot open video")

    counts = []

    # For saving processed video (optional)
    writer = None
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = cap.get(cv2.CAP_PROP_FPS)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    '''
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        '''
    frame_limit = 150
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret or frame_count >= frame_limit:
            break
        frame_count += 1

        results = model(frame, stream=True)

        people_count = 0
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                if cls == 0:
                    people_count += 1

        counts.append(people_count)
        if len(counts) > FRAME_WINDOW:
            counts.pop(0)

        avg_count = int(np.mean(counts))

        # Draw count on frame
        cv2.putText(frame, f"People: {avg_count}", (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        if writer:
            writer.write(frame)

    cap.release()
    if writer:
        writer.release()

    final_count = int(np.mean(counts)) if counts else 0
    return final_count
