from typing import Optional

class AioTeleError(Exception):
    """
    Base exception for all aiogram errors.
    """


class DetailedAioTeleError(AioTeleError):
    """
    Base exception for all aiogram errors with detailed message.
    """

    url: Optional[str] = None

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        message = self.message
        if self.url:
            message += f"\n(background on this error at: {self.url})"
        return message

    def __repr__(self) -> str:
        return f"{type(self).__name__}('{self}')"

class TelegramAPIError(DetailedAioTeleError):
    """
    Base exception for all Telegram API errors.
    """
    
    label: str = "Telegram server says"
    
    def __init__(self, message: str) -> None:
        super().__init__(message=message)
    
    def __str__(self) -> str:
        original_message = super().__str__()
        return f"{self.label} - {original_message}"

class TelegramBadRequest(TelegramAPIError):
    """
    The standard exception for TelegramBadRequest errors with a description
    """

class ValidationError(DetailedAioTeleError):
    """
    Input data validation error.
    """

class TelegramConflictError(TelegramAPIError):
    """
    The standard exception for TelegramConflictError errors with a description
    """

class TelegramNetworkError(DetailedAioTeleError):
    """
    Network communication error.
    """
