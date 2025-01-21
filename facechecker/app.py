import os
import subprocess
from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window

class ImageViewerApp(App):
    def __init__(self, folder_path, **kwargs):
        super().__init__(**kwargs)
        Window.set_icon('facechecker/download.jpeg')  # Path to the app icon
        Window.title = "Sunshine Detector"  # Set the application window title
        self.folder_path = folder_path
        self.image_files = []
        self.current_image_index = 0
        self.script_process = None
        self.load_images()
        self.background_sound = None

    def load_images(self):
        if os.path.isdir(self.folder_path):
            self.image_files = [os.path.join(self.folder_path, file) for file in os.listdir(self.folder_path) if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            if not self.image_files:
                print("No image files found in the specified directory.")
            else:
                print(f"Loaded {len(self.image_files)} images from {self.folder_path}")
        else:
            print(f"Directory {self.folder_path} does not exist.")

    def build(self):
        self.root = BoxLayout(orientation='vertical')

        # Top button layout
        top_button_layout = BoxLayout(size_hint_y=None, height='50dp')
        delete_button = Button(text='Delete', on_release=self.delete_image)
        self.run_script_button = Button(text='Start', on_release=self.toggle_script)

        top_button_layout.add_widget(delete_button)
        top_button_layout.add_widget(BoxLayout())  # Add a spacer
        top_button_layout.add_widget(self.run_script_button)

        self.root.add_widget(top_button_layout)

        # Image display widget
        self.image_widget = Image(allow_stretch=True, keep_ratio=True)
        self.root.add_widget(self.image_widget)

        # Bottom button layout
        button_layout = BoxLayout(size_hint_y=None, height='50dp')
        prev_button = Button(text='Previous', on_release=self.show_previous_image)
        next_button = Button(text='Next', on_release=self.show_next_image)

        button_layout.add_widget(prev_button)
        button_layout.add_widget(next_button)

        self.root.add_widget(button_layout)

        self.show_image()
        self.play_background_sound()  # Start playing the background sound

        return self.root

    def play_background_sound(self):
        self.background_sound = SoundLoader.load('path/to/your/soundfile.mp3')  # Replace with your sound file path
        if self.background_sound:
            self.background_sound.loop = True  # Enable looping
            self.background_sound.play()  # Play the sound

    def show_image(self):
        if self.image_files:
            image_path = self.image_files[self.current_image_index]
            print(f"Showing image {image_path}")
            self.image_widget.source = image_path
            self.image_widget.reload()  # Ensure the image widget updates
        else:
            print("No images to show. Displaying default background.")
            self.image_widget.source = 'facechecker/download.jpeg'  # Default background image
            self.image_widget.reload()  # Ensure the image widget updates

    def show_next_image(self, instance):
        if self.image_files:
            self.current_image_index = (self.current_image_index + 1) % len(self.image_files)
            self.show_image()

    def show_previous_image(self, instance):
        if self.image_files:
            self.current_image_index = (self.current_image_index - 1) % len(self.image_files)
            self.show_image()

    def delete_image(self, instance):
        if self.image_files:
            image_path = self.image_files.pop(self.current_image_index)
            print(f"Deleting image {image_path}")
            os.remove(image_path)
            if self.current_image_index >= len(self.image_files):
                self.current_image_index = 0
            self.show_image()

    def toggle_script(self, instance):
        if self.script_process is None:
            self.run_script()
        else:
            self.stop_script()

    def run_script(self):
        script_path = "/Users/dzhang/Downloads/Recruiting/Coding/LebronChecker/facechecker/LeBonBonDectector.py"  # Path to the script
        print(f"Running script {script_path}")
        self.script_process = subprocess.Popen(["python3", script_path])
        self.run_script_button.text = "Stop"
        Clock.schedule_interval(self.refresh_images, 1)  # Refresh images every second

    def stop_script(self):
        if self.script_process:
            print("Stopping script")
            self.script_process.terminate()
            self.script_process = None
            self.run_script_button.text = "Start"
            Clock.unschedule(self.refresh_images)

    def refresh_images(self, dt):
        current_images = set(self.image_files)
        self.load_images()
        new_images = set(self.image_files) - current_images

        if new_images:
            print(f"New images found: {new_images}")
            self.current_image_index = len(self.image_files) - len(new_images)
            self.show_image()

if __name__ == '__main__':
    folder_path = "facechecker/images"  # Replace with the path to your folder
    ImageViewerApp(folder_path=folder_path).run()
