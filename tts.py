import pyttsx3
import threading

def speak_live_text(text, voice_name=None, rate=150):
    def speak():
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", rate)

            if voice_name and voice_name != "Default":
                for voice in engine.getProperty('voices'):
                    if voice_name.lower() in voice.name.lower():
                        engine.setProperty("voice", voice.id)
                        break

            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            print(f"[Live Speech Error] {e}")

    threading.Thread(target=speak).start()
    return True

def generate_audio_file(text, output_file="output.wav", voice_name=None, rate=150):
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", rate)

        if voice_name and voice_name != "Default":
            for voice in engine.getProperty('voices'):
                if voice_name.lower() in voice.name.lower():
                    engine.setProperty("voice", voice.id)
                    break

        engine.save_to_file(text, output_file)
        engine.runAndWait()
        engine.stop()
        return output_file
    except Exception as e:
        print(f"[File TTS Error] {e}")
        return None

def get_available_voices():
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        voice_names = ["Default"] + [v.name for v in voices if v.name]
        engine.stop()
        return voice_names
    except Exception as e:
        print(f"[Voice Error] {e}")
        return ["Default"]
