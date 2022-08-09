"""
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler, DisableAbleMessageHandler
from Cutiepii_Robot import LOGGER, CUTIEPII_PTB as app

from typing import Optional, List

from telegram.ext import Application, CallbackQueryHandler, CommandHandler, InlineQueryHandler, MessageHandler, filters
from telegram.ext.filters import BaseFilter


class Cutiepii_TG_Handler:
    def __init__(self, app):
        self.app: Application = app

    def command(
        self,
        command: str,
        filters: Optional[BaseFilter] = None,
        admin_ok: bool = False,
        pass_chat_data: bool = False,
        run_async: bool = True,
        can_disable: bool = True,
        group: Optional[int] = 40,
    ):
        def _command(func):
            try:
                if can_disable:
                    self.app.add_handler(
                        DisableAbleCommandHandler(
                            command,
                            func,
                            filters=filters,
                            admin_ok=admin_ok,
                        ),
                        group,
                    )
                else:
                    self.app.add_handler(
                        CommandHandler(
                            command,
                            func,
                            filters=filters,
                        ),
                        group,
                    )
                LOGGER.debug(
                    f"[CUTIEPII CMD] Loaded handler {command} for function {func.__name__} in group {group}"
                )
            except TypeError:
                if can_disable:
                    self.app.add_handler(
                        DisableAbleCommandHandler(
                            command,
                            func,
                            filters=filters,
                            admin_ok=admin_ok,
                            pass_chat_data=pass_chat_data,
                        )
                    )
                else:
                    self.app.add_handler(
                        CommandHandler(
                            command,
                            func,
                            filters=filters,
                            pass_chat_data=pass_chat_data,
                        )
                    )
                LOGGER.debug(
                    f"[CUTIEPII CMD] Loaded handler {command} for function {func.__name__}"
                )

            return func

        return _command

    def message(
        self,
        pattern: Optional[BaseFilter] = None,
        can_disable: bool = True,
        block: bool = True,
        group: Optional[int] = 60,
        friendly=None,
    ):
        def _message(func):
            try:
                if can_disable:
                    self.app.add_handler(
                        DisableAbleMessageHandler(pattern, func, friendly=friendly),
                        group,
                    )
                else:
                    self.app.add_handler(MessageHandler(pattern, func), group)
                LOGGER.debug(
                    f"[CUTIEPII MSG] Loaded filter pattern {pattern} for function {func.__name__} in group {group}"
                )
            except TypeError:
                if can_disable:
                    self.app.add_handler(
                        DisableAbleMessageHandler(pattern, func, friendly=friendly)
                    )
                else:
                    self.app.add_handler(MessageHandler(pattern, func))
                LOGGER.debug(
                    f"[CUTIEPII MSG] Loaded filter pattern {pattern} for function {func.__name__}"
                )

            return func

        return _message

    def callbackquery(self, pattern: str = None):
        def _callbackquery(func):
            self.app.add_handler(CallbackQueryHandler(pattern=pattern, callback=func))
            LOGGER.debug(
                f"[CUTIEPII CALLBACK] Loaded callbackquery handler with pattern {pattern} for function {func.__name__}"
            )
            return func

        return _callbackquery

    def inlinequery(
        self,
        pattern: Optional[str] = None,
#        run_async: bool = True,
        pass_user_data: bool = True,
        pass_chat_data: bool = True,
        chat_types: List[str] = None,
    ):
        def _inlinequery(func):
            self.app.add_handler(
                InlineQueryHandler(
                    pattern=pattern,
                    callback=func,
                    # pass_user_data=pass_user_data,
                    # pass_chat_data=pass_chat_data,
                    chat_types=chat_types,
                )
            )
            LOGGER.debug(
                f"[CUTIEPII INLINE] Loaded inlinequery handler with pattern {pattern} for function {func.__name__} | PASSES "
                f"USER DATA: {pass_user_data} | PASSES CHAT DATA: {pass_chat_data} | CHAT TYPES: {chat_types}"
            )
            return func

        return _inlinequery


cutiepii_cmd = Cutiepii_TG_Handler(app).command
cutiepii_msg = Cutiepii_TG_Handler(app).message
cutiepii_callback = Cutiepii_TG_Handler(app).callbackquery
cutiepii_inline = Cutiepii_TG_Handler(app).inlinequery

"""