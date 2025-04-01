import re
import json

class URLNavigator:
    def __init__(self, config_path="Zingo_app/config.json"):
        with open(config_path, 'r', encoding="utf-8") as f:
            config = json.load(f)
        self.static_urls = config["urls"]["static"]
        self.dynamic_urls = config["urls"]["dynamic"]
        self.bg_mappings = config.get("bg_mappings", {})
        self.lc_mappings = config.get("lc_mappings", {})
        self.lc_mappings_lower = {k.lower(): v for k, v in self.lc_mappings.items()}
        self.lc_num_regex = re.compile(r'(?P<lc_num>[0-9A-z\/-]*([A-Z]+[\/]*[0-9-]+|[A-Z]*[\/]*[0-9-]{5}))', re.IGNORECASE)

    def detect_url_intent(self, message, context=None):
        message = message.strip()  # Don't lowercase to preserve Hindi
        print(f"Processing message: '{message}' with context: {context}")

        words = message.split()
        bg_number = None
        lc_number = None

        # Check for single-word input or direct LC number (e.g., from LC amendment input)
        if len(words) == 1:
            number = words[0]
            if self.lc_num_regex.match(number):
                if number in self.bg_mappings:
                    return f"{self.dynamic_urls['view_bg']['base_url']}{self.bg_mappings[number]}", "view_bg"
                elif number.lower() in self.lc_mappings_lower:
                    return f"{self.dynamic_urls['lc_view']['base_url']}{self.lc_mappings_lower[number.lower()]}", "lc_view"
                else:
                    return None, "invalid_ticket_number"

        # Check for "ticket" or "टिकट" followed by a potential number
        ticket_keywords = ["ticket", "टिकट"]
        for ticket_key in ticket_keywords:
            if ticket_key in words:
                ticket_idx = words.index(ticket_key)
                if ticket_idx + 1 < len(words):
                    potential_number = words[ticket_idx + 1]
                    if self.lc_num_regex.match(potential_number):
                        if potential_number in self.bg_mappings:
                            return f"{self.dynamic_urls['view_bg']['base_url']}{self.bg_mappings[potential_number]}", "view_bg"
                        elif potential_number.lower() in self.lc_mappings_lower:
                            return f"{self.dynamic_urls['lc_view']['base_url']}{self.lc_mappings_lower[potential_number.lower()]}", "lc_view"
                        else:
                            return None, "invalid_ticket_number"
                    else:
                        return None, "invalid_ticket_number"

        # Check for BG number in multi-word input
        for word in words:
            if word in self.bg_mappings:
                bg_number = word
                return f"{self.dynamic_urls['view_bg']['base_url']}{self.bg_mappings[bg_number]}", "view_bg"

        # Check for LC number in multi-word input
        for word in words:
            if word.lower() in self.lc_mappings_lower:
                lc_number = word
                return f"{self.dynamic_urls['lc_view']['base_url']}{self.lc_mappings_lower[lc_number.lower()]}", "lc_view"

        # BG Amendment
        amend_config = self.dynamic_urls.get("bg_amendment", {})
        if amend_config.get("trigger") in message:
            for i, word in enumerate(words):
                if word == "bg" and i + 1 < len(words):
                    bg_number = words[i + 1]
                    if self.lc_num_regex.match(bg_number):
                        if bg_number in self.bg_mappings:
                            return f"{amend_config['base_url']}{self.bg_mappings[bg_number]}", "bg_amendment"
                        return None, "invalid_ticket_number"
                    return None, "invalid_ticket_number"

        # View BG with triggers (English and Hindi)
        view_bg_config = self.dynamic_urls.get("view_bg", {})
        view_bg_triggers = view_bg_config.get("triggers", []) + ["बीजी देखें"]
        view_bg_base_url = view_bg_config.get("base_url")
        for trigger in view_bg_triggers:
            if trigger in message:
                if "number" in words or "नंबर" in words:
                    number_idx = words.index("number") if "number" in words else words.index("नंबर")
                    if number_idx + 1 < len(words):
                        bg_number = words[number_idx + 1]
                elif "id" in words:
                    id_idx = words.index("id")
                    if id_idx + 1 < len(words):
                        bg_number = words[id_idx + 1]
                elif "bg" in words or "बीजी" in words:
                    bg_idx = words.index("bg") if "bg" in words else words.index("बीजी")
                    if bg_idx + 1 < len(words) and words[bg_idx + 1] not in ["is", "was", "a", "and", "the", "है"]:
                        bg_number = words[bg_idx + 1]
                if bg_number and self.lc_num_regex.match(bg_number):
                    if bg_number in self.bg_mappings:
                        return f"{view_bg_base_url}{self.bg_mappings[bg_number]}", "view_bg"
                    return None, "invalid_ticket_number"
                if bg_number:
                    return None, "invalid_ticket_number"
                return view_bg_base_url, "view_bg_pending_number"

        # LC View with triggers (English and Hindi)
        lc_view_config = self.dynamic_urls.get("lc_view", {})
        lc_view_triggers = lc_view_config.get("triggers", []) + ["एलसी देखें", "i want to view my lc"]
        lc_view_base_url = lc_view_config.get("base_url")
        for trigger in lc_view_triggers:
            if trigger in message.lower():  # Case-insensitive for English triggers
                if "lc" in words or "एलसी" in words:
                    lc_idx = words.index("lc") if "lc" in words else words.index("एलसी")
                    if lc_idx + 1 < len(words) and words[lc_idx + 1] not in ["is", "was", "a", "and", "the", "है"]:
                        lc_number = words[lc_idx + 1]
                elif "number" in words or "नंबर" in words:
                    number_idx = words.index("number") if "number" in words else words.index("नंबर")
                    if number_idx + 1 < len(words):
                        lc_number = words[number_idx + 1]
                elif "is" in words or "है" in words:
                    is_idx = words.index("is") if "is" in words else words.index("है")
                    if is_idx + 1 < len(words):
                        lc_number = words[is_idx + 1]
                elif trigger == "i want to view my lc" and len(words) > 5:  # Check for LC number after "i want to view my lc"
                    lc_number = words[-1]  # Assume last word is the LC number
                if not lc_number and words[-1] not in ["lc", "एलसी", "is", "है", "was", "a", "and", "the", "on", "this"]:
                    lc_number = words[-1]
                if lc_number and self.lc_num_regex.match(lc_number):
                    lc_number_lower = lc_number.lower()
                    if lc_number_lower in self.lc_mappings_lower:
                        return f"{lc_view_base_url}{self.lc_mappings_lower[lc_number_lower]}", "lc_view"
                    return None, "invalid_ticket_number"
                if lc_number:
                    return None, "invalid_ticket_number"
                return lc_view_base_url, "lc_view_pending_number"

        # BG Creation with File (English and Hindi triggers)
        bg_file_config = self.dynamic_urls.get("bg_creation_with_file", {})
        bg_file_triggers = bg_file_config.get("triggers", []) + [
            "create bg with file", "i want to create a new bg",
            "मैं एक नया बीजी बनाना चाहता हूँ", "नया बीजी बनाएं", "मैं एक नया बिजी बनाना चाहता हूं", "यह फाइल को लेकर एक नया बिजी बनाया", "मुझे एक नया बिजी बना कर दो"
        ]
        bg_file_base_url = bg_file_config.get("base_url")
        for trigger in bg_file_triggers:
            if trigger in message.lower():
                if context and context.get("has_uploaded_file"):
                    return bg_file_base_url, "bg_creation_with_file"
                return None, "bg_creation_no_file"

        # # LC Creation with File (English and Hindi triggers)
        # lc_file_config = self.dynamic_urls.get("lc_creation_with_file", {})
        # lc_file_triggers = lc_file_config.get("triggers", []) + [
        #     "create lc with file", "i want to create a new lc",
        #     "मैं एक नया एलसी बनाना चाहता हूँ", "नया एलसी बनाएं"
        # ]
        # lc_file_base_url = lc_file_config.get("base_url")
        # for trigger in lc_file_triggers:
        #     if trigger in message.lower():
        #         if context and context.get("has_uploaded_file"):
        #             return lc_file_base_url, "lc_creation_with_file"
        #         return None, "lc_creation_no_file"

        # LC Creation without file (English and Hindi triggers)
        lc_create_config = self.dynamic_urls.get("lc_creation", {})
        lc_create_triggers = lc_create_config.get("triggers", []) + ["मैं एक नया एलसी बनाना चाहता हूँ", "नया एलसी बनाएं", "मैं एक नया लक बनाना चाहता हूं","नया लक बनाएं", "नया लक बनाया"]
        lc_create_base_url = lc_create_config.get("base_url")
        for trigger in lc_create_triggers:
            if trigger in message:
                return lc_create_base_url, "lc_creation"

        # Context-based detection for pending numbers
        if context and context.get("waiting_for_number") == "view_bg":
            for word in words:
                if word not in ["bg", "बीजी", "bank", "guarantee", "is", "है", "was", "a", "and", "the"]:
                    bg_number = word
                    break
            if bg_number and self.lc_num_regex.match(bg_number):
                if bg_number in self.bg_mappings:
                    return f"{view_bg_base_url}{self.bg_mappings[bg_number]}", "view_bg"
                return None, "invalid_ticket_number"
            if bg_number:
                return None, "invalid_ticket_number"

        if context and context.get("waiting_for_number") == "lc_view":
            for word in words:
                if word not in ["lc", "एलसी", "letter", "of", "credit", "is", "है", "was", "a", "and", "the"]:
                    lc_number = word
                    break
            if lc_number and self.lc_num_regex.match(lc_number):
                lc_number_lower = lc_number.lower()
                if lc_number_lower in self.lc_mappings_lower:
                    return f"{lc_view_base_url}{self.lc_mappings_lower[lc_number_lower]}", "lc_view"
                return None, "invalid_ticket_number"
            if lc_number:
                return None, "invalid_ticket_number"

        if context and context.get("has_uploaded_file") and ("bg" in message or "बीजी" in message):
            return bg_file_base_url, "bg_creation_with_file"

        # if context and context.get("has_uploaded_file") and ("lc" in message or "एलसी" in message):
        #     return lc_file_base_url, "lc_creation_with_file"

        if "bg" in message or "bank guarantee" in message or "बीजी" in message:
            return None, "bg_suggestion"
        if "lc" in message or "letter of credit" in message or "एलसी" in message:
            return None, "lc_suggestion"

        print("No URL detected")
        return None, None