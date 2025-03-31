import speech_recognition as sr


def recognize_hindi_speech():
    # Initialize recognizer and microphone
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    print("Please speak in Hindi...")
    with microphone as source:
        # Adjust for ambient noise
        recognizer.adjust_for_ambient_noise(source, duration=2)
        audio = recognizer.listen(source, timeout=20, phrase_time_limit=10)

    try:
        # Recognize speech using Google Speech Recognition (Hindi)
        text = recognizer.recognize_google(audio, language="hi-IN")
        print(f"Transcribed Hindi text: {text}")
        return text
    except sr.UnknownValueError:
        print("Sorry, I couldn't understand the audio.")
        return "Sorry, I couldn't understand the audio."
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
        return f"Error: {e}"


if __name__ == "__main__":
    hindi_text = recognize_hindi_speech()
