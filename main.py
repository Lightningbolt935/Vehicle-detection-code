import cv2
import numpy as np
import time
import os

# Load YOLO
try:
    if not os.path.exists("yolov3.weights") or not os.path.exists("yolov3.cfg"):
        print("Error: YOLO model files not found. Check the paths.")
        exit()
    net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
    print("YOLO model loaded successfully.")
except Exception as e:
    print(f"Error loading YOLO model: {e}")
    exit()

layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

# Load class labels
try:
    if not os.path.exists("coco.names"):
        print("Error: COCO names file not found. Check the path.")
        exit()
    with open("coco.names", "r") as f:
        classes = [line.strip() for line in f.readlines()]
    print("Class labels loaded successfully.")
except FileNotFoundError as e:
    print(f"Error loading coco.names: {e}")
    exit()

# Initialize parameters for vehicle counting
previous_vehicle_positions = {"north": {}, "south": {}, "east": {}, "west": {}}  # Track previous positions of vehicles

# Function to process frame and count vehicles for each direction
def process_frame(direction, frame, previous_vehicle_positions):
    height, width, _ = frame.shape
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)

    # Get detections
    outs = net.forward(output_layers)

    class_ids = []
    confidences = []
    boxes = []

    # Process each detection
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]

            # Filter out weak predictions
            if confidence > 0.5 and class_id in [2, 3, 5, 7]:  # Only car, motorcycle, bus, truck
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)

                # Rectangle coordinates
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    # Apply Non-Max Suppression
    indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
    current_vehicle_positions = {}  # Current frame vehicle positions
    incoming_vehicles = 0
    outgoing_vehicles = 0

    if len(indices) > 0:
        for i in indices.flatten():
            label = str(classes[class_ids[i]])
            if label in ['car', 'motorcycle', 'bus', 'truck']:
                x, y, w, h = boxes[i]
                vehicle_id = f"{label}_{i}"

                # Track vehicle positions
                current_position = (x + w // 2, y + h // 2)  # Center point of the bounding box
                current_vehicle_positions[vehicle_id] = current_position

                # Determine if the vehicle is coming or going
                if vehicle_id in previous_vehicle_positions:
                    previous_position = previous_vehicle_positions[vehicle_id]
                    if current_position[0] < previous_position[0]:
                        outgoing_vehicles += 1
                    elif current_position[0] > previous_position[0]:
                        incoming_vehicles += 1

                previous_vehicle_positions[vehicle_id] = current_position

    # Count total vehicles and calculate stopped vehicles
    total_vehicles = len(current_vehicle_positions)
    stopped_vehicles = total_vehicles - (incoming_vehicles + outgoing_vehicles)

    return stopped_vehicles, previous_vehicle_positions


# Simple Roundabout Traffic Controller
class RoundaboutTrafficController:
    def __init__(self):
        self.base_duration = 15  # Base duration in seconds

    def adjust_light_duration(self, traffic_densities):
        # Adjust green light duration based on traffic densities
        return [max(5, min(30, self.base_duration + density // 2)) for density in traffic_densities]

    def run_cycle(self, traffic_densities):
        directions = ["North", "South", "East", "West"]
        
        print(f"Current traffic densities: {dict(zip(directions, traffic_densities))}")

        durations = self.adjust_light_duration(traffic_densities)
        print(f"Adjusted green light durations: {dict(zip(directions, durations))}")
        
        # Simulate green light phase for each direction
        for direction, duration in zip(directions, durations):
            print(f"{direction} Green light ON for {duration} seconds")
            time.sleep(duration)
            print(f"{direction} Green light OFF")

        print()  # New line for clarity


if __name__ == "__main__":
    # Define video paths for each direction
    video_paths = {
        "north": "video_north.mp4",  # Replace with your video file path for north
        "south": "video_south.mp4",  # Replace with your video file path for south
        "east": "video_east.mp4",    # Replace with your video file path for east
        "west": "video_west.mp4"     # Replace with your video file path for west
    }

    # Open video captures for all directions
    caps = {}
    for direction, video_path in video_paths.items():
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video {video_path} for {direction}.")
            exit()
        caps[direction] = cap

    # Time interval for processing in milliseconds
    time_interval = 5000
    last_time = 0

    # Initialize the traffic controller
    controller = RoundaboutTrafficController()

    while True:
        current_time = time.time() * 1000  # Get current time in milliseconds

        # Check if 5 seconds have passed since the last update
        if current_time - last_time >= time_interval:
            last_time = current_time

            # Dictionary to store stopped vehicle counts for each direction
            stopped_vehicle_counts = {}

            # Process each direction's frame and update stopped vehicle counts
            for direction, cap in caps.items():
                ret, frame = cap.read()
                if not ret:
                    print(f"End of video or error reading frame for {direction}.")
                    break

                stopped_vehicles, previous_vehicle_positions[direction] = process_frame(
                    direction, frame, previous_vehicle_positions[direction]
                )
                stopped_vehicle_counts[direction] = stopped_vehicles

            # Run the traffic light cycle using stopped vehicle counts
            traffic_densities = [
                stopped_vehicle_counts.get("north", 0),
                stopped_vehicle_counts.get("south", 0),
                stopped_vehicle_counts.get("east", 0),
                stopped_vehicle_counts.get("west", 0)
            ]

            controller.run_cycle(traffic_densities)

        # Exit if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release all captures and close windows
    for cap in caps.values():
        cap.release()
    cv2.destroyAllWindows()
