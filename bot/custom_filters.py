import telegram
from telegram import Update
from telegram.ext.filters import UpdateFilter


class FilterIsPrivateChat(UpdateFilter):
    def filter(self, update: Update) -> bool:
        return update.effective_chat.type == telegram.constants.ChatType.PRIVATE


class FilterRepliedTo(UpdateFilter):
    def filter(self, update: Update) -> bool:
        return update.effective_message.reply_to_message is not None
