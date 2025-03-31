import webbrowser
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

    def detect_url_intent(self, message, context=None):
        message = message.lower().strip()
        print(f"Processing message: '{message}' with context: {context}")

        words = message.split()
        bg_number = None
        lc_number = None

        # BG Amendment
        amend_config = self.dynamic_urls.get("bg_amendment", {})
        if amend_config.get("trigger") in message:
            for i, word in enumerate(words):
                if word == "bg" and i + 1 < len(words):
                    bg_number = words[i + 1]
                    if bg_number in self.bg_mappings:
                        return f"{amend_config['base_url']}{self.bg_mappings[bg_number]}", "bg_amendment"
                    return f"{amend_config['base_url']}{bg_number}", "bg_amendment"

        # BG Creation for Existing Applicants
        bg_config = self.dynamic_urls.get("bg_creation", {})
        bg_triggers = bg_config.get("triggers", [])
        bg_base_url = bg_config.get("base_url")
        for trigger in bg_triggers:
            if trigger in message:
                if "number" in words:
                    number_idx = words.index("number")
                    if number_idx + 1 < len(words):
                        bg_number = words[number_idx + 1]
                elif "id" in words:
                    id_idx = words.index("id")
                    if id_idx + 1 < len(words):
                        bg_number = words[id_idx + 1]
                elif "bg" in words:
                    bg_idx = words.index("bg")
                    if bg_idx + 1 < len(words) and words[bg_idx + 1] not in ["is", "was", "a", "and", "the"]:
                        bg_number = words[bg_idx + 1]
                if bg_number:
                    if bg_number in self.bg_mappings:
                        return f"{bg_base_url}{self.bg_mappings[bg_number]}", "bg_creation"
                    return f"{bg_base_url}{bg_number}", "bg_creation"
                return bg_base_url, "bg_creation_pending_number"

        # BG Creation for New Applicants with File
        bg_file_config = self.dynamic_urls.get("bg_creation_with_file", {})
        bg_file_triggers = bg_file_config.get("triggers", [])
        bg_file_base_url = bg_file_config.get("base_url")
        for trigger in bg_file_triggers:
            if trigger in message and context and context.get("has_uploaded_file"):
                return bg_file_base_url, "bg_creation_with_file"

        # LC Creation
        lc_create_config = self.dynamic_urls.get("lc_creation", {})
        lc_create_triggers = lc_create_config.get("triggers", [])
        lc_create_base_url = lc_create_config.get("base_url")
        for trigger in lc_create_triggers:
            if trigger in message:
                return lc_create_base_url, "lc_creation"

        # LC View
        lc_view_config = self.dynamic_urls.get("lc_view", {})
        lc_view_triggers = lc_view_config.get("triggers", [])
        lc_view_base_url = lc_view_config.get("base_url")
        for trigger in lc_view_triggers:
            if trigger in message:
                if "lc" in words:
                    lc_idx = words.index("lc")
                    if lc_idx + 1 < len(words) and words[lc_idx + 1] not in ["is", "was", "a", "and", "the"]:
                        lc_number = words[lc_idx + 1]
                elif "number" in words:
                    number_idx = words.index("number")
                    if number_idx + 1 < len(words):
                        lc_number = words[number_idx + 1]
                elif "is" in words:
                    is_idx = words.index("is")
                    if is_idx + 1 < len(words):
                        lc_number = words[is_idx + 1]
                if not lc_number and words[-1] not in ["lc", "is", "was", "a", "and", "the", "on", "this"]:
                    lc_number = words[-1]
                if lc_number:
                    lc_number_lower = lc_number.lower()
                    if lc_number_lower in self.lc_mappings_lower:
                        return f"{lc_view_base_url}{self.lc_mappings_lower[lc_number_lower]}", "lc_view"
                    return f"{lc_view_base_url}{lc_number}", "lc_view"
                return lc_view_base_url, "lc_view_pending_number"

        # Context-based detection
        if context and context.get("waiting_for_number") == "bg":
            for word in words:
                if word not in ["bg", "bank", "guarantee", "is", "was", "a", "and", "the"]:
                    bg_number = word
                    break
            if bg_number:
                if bg_number in self.bg_mappings:
                    return f"{bg_base_url}{self.bg_mappings[bg_number]}", "bg_creation"
                return f"{bg_base_url}{bg_number}", "bg_creation"

        if context and context.get("waiting_for_number") == "lc_view":
            for word in words:
                if word not in ["lc", "letter", "of", "credit", "is", "was", "a", "and", "the"]:
                    lc_number = word
                    break
            if lc_number:
                lc_number_lower = lc_number.lower()
                if lc_number_lower in self.lc_mappings_lower:
                    return f"{lc_view_base_url}{self.lc_mappings_lower[lc_number_lower]}", "lc_view"
                return f"{lc_view_base_url}{lc_number}", "lc_view"

        if context and context.get("has_uploaded_file") and "bg" in message:
            return bg_file_base_url, "bg_creation_with_file"

        if "bg" in message or "bank guarantee" in message:
            return None, "bg_suggestion"
        if "lc" in message or "letter of credit" in message:
            return None, "lc_suggestion"

        print("No URL detected")
        return None, None