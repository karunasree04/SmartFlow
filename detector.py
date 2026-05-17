import cv2
import torch
import os

model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

def process_video(path):
    cap = cv2.VideoCapture(path)

    os.makedirs("static", exist_ok=True)
    output_path = "static/output.mp4"

    width = int(cap.get(3))
    height = int(cap.get(4))
    fps = int(cap.get(5))

    out = cv2.VideoWriter(output_path,
                          cv2.VideoWriter_fourcc(*'mp4v'),
                          fps,
                          (width, height))

    lane_counts = [0, 0, 0, 0]
    ambulance_detected = False

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)
        detections = results.xyxy[0]

        for *box, conf, cls in detections:
            label = model.names[int(cls)]
            x1, y1, x2, y2 = map(int, box)

            color = (0, 255, 0)

            if "ambulance" in label:
                ambulance_detected = True
                color = (0, 0, 255)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            cx = (x1 + x2) // 2
            lane = min(cx // (width // 4), 3)

            if label in ['car', 'bus', 'truck', 'motorbike']:
                lane_counts[lane] += 1

        out.write(frame)

    cap.release()
    out.release()

    return lane_counts, ambulance_detected, "output.mp4"