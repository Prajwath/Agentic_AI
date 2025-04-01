from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
import tempfile
import os
from .url_navigator import URLNavigator

with open("Zingo_app/config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

url_navigator = URLNavigator("Zingo_app/config.json")

def is_hindi(text):
    return any(ord(char) >= 0x0900 and ord(char) <= 0x097F for char in text)

def is_greeting(message):
    greetings = ["hi", "hello", "hey", "हाय", "नमस्ते"]
    return any(g.lower() in message.lower() for g in greetings)

def is_help_request(message):
    help_keywords = ["help", "assist", "support", "मदद", "सहायता"]
    return any(keyword.lower() in message.lower() for keyword in help_keywords)

def home(request):
    if 'conversation_context' not in request.session:
        request.session['conversation_context'] = {
            "last_intent": None,
            "waiting_for_number": None,
            "last_message": "",
            "has_uploaded_file": False,
            "language_preference": "auto"
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
            context = request.session['conversation_context']
            use_hindi = context.get("language_preference") == "hindi" or (context.get("language_preference") == "auto" and is_hindi(context.get('last_message', '')))
            response = "फ़ाइल अपलोड हो गई: {}. इसके साथ क्या करना चाहते हैं?" .format(file.name) if use_hindi else f"Uploaded file: {file.name}. What do you want to do with it?"
            return JsonResponse({'response': response})

        data = json.loads(request.body)
        user_input = data.get('message', '').strip()
        if not user_input:
            context = request.session['conversation_context']
            use_hindi = context.get("language_preference") == "hindi" or (context.get("language_preference") == "auto" and is_hindi(user_input))
            response = 'हाय, कुछ कहें—मैं सुन रहा हूँ!' if use_hindi else 'Hey, say something—I’m all ears!'
            return JsonResponse({'response': response})

        if 'conversation_context' not in request.session:
            request.session['conversation_context'] = {
                "last_intent": None,
                "waiting_for_number": None,
                "last_message": "",
                "has_uploaded_file": False,
                "language_preference": "auto"
            }
        context = request.session['conversation_context']
        if 'has_uploaded_file' not in context:
            context['has_uploaded_file'] = False
        if 'language_preference' not in context:
            context['language_preference'] = "auto"
        print(f"User input: '{user_input}' with context: {context}")

        target_url, intent = url_navigator.detect_url_intent(user_input, context)
        print(f"Detected URL: {target_url}, Intent: {intent}")

        use_hindi = context["language_preference"] == "hindi" or (context["language_preference"] == "auto" and is_hindi(user_input))

        if intent == "invalid_ticket_number":
            response = "उल्लिखित टिकट नंबर नहीं मिला। कृपया सही टिकट नंबर दर्ज करें और पुनः प्रयास करें।" if use_hindi else "The mentioned ticket number is not found. Please enter the correct ticket number and try again."
            context.update({"last_intent": intent, "waiting_for_number": None, "last_message": user_input})
            request.session['conversation_context'] = context
            return JsonResponse({'response': response})

        if intent == "bg_creation_no_file":
            response = "कृपया पहले एक बीजी फ़ाइल अपलोड करें।" if use_hindi else "Please upload a BG file first."
            context.update({"last_intent": intent, "waiting_for_number": None, "last_message": user_input})
            request.session['conversation_context'] = context
            return JsonResponse({'response': response})

        # if intent == "lc_creation_no_file":
        #     response = "कृपया पहले एक एलसी फ़ाइल अपलोड करें।" if use_hindi else "Please upload an LC file first."
        #     context.update({"last_intent": intent, "waiting_for_number": None, "last_message": user_input})
        #     request.session['conversation_context'] = context
        #     return JsonResponse({'response': response})

        if target_url and intent in ["view_bg", "lc_creation", "lc_view", "bg_amendment"]:
            if intent == "view_bg":
                response = "ठीक है, आपका बीजी एक नई टैब में खोल दिया गया है!" if use_hindi else "Alright, I’ve got your Bank Guarantee lined up in a new tab for you!"
            elif intent == "lc_view":
                response = "ठीक है, आपका एलसी विवरण एक नई टैब में खोल दिया गया है!" if use_hindi else "Got it, pulling up your LC details in a new tab!"
            elif intent == "lc_creation":
                response = "ठीक है, आपका नया एलसी एक नई टैब में तैयार हो रहा है!" if use_hindi else "Got it, your new LC is being prepared in a new tab!"
            else:  # bg_amendment
                response = "ठीक है, आपका बीजी संशोधन एक नई टैब में खोल दिया गया है!" if use_hindi else CONFIG["responses"]["bg_prompt"]
            context.update({"last_intent": intent, "waiting_for_number": None, "last_message": user_input})
            request.session['conversation_context'] = context
            return JsonResponse({'response': response, 'url': target_url, 'redirect': True})

        if intent == "bg_creation_with_file" and context.get("has_uploaded_file"):
            response = "ठीक है, आपकी बीजी फ़ाइल प्रोसेस हो रही है और एक नई टैब में खोली जाएगी!" if use_hindi else CONFIG["responses"]["bg_file_prompt"]
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
                        context.update({"last_intent": intent, "waiting_for_number": None, "last_message": user_input, "has_uploaded_file": False})
                        request.session['conversation_context'] = context
                        del request.session['uploaded_file_path']
                        del request.session['uploaded_file_name']
                        os.unlink(file_path)
                        return JsonResponse({'response': response, 'url': redirect_url, 'redirect': True, 'process_file': True})
                except requests.RequestException as e:
                    if os.path.exists(file_path):
                        os.unlink(file_path)
                    error_response = f"फ़ाइल प्रोसेसिंग में कुछ गड़बड़ हुई: {str(e)}" if use_hindi else f"Oops, something went wrong processing the file: {str(e)}"
                    return JsonResponse({'response': error_response})
            return JsonResponse({'response': "कोई फ़ाइल अभी तक अपलोड नहीं हुई! पहले एक अपलोड करें।" if use_hindi else "No file uploaded yet! Upload one first."})

        if intent == "lc_creation_with_file" and context.get("has_uploaded_file"):
            response = "ठीक है, आपकी एलसी फ़ाइल प्रोसेस हो रही है और एक नई टैब में खोली जाएगी!" if use_hindi else "Alright, your LC file is being processed and will open in a new tab!"
            file_path = request.session.get('uploaded_file_path')
            if file_path and os.path.exists(file_path):
                try:
                    payload = {'userName': 'Impactsure', 'userId': 'adminuser'}
                    with open(file_path, 'rb') as f:
                        files = {'file': (request.session['uploaded_file_name'], f)}
                        api_response = requests.post(target_url, data=payload, files=files, timeout=10)
                    api_response.raise_for_status()
                    result = api_response.json()
                    redirect_url = result.get('url', target_url)  # Use target_url if no redirect URL in response
                    context.update({"last_intent": intent, "waiting_for_number": None, "last_message": user_input, "has_uploaded_file": False})
                    request.session['conversation_context'] = context
                    del request.session['uploaded_file_path']
                    del request.session['uploaded_file_name']
                    os.unlink(file_path)
                    return JsonResponse({'response': response, 'url': redirect_url, 'redirect': True, 'process_file': True})
                except requests.RequestException as e:
                    if os.path.exists(file_path):
                        os.unlink(file_path)
                    error_response = f"फ़ाइल प्रोसेसिंग में कुछ गड़बड़ हुई: {str(e)}" if use_hindi else f"Oops, something went wrong processing the file: {str(e)}"
                    return JsonResponse({'response': error_response})
            return JsonResponse({'response': "कोई फ़ाइल अभी तक अपलोड नहीं हुई! पहले एक अपलोड करें।" if use_hindi else "No file uploaded yet! Upload one first."})

        if intent == "view_bg_pending_number":
            response = "कृपया बीजी नंबर बताएं।" if use_hindi else CONFIG["responses"]["number_prompt"]
            context.update({"last_intent": "view_bg", "waiting_for_number": "view_bg", "last_message": user_input})
            request.session['conversation_context'] = context
            return JsonResponse({'response': response})

        if intent == "lc_view_pending_number":
            response = "कृपया एलसी नंबर बताएं।" if use_hindi else CONFIG["responses"]["number_prompt"]
            context.update({"last_intent": "lc_view", "waiting_for_number": "lc_view", "last_message": user_input})
            request.session['conversation_context'] = context
            return JsonResponse({'response': response})

        if intent == "bg_suggestion":
            response = "क्या आप बीजी बनाना चाहते हैं या मौजूदा बीजी देखना चाहते हैं? मुझे और बताएं।" if use_hindi else CONFIG["responses"]["bg_suggestion"]
            context.update({"last_intent": "bg_suggestion", "waiting_for_number": "view_bg", "last_message": user_input})
            request.session['conversation_context'] = context
            return JsonResponse({'response': response})

        if intent == "lc_suggestion":
            response = "क्या आप एलसी बनाना चाहते हैं या मौजूदा एलसी देखना चाहते हैं? मुझे और बताएं।" if use_hindi else CONFIG["responses"]["lc_suggestion"]
            context.update({"last_intent": "lc_suggestion", "waiting_for_number": None, "last_message": user_input})
            request.session['conversation_context'] = context
            return JsonResponse({'response': response})

        if is_greeting(user_input):
            response = "नमस्ते! आप आज कैसे हैं?" if use_hindi else CONFIG["responses"]["casual_hi"]
            context.update({"last_intent": None, "waiting_for_number": None, "last_message": user_input})
            request.session['conversation_context'] = context
            return JsonResponse({'response': response})

        if is_help_request(user_input):
            response = "मदद चाहिए? मुझे बताएं कि मैं आपकी कैसे सहायता कर सकता हूँ!" if use_hindi else CONFIG["responses"]["casual_help"]
            context.update({"last_intent": "help", "last_message": user_input})
            request.session['conversation_context'] = context
            return JsonResponse({'response': response})

        response = "मुझे समझ नहीं आया। कृपया और स्पष्ट करें।" if use_hindi else CONFIG["responses"]["unclear"]
        context.update({"last_intent": "chat", "waiting_for_number": None, "last_message": user_input})
        request.session['conversation_context'] = context
        return JsonResponse({'response': response})

    return JsonResponse({'error': 'Invalid request'}, status=400)