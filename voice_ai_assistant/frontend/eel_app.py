import eel
import requests

eel.init("frontend/web")

@eel.expose
def send_audio_to_api(file_path):
    # send file to http://localhost:8000/stt/transcribe
    pass

if __name__ == "__main__":
    eel.start("index.html", size=(800,600))
