class Button:
    def __init__(self, text: str, callback_data: str, one_time_keyboard: bool = False, resize_keyboard: bool = True):
        self.text = text
        self.callback_data = callback_data
        self.one_time_keyboard = one_time_keyboard
        self.resize_keyboard = resize_keyboard
    
    def __str__(self):
        keyboard = {
            "keyboard": [
                [self.text]
            ],
            "resize_keyboard": self.resize_keyboard,
            "one_time_keyboard": self.one_time_keyboard
        }
        return keyboard

class InlineButton:
    def __init__(self, text: str, callback_data: str):
        self.text = text
        self.callback_data = callback_data
    
    def __str__(self):
        keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": self.text,
                        "callback_data": self.callback_data
                    }
                ]
            ]
        }
        return keyboard

class MarkupButton:
    def __init__(self, resize_keyboard: bool = True, one_time_keyboard: bool = False):
        self.keyboards = {
            "keyboard": [],
            "resize_keyboard": resize_keyboard,
            "one_time_keyboard": one_time_keyboard
        }
    
    def add(self, button: Button):
        self.keyboards["keyboard"].append([button.text])
    
    def get(self):
        return self.keyboards

class MarkupButton:
    def __init__(self, resize_keyboard: bool = True, one_time_keyboard: bool = False):
        self.keyboards = {
            "keyboard": [],
            "resize_keyboard": resize_keyboard,
            "one_time_keyboard": one_time_keyboard
        }
    
    def add(self, button: Button):
        self.keyboards["keyboard"].append([button.text])
    
    def get(self):
        return self.keyboards

class MarkupButtonInline:
    def __init__(self):
        self.keyboards = {
            "inline_keyboard": [],
        }
    
    def add(self, button: InlineButton):
        self.keyboards["inline_keyboard"].append([{"text": button.text, "callback_data": button.callback_data}])
    
    def get(self):
        return self.keyboards