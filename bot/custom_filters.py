import telegram
from telegram.ext.filters import UpdateFilter
from telegram import Update


class FilterIsPrivateChat(UpdateFilter):
    def filter(self, update: Update) -> bool:
        return update.effective_chat.type == telegram.constants.ChatType.PRIVATE
