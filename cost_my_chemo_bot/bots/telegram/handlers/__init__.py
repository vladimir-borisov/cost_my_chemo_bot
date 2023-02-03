from aiogram import Dispatcher

from .back import back_handler, init_back_handlers
from .cancel import cancel_handler, init_cancel_handlers
from .category import init_category_handlers, process_category, process_category_invalid
from .course import init_course_handlers, process_course, process_course_invalid
from .height import init_height_handlers, process_height, process_height_invalid
from .lead import (
    init_lead_handlers,
    process_email,
    process_email_invalid,
    process_first_name,
    process_last_name,
    process_phone_number,
)
from .nosology import init_nosology_handlers, process_nosology, process_nosology_invalid
from .weight import init_weight_handlers, process_weight, process_weight_invalid
from .welcome import init_welcome_handlers, welcome_handler


def init_handlers(dp: Dispatcher):
    init_back_handlers(dp)
    init_cancel_handlers(dp)
    init_category_handlers(dp)
    init_height_handlers(dp)
    init_nosology_handlers(dp)
    init_weight_handlers(dp)
    init_lead_handlers(dp)
    init_welcome_handlers(dp)
    init_course_handlers(dp)


__all__ = (
    "back_handler",
    "cancel_handler",
    "process_category",
    "process_category_invalid",
    "process_course",
    "process_course_invalid",
    "process_height",
    "process_height_invalid",
    "init_lead_handlers",
    "process_first_name",
    "process_last_name",
    "process_email",
    "process_email_invalid",
    "process_phone_number",
    "process_nosology",
    "process_nosology_invalid",
    "process_weight",
    "process_weight_invalid",
    "welcome_handler",
)
