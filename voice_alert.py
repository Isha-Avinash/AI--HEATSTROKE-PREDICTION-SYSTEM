import pyttsx3

def speak(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)   # speed
    engine.setProperty('volume', 1)   # volume max

    engine.say(text)
    engine.runAndWait()