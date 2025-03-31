from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
import tempfile
import os
from .ollama_client import OllamaClient
from .url_navigator2 import URLNavigator

with open("Zingo_app/config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

ollama_client = OllamaClient(model_name="Zingo")
url_navigator = URLNavigator("Zingo_app/config.json")

def is_greeting(message):
    greetings = ["hi", "hello", "hey"]
    message_lower = message.lower().strip()
    return message_lower in greetings

def is_help_request(message):
    help_keywords = ["help", "assist", "support"]
    return any(keyword in message.lower() for keyword in help_keywords)

def home(request):
    if 'conversation_context' not in request.session:
        request.session['conversation_context'] = {
            "last_intent": None,
            "waiting_for_number": None,
            "last_message": "",
            "has_uploaded_file": False
        }
    return render(request, 'home.html')

@csrf_exempt
def chat(request):
    if request.method == "POST":
        if 'file' in request.FILES:
            file = request.FILES['file']
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            with temp_file as f:
                for chunk in file.chunks():
                    f.write(chunk)
            request.session['uploaded_file_path'] = temp_file.name
            request.session['uploaded_file_name'] = file.name
            request.session['conversation_context']['has_uploaded_file'] = True
            return JsonResponse({'response': f"Uploaded file: {file.name}. What do you want to do with it?"})

        data = json.loads(request.body)
        user_input = data.get('message', '').strip()
        if not user_input:
            return JsonResponse({'response': 'Hey, say something—I’m all ears!'})

        if 'conversation_context' not in request.session:
            request.session['conversation_context'] = {
                "last_intent": None,
                "waiting_for_number": None,
                "last_message": "",
                "has_uploaded_file": False
            }
        context = request.session['conversation_context']
        # Ensure has_uploaded_file is always present
        if 'has_uploaded_file' not in context:
            context['has_uploaded_file'] = False
            request.session['conversation_context'] = context
        print(f"User input: '{user_input}' with context: {context}")

        target_url, intent = url_navigator.detect_url_intent(user_input, context)
        print(f"Detected URL: {target_url}, Intent: {intent}")

        if target_url and intent in ["bg_creation", "lc_creation", "lc_view", "bg_amendment"]:
            response = CONFIG["responses"]["bg_prompt"] if "bg" in intent else CONFIG["responses"]["lc_prompt"]
            if intent == "lc_view":
                response = CONFIG["responses"]["lc_view_prompt"]
            context = {
                "last_intent": intent,
                "waiting_for_number": None,
                "last_message": user_input,
                "has_uploaded_file": context["has_uploaded_file"]
            }
            request.session['conversation_context'] = context
            return JsonResponse({'response': response, 'url': target_url, 'redirect': True})

        if intent == "bg_creation_with_file" and context.get("has_uploaded_file"):
            response = CONFIG["responses"]["bg_file_prompt"]
            file_path = request.session.get('uploaded_file_path')
            if file_path and os.path.exists(file_path):
                try:
                    payload = {'userName': 'Impactsure', 'userId': 'adminuser'}
                    with open(file_path, 'rb') as f:
                        files = {'file': (request.session['uploaded_file_name'], f)}
                        api_response = requests.post(target_url, data=payload, files=files, timeout=10)
                    api_response.raise_for_status()
                    result = api_response.json()
                    redirect_url = result.get('url')
                    if redirect_url:
                        context = {
                            "last_intent": intent,
                            "waiting_for_number": None,
                            "last_message": user_input,
                            "has_uploaded_file": False
                        }
                        request.session['conversation_context'] = context
                        del request.session['uploaded_file_path']
                        del request.session['uploaded_file_name']
                        os.unlink(file_path)
                        return JsonResponse({'response': response, 'url': redirect_url, 'redirect': True, 'process_file': True})
                except requests.RequestException as e:
                    if os.path.exists(file_path):
                        os.unlink(file_path)
                    return JsonResponse({'response': f"Oops, something went wrong processing the file: {str(e)}"})
            return JsonResponse({'response': "No file uploaded yet! Upload one first."})

        if intent == "bg_creation_pending_number":
            context = {
                "last_intent": "bg_creation",
                "waiting_for_number": "bg",
                "last_message": user_input,
                "has_uploaded_file": context["has_uploaded_file"]
            }
            request.session['conversation_context'] = context
            return JsonResponse({'response': CONFIG["responses"]["number_prompt"]})

        if intent == "lc_view_pending_number":
            context = {
                "last_intent": "lc_view",
                "waiting_for_number": "lc_view",
                "last_message": user_input,
                "has_uploaded_file": context["has_uploaded_file"]
            }
            request.session['conversation_context'] = context
            return JsonResponse({'response': CONFIG["responses"]["number_prompt"]})

        if intent == "bg_suggestion":
            context = {
                "last_intent": "bg_suggestion",
                "waiting_for_number": "bg",
                "last_message": user_input,
                "has_uploaded_file": context["has_uploaded_file"]
            }
            request.session['conversation_context'] = context
            return JsonResponse({'response': CONFIG["responses"]["bg_suggestion"]})

        if intent == "lc_suggestion":
            context = {
                "last_intent": "lc_suggestion",
                "waiting_for_number": None,
                "last_message": user_input,
                "has_uploaded_file": context["has_uploaded_file"]
            }
            request.session['conversation_context'] = context
            return JsonResponse({'response': CONFIG["responses"]["lc_suggestion"]})

        if is_greeting(user_input):
            context = {
                "last_intent": None,
                "waiting_for_number": None,
                "last_message": user_input,
                "has_uploaded_file": context["has_uploaded_file"]
            }
            request.session['conversation_context'] = context
            return JsonResponse({'response': CONFIG["responses"]["casual_hi"]})

        if is_help_request(user_input):
            context["last_intent"] = "help"
            context["last_message"] = user_input
            request.session['conversation_context'] = context
            return JsonResponse({'response': CONFIG["responses"]["casual_help"]})

        if context["last_message"]:
            full_input = f"{context['last_message']} {user_input}"
        else:
            full_input = user_input
        response = ollama_client.chat(full_input)
        if not response.strip():
            response = CONFIG["responses"]["unclear"]
        context = {
            "last_intent": "chat",
            "waiting_for_number": None,
            "last_message": user_input,
            "has_uploaded_file": context["has_uploaded_file"]
        }
        request.session['conversation_context'] = context
        return JsonResponse({'response': response})

    return JsonResponse({'error': 'Invalid request'}, status=400)