import argparse
import pickle
from collections import Counter
from pathlib import Path
import numpy as np
import face_recognition
from PIL import Image, ImageDraw, ImageTk
import mss
import os
import time
from pynput import keyboard
import tkinter as tk
from tkinter import ttk

DEFAULT_ENCODINGS_PATH = Path("facechecker/output/encodings.pkl")
BOUNDING_BOX_COLOR = "blue"
TEXT_COLOR = "white"
CONFIDENCE_THRESHOLD = 0.4  # Adjust this value as needed
''
parser = argparse.ArgumentParser(description="Recognize faces in an image")
parser.add_argument("--train", action="store_true", help="Train on input data")
parser.add_argument(
    "--validate", action="store_true", help="Validate trained model"
)
parser.add_argument(
    "--test", action="store_true", help="Test the model with an unknown image"
)
parser.add_argument(
    "-m",
    action="store",
    default="hog",
    choices=["hog", "cnn"],
    help="Which model to use for training: hog (CPU), cnn (GPU)",
)
parser.add_argument(
    "-f", action="store", help="Path to an image with an unknown face"
)
args = parser.parse_args()

def encode_known_faces(
    model: str = "hog", encodings_location: Path = DEFAULT_ENCODINGS_PATH
) -> None:
    """
    Loads images in the training directory and builds a dictionary of their
    names and encodings.
    """
    names = []
    encodings = []

    for filepath in Path("training").glob("*/*"):
        name = filepath.parent.name
        image = face_recognition.load_image_file(filepath)

        face_locations = face_recognition.face_locations(image, model=model)
        face_encodings = face_recognition.face_encodings(image, face_locations)

        for encoding in face_encodings:
            names.append(name)
            encodings.append(encoding)

    name_encodings = {"names": names, "encodings": encodings}
    with encodings_location.open(mode="wb") as f:
        pickle.dump(name_encodings, f)

def recognize_faces(
    image_array,
    model: str = "hog",
    encodings_location: Path = DEFAULT_ENCODINGS_PATH,
) -> Image:
    """
    Given an image array, get the locations and encodings of any faces and
    compares them against the known encodings to find potential matches.
    """
    with encodings_location.open(mode="rb") as f:
        loaded_encodings = pickle.load(f)

    input_face_locations = face_recognition.face_locations(image_array, model=model)
    input_face_encodings = face_recognition.face_encodings(image_array, input_face_locations)

    pillow_image = Image.fromarray(image_array)
    draw = ImageDraw.Draw(pillow_image)

    has_face = False
    for bounding_box, unknown_encoding in zip(input_face_locations, input_face_encodings):
        name = _recognize_face(unknown_encoding, loaded_encodings)
        if name:
            _display_face(draw, bounding_box, name)
            has_face = True

    del draw
    return pillow_image if has_face else None

def _recognize_face(unknown_encoding, loaded_encodings):
    """
    Given an unknown encoding and all known encodings, find the known
    encoding with the most matches.
    """
    distances = face_recognition.face_distance(loaded_encodings["encodings"], unknown_encoding)
    best_match_index = np.argmin(distances)

    # Debugging statements to trace values
    print(f"Distances: {distances}")
    print(f"Best match index: {best_match_index}")
    print(f"Best match distance: {distances[best_match_index]}")

    if distances[best_match_index] < CONFIDENCE_THRESHOLD:
        return loaded_encodings["names"][best_match_index]
    else:
        return None

def _display_face(draw, bounding_box, name):
    """
    Draws bounding boxes around faces, a caption area, and text captions.
    """
    top, right, bottom, left = bounding_box
    draw.rectangle(((left, top), (right, bottom)), outline=BOUNDING_BOX_COLOR)
    text_left, text_top, text_right, text_bottom = draw.textbbox(
        (left, bottom), name
    )
    draw.rectangle(
        ((text_left, text_top), (text_right, text_bottom)),
        fill=BOUNDING_BOX_COLOR,
        outline=BOUNDING_BOX_COLOR,
    )
    draw.text(
        (text_left, text_top),
        name,
        fill=TEXT_COLOR,
    )

def validate(model: str = "hog"):
    """
    Runs recognize_faces on a set of images with known faces to validate
    known encodings.
    """
    for filepath in Path("validation").rglob("*"):
        if filepath.is_file():
            recognize_faces(
                image_location=str(filepath.absolute()), model=model
            )

if __name__ == "__main__":
    
    if args.train:
        encode_known_faces(model=args.m)
    if args.validate:
        validate(model=args.m)
    if args.test:
        recognize_faces(image_location=args.f, model=args.m)

    exit_flag = False

    # Start the keyboard listener in the main thread
    listener = keyboard.Listener(on_press=lambda key: exit() if hasattr(key, 'char') and key.char == 'x' else None)
    listener.start()

    def exit():
        global exit_flag
        exit_flag = True
        print("Exiting the loop...")
        listener.stop()

    while not exit_flag:
        # Capture the entire screen
        with mss.mss() as sct:
            # Get the current time
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            # Create the screenshot filename
            filename = f"Lebron_{timestamp}.png"
            # Full path to save the screenshot
            filepath = os.path.join("facechecker/images", filename)
            
            # Grab the screen
            screenshot = sct.grab(sct.monitors[1])
            
            # Convert the screenshot to a Pillow Image
            img = Image.frombytes("RGB", (screenshot.width, screenshot.height), screenshot.rgb)

            # Convert the Pillow Image to an array for face recognition
            image_array = np.array(img)

            # Run the face recognition
            result_image = recognize_faces(image_array, model=args.m)
            
            # Save the image if a face is recognized
            if result_image:
                result_image.save(filepath)
                print(f"Screenshot with faces saved as {filepath}")
            else:
                print("No faces detected, screenshot not saved.")
        
        # Add a delay to avoid excessive loop execution (e.g., 1 second)
        time.sleep(1)

    listener.join()
