from ultralytics import YOLO
import cv2

# LOAD YOLO MODEL

model = YOLO("yolo11n.pt")

# OPEN WEBCAM

camera = cv2.VideoCapture(0)

# SELECT KITCHEN ZONE

print("Select the Kitchen Zone using your mouse.")
print("Press ENTER or SPACE to confirm the selection.")

# Read one frame for selecting the kitchen zone
success, frame = camera.read()

if not success:
    print("Could not read from camera.")
    camera.release()
    exit()

# Let the user drag a rectangle around the kitchen

roi = cv2.selectROI(
"Select Kitchen Zone",
frame,
fromCenter=False,
showCrosshair=True
)

# Close the selection window

cv2.destroyWindow("Select Kitchen Zone")

# ROI returns: x, y, width, height

x, y, width, height = roi

# Convert ROI into corner coordinates

kitchen_x1 = x
kitchen_y1 = y
kitchen_x2 = x + width
kitchen_y2 = y + height

# INTRUDER STATE

intruder_present = False

# CREATE DISPLAY WINDOW

cv2.namedWindow("Kitchen Guard", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Kitchen Guard", 900, 600)

# MAIN LOOP

while True:

    # Read one frame
    success, frame = camera.read()

    # Stop if camera cannot provide a frame
    if not success:
        break


    # Nobody is inside at the beginning of this frame
    person_inside = False


    # Detect objects
    results = model(frame, verbose=False)

    # Get detections
    result = results[0]


    # Go through every detected object
    for box in result.boxes:

        # Get object class
        class_id = int(box.cls[0])


        # Only detect humans
        # COCO class 0 = person
        if class_id != 0:
            continue


        # Get bounding box coordinates
        x1, y1, x2, y2 = box.xyxy[0]


        # Convert coordinates to integers
        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)


        # Calculate the center of the person
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2


        # Check if the person is inside the selected kitchen zone
        inside_kitchen = (
            kitchen_x1 < center_x < kitchen_x2
            and kitchen_y1 < center_y < kitchen_y2
        )


        # If at least one person is inside
        if inside_kitchen:

            person_inside = True

            cv2.putText(
                frame,
                "INTRUDER!",
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                3
            )


        # Draw center point
        cv2.circle(
            frame,
            (center_x, center_y),
            6,
            (0, 0, 255),
            -1
        )


        # Draw bounding box around the person
        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )


        # Add label
        cv2.putText(
            frame,
            "Person",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )


    # INTRUDER EVENT LOGIC

    # Person just entered the kitchen
    if person_inside and not intruder_present:

        print("INTRUDER DETECTED!")

        intruder_present = True


    # Everyone has left the kitchen
    elif not person_inside and intruder_present:

        print("Kitchen zone is clear.")

        intruder_present = False


    # DRAW KITCHEN ZONE
    cv2.rectangle(
        frame,
        (kitchen_x1, kitchen_y1),
        (kitchen_x2, kitchen_y2),
        (255, 0, 0),
        2
    )


    cv2.putText(
        frame,
        "KITCHEN ZONE",
        (kitchen_x1, kitchen_y1 - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 0, 0),
        2
    )


    # Show the processed frame
    cv2.imshow("Kitchen Guard", frame)


    # Press Q to exit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# CLEANUP

camera.release()
cv2.destroyAllWindows()
