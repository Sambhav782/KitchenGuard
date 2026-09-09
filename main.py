import numpy as np
import cv2
import os
import json
import threading
import time
import queue

from ultralytics import YOLO
from datetime import datetime
from flask import Flask, Response, request
from flask_cors import CORS


# ============================================================
# LOAD YOLO MODEL
# ============================================================

model = YOLO("yolo11n.pt")


# ============================================================
# FLASK SETUP
# ============================================================

app = Flask(__name__)
CORS(app)


# ============================================================
# SHARED STATE
# ============================================================

latest_frame = None

detection_started = False

selected_source = "demo"

source_changed = False

frame_condition = threading.Condition()
zone_condition = threading.Condition()


# ============================================================
# RESTRICTED ZONE
# ============================================================

zone = np.array([], dtype=np.int32)


# ============================================================
# SNAPSHOT FOLDER
# ============================================================

os.makedirs(
    "snapshots",
    exist_ok=True
)


# ============================================================
# SSE EVENT CLIENTS
# ============================================================

event_clients = []

event_clients_lock = threading.Lock()


# ============================================================
# VIDEO STREAM
# ============================================================

@app.route("/video")
def video():

    def generate():

        while True:

            with frame_condition:

                frame = latest_frame

            if frame is not None:

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + frame
                    + b"\r\n"
                )

            time.sleep(0.03)

    return Response(
        generate(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# ============================================================
# SERVER-SENT EVENTS
# ============================================================

@app.route("/events/stream")
def events_stream():

    client_queue = queue.Queue()

    with event_clients_lock:

        event_clients.append(
            client_queue
        )

    print("React event client connected.")

    def generate():

        try:

            while True:

                try:

                    event = client_queue.get(
                        timeout=15
                    )

                    yield (
                        f"data: {json.dumps(event)}\n\n"
                    ).encode("utf-8")

                except queue.Empty:

                    # Keep connection alive
                    yield b": keep-alive\n\n"

        finally:

            with event_clients_lock:

                if client_queue in event_clients:

                    event_clients.remove(
                        client_queue
                    )

            print(
                "React event client disconnected."
            )

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


# ============================================================
# BROADCAST NEW EVENT
# ============================================================

def broadcast_event(event):

    with event_clients_lock:

        clients = list(event_clients)


    for client_queue in clients:

        try:

            client_queue.put_nowait(
                event
            )

        except queue.Full:

            pass


# ============================================================
# SOURCE SELECTION
# ============================================================

@app.route("/source", methods=["POST"])
def set_source():

    global selected_source
    global source_changed
    global detection_started
    global latest_frame
    global zone

    data = request.get_json()

    source = data.get("source")


    if source not in ["live", "demo"]:

        return {
            "status": "error",
            "message": "Invalid source."
        }, 400


    # --------------------------------------------------------
    # Ignore if the same source is already active
    # --------------------------------------------------------

    if source == selected_source:

        return {
            "status": "success",
            "source": selected_source,
            "changed": False
        }


    # --------------------------------------------------------
    # Change source
    # --------------------------------------------------------

    selected_source = source

    source_changed = True

    detection_started = False


    # --------------------------------------------------------
    # Old zone belongs to old source.
    # New source must receive a new zone.
    # --------------------------------------------------------

    zone = np.array(
        [],
        dtype=np.int32
    )


    # --------------------------------------------------------
    # Clear current frame
    # --------------------------------------------------------

    with frame_condition:

        latest_frame = None

        frame_condition.notify_all()


    # --------------------------------------------------------
    # Wake detection thread if waiting for zone
    # --------------------------------------------------------

    with zone_condition:

        zone_condition.notify_all()


    print()

    print(
        f"Source changed to: {selected_source}"
    )

    print(
        "Restricted zone cleared."
    )


    return {
        "status": "success",
        "source": selected_source,
        "changed": True
    }


# ============================================================
# RESTRICTED ZONE
# ============================================================

@app.route("/zone", methods=["POST"])
def set_zone():

    global zone
    global detection_started

    data = request.get_json()

    points = data.get("points")


    if not points or len(points) < 3:

        return {
            "status": "error",
            "message": "At least 3 points are required."
        }, 400


    # --------------------------------------------------------
    # React sends normalized coordinates.
    #
    # Convert them into 1280 x 720.
    # --------------------------------------------------------

    zone = np.array(
        [
            [
                int(x * 1280),
                int(y * 720)
            ]
            for x, y in points
        ],
        dtype=np.int32
    )


    print()

    print("Zone updated:")

    print(zone)


    detection_started = True


    print(
        "Detection started."
    )


    with zone_condition:

        zone_condition.notify_all()


    return {
        "status": "success"
    }


# ============================================================
# OPEN VIDEO SOURCE
# ============================================================

def open_source():

    global selected_source


    if selected_source == "live":

        print()

        print(
            "Opening LIVE CAMERA..."
        )

        camera = cv2.VideoCapture(
            0
        )

        source_type = "live"


    else:

        print()

        print(
            "Opening DEMO VIDEO..."
        )

        camera = cv2.VideoCapture(
            "./footage/borderTest.mp4"
        )

        source_type = "demo"


    if not camera.isOpened():

        print(
            "Could not open selected source."
        )

        return None, source_type


    # --------------------------------------------------------
    # Reset demo video
    # --------------------------------------------------------

    if source_type == "demo":

        camera.set(
            cv2.CAP_PROP_POS_FRAMES,
            0
        )


    return camera, source_type


# ============================================================
# SEND FRAME TO REACT
# ============================================================

def publish_frame(frame):

    global latest_frame


    success, encoded_frame = cv2.imencode(
        ".jpg",
        frame,
        [
            cv2.IMWRITE_JPEG_QUALITY,
            70
        ]
    )


    if success:

        with frame_condition:

            latest_frame = (
                encoded_frame.tobytes()
            )

            frame_condition.notify_all()


# ============================================================
# WAIT FOR ZONE
# ============================================================

def wait_for_zone():

    global detection_started
    global source_changed


    print()

    print(
        "Select the restricted zone "
        "from the dashboard."
    )

    print(
        "Waiting for zone confirmation..."
    )


    with zone_condition:

        while (
            not detection_started
            and
            not source_changed
        ):

            zone_condition.wait()


    # --------------------------------------------------------
    # Source changed while waiting
    # --------------------------------------------------------

    if source_changed:

        return False


    return True


# ============================================================
# DETECTION FUNCTION
# ============================================================

def run_detection():

    global latest_frame
    global detection_started
    global source_changed


    # ========================================================
    # MAIN SOURCE LOOP
    # ========================================================

    while True:

        # ----------------------------------------------------
        # Reset source-change flag
        # ----------------------------------------------------

        source_changed = False


        # ----------------------------------------------------
        # Open selected source
        # ----------------------------------------------------

        camera, source_type = open_source()


        if camera is None:

            time.sleep(1)

            continue


        print(
            f"Source ready: {source_type}"
        )


        # ====================================================
        # READ FIRST FRAME
        # ====================================================

        success, first_frame = camera.read()


        if not success:

            print(
                "Could not read first frame."
            )

            camera.release()

            time.sleep(1)

            continue


        # ====================================================
        # RESIZE FIRST FRAME
        # ====================================================

        preview_frame = cv2.resize(
            first_frame,
            (1280, 720)
        )


        # ====================================================
        # SEND PREVIEW
        # ====================================================

        publish_frame(
            preview_frame
        )


        print()

        print(
            "Video preview ready."
        )


        # ====================================================
        # WAIT FOR ZONE
        # ====================================================

        zone_ready = wait_for_zone()


        # ----------------------------------------------------
        # Source changed while waiting
        # ----------------------------------------------------

        if not zone_ready:

            camera.release()

            continue


        print()

        print(
            "Zone confirmed."
        )

        print(
            "Starting detection..."
        )


        # ====================================================
        # INTRUDER STATE
        # ====================================================

        intruders = set()

        missing_frames = {}

        GRACE_FRAMES = 15


        # ====================================================
        # DETECTION LOOP
        # ====================================================

        while True:

            # ------------------------------------------------
            # Check whether source changed
            # ------------------------------------------------

            if source_changed:

                print()

                print(
                    "Stopping current source..."
                )

                break


            # ------------------------------------------------
            # Read frame
            # ------------------------------------------------

            success, original_frame = camera.read()


            if not success:

                print(
                    "Video source ended."
                )

                break


            # ------------------------------------------------
            # Resize frame
            # ------------------------------------------------

            frame = cv2.resize(
                original_frame,
                (1280, 720)
            )


            # ------------------------------------------------
            # Intruders in this frame
            # ------------------------------------------------

            intruders_this_frame = set()


            # =================================================
            # YOLO TRACKING
            # =================================================

            results = model.track(
                frame,
                persist=True,
                classes=[0],
                verbose=False
            )


            result = results[0]

            boxes = result.boxes


            # =================================================
            # TRACKING IDS
            # =================================================

            if boxes.id is not None:

                track_ids = (
                    boxes.id
                    .int()
                    .cpu()
                    .tolist()
                )

            else:

                track_ids = [
                    None
                ] * len(boxes)


            # =================================================
            # PROCESS PEOPLE
            # =================================================

            for box, track_id in zip(
                boxes,
                track_ids
            ):

                class_id = int(
                    box.cls[0]
                )


                # COCO class 0 = person
                if class_id != 0:

                    continue


                # ------------------------------------------------
                # Bounding box
                # ------------------------------------------------

                x1, y1, x2, y2 = box.xyxy[0]


                x1 = int(x1)
                y1 = int(y1)
                x2 = int(x2)
                y2 = int(y2)


                # ------------------------------------------------
                # Feet point
                # ------------------------------------------------

                center_x = (
                    x1 + x2
                ) // 2

                center_y = y2


                # ------------------------------------------------
                # Zone check
                # ------------------------------------------------

                inside_zone = False


                if len(zone) >= 3:

                    inside_zone = (
                        cv2.pointPolygonTest(
                            zone,
                            (
                                center_x,
                                center_y
                            ),
                            False
                        ) >= 0
                    )


                # ------------------------------------------------
                # Intruder
                # ------------------------------------------------

                if inside_zone:

                    if track_id is not None:

                        intruders_this_frame.add(
                            track_id
                        )


                # ------------------------------------------------
                # Feet marker
                # ------------------------------------------------

                cv2.circle(
                    frame,
                    (
                        center_x,
                        center_y
                    ),
                    6,
                    (0, 0, 255),
                    -1
                )


                # ------------------------------------------------
                # Bounding box
                # ------------------------------------------------

                if inside_zone:

                    box_color = (
                        0,
                        0,
                        255
                    )

                else:

                    box_color = (
                        0,
                        255,
                        0
                    )


                cv2.rectangle(
                    frame,
                    (
                        x1,
                        y1
                    ),
                    (
                        x2,
                        y2
                    ),
                    box_color,
                    2
                )


                # ------------------------------------------------
                # Person ID
                # ------------------------------------------------

                cv2.putText(
                    frame,
                    f"Person ID: {track_id}",
                    (
                        x1,
                        y1 - 10
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    3
                )


            # =================================================
            # INTRUDER WARNING
            # =================================================

            if intruders_this_frame:

                intruder_text = (
                    "INTRUDERS DETECTED - IDs: "
                    +
                    ", ".join(
                        str(track_id)
                        for track_id
                        in sorted(
                            intruders_this_frame
                        )
                    )
                )


                cv2.putText(
                    frame,
                    intruder_text,
                    (
                        50,
                        50
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2
                )


            # =================================================
            # NEW INTRUSIONS
            # =================================================

            new_intruders = (
                intruders_this_frame
                - intruders
            )


            if new_intruders:

                print()

                print(
                    "New intrusion detected!"
                )


                # ------------------------------------------------
                # Snapshot
                # ------------------------------------------------

                timestamp = datetime.now().strftime(
                    "%Y%m%d_%H%M%S_%f"
                )


                snapshot_path = (
                    f"snapshots/"
                    f"intrusion_{timestamp}.jpg"
                )


                cv2.imwrite(
                    snapshot_path,
                    frame
                )


                # ------------------------------------------------
                # Read events
                # ------------------------------------------------

                try:

                    with open(
                        "events.json",
                        "r"
                    ) as file:

                        events = json.load(file)

                except (
                    FileNotFoundError,
                    json.JSONDecodeError
                ):

                    events = []


                # ------------------------------------------------
                # Add events
                # ------------------------------------------------

                for track_id in new_intruders:

                    event = {

                        "personId": track_id,

                        "time": datetime.now().strftime(
                            "%H:%M:%S"
                        ),

                        "snapshot": snapshot_path
                    }


                    events.append(
                        event
                    )


                    print(
                        f"INTRUSION DETECTED! "
                        f"Person ID: {track_id}"
                    )


                    print(
                        f"Snapshot saved: "
                        f"{snapshot_path}"
                    )


                    missing_frames[
                        track_id
                    ] = 0


                    # ------------------------------------------------
                    # SEND EVENT TO REACT IMMEDIATELY
                    # ------------------------------------------------

                    broadcast_event(
                        event
                    )


                # ------------------------------------------------
                # Save events
                # ------------------------------------------------

                with open(
                    "events.json",
                    "w"
                ) as file:

                    json.dump(
                        events,
                        file,
                        indent=4
                    )


            # =================================================
            # PEOPLE LEAVING
            # =================================================

            for track_id in list(intruders):

                if (
                    track_id
                    not in intruders_this_frame
                ):

                    missing_frames[
                        track_id
                    ] = (
                        missing_frames.get(
                            track_id,
                            0
                        ) + 1
                    )


                    if (
                        missing_frames[
                            track_id
                        ]
                        >= GRACE_FRAMES
                    ):

                        print(
                            f"Person ID: {track_id} "
                            "left the restricted zone."
                        )


                        intruders.discard(
                            track_id
                        )


                        missing_frames.pop(
                            track_id,
                            None
                        )


            # =================================================
            # RESET MISSING COUNTERS
            # =================================================

            for track_id in intruders_this_frame:

                missing_frames[
                    track_id
                ] = 0


            # =================================================
            # UPDATE CURRENT INTRUDERS
            # =================================================

            intruders.update(
                intruders_this_frame
            )


            # =================================================
            # SEND FRAME TO REACT
            # =================================================

            publish_frame(
                frame
            )


            # =================================================
            # DEMO VIDEO END
            # =================================================

            if source_type == "demo":

                current_frame = camera.get(
                    cv2.CAP_PROP_POS_FRAMES
                )

                total_frames = camera.get(
                    cv2.CAP_PROP_FRAME_COUNT
                )


                if (
                    total_frames > 0
                    and
                    current_frame >= total_frames
                ):

                    print()

                    print(
                        "Demo video finished."
                    )

                    break


        # ====================================================
        # CLEANUP CURRENT SOURCE
        # ====================================================

        camera.release()


        # ====================================================
        # IF SOURCE WAS CHANGED
        # ====================================================

        if source_changed:

            print(
                "Opening new source..."
            )

            continue


        # ====================================================
        # DEMO FINISHED
        # ====================================================

        if source_type == "demo":

            print(
                "Demo session ended."
            )

            detection_started = False

            continue


        # ====================================================
        # LIVE CAMERA STOPPED
        # ====================================================

        detection_started = False

        time.sleep(0.5)


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    detection_thread = threading.Thread(
        target=run_detection,
        daemon=True
    )


    detection_thread.start()


    app.run(
        host="0.0.0.0",
        port=5001,
        threaded=True
    )