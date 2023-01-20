import decimal

import aiogram.utils.markdown as md

from cost_my_chemo_bot.db import Category, Course, Nosology

GOODBYE = "До свидания!"
WELCOME = "Здравствуйте, {full_name}!\n" "Я помогу рассчитать стоимость курса лечения\n"
HEIGHT_INPUT = "Введите ваш рост"
HEIGHT_WRONG = "Введите число"
WEIGHT_INPUT = "Введите ваш вес"
WEIGHT_WRONG = "Введите число"
CATEGORY_CHOOSE = "Выберите раздел"
CATEGORY_WRONG = "Неверно выбрана раздел. Выберите раздел на клавиатуре."
NOSOLOGY_CHOOSE = "Выберите подраздел"
NOSOLOGY_WRONG = "Неверно выбрана подраздел. Выберите подраздел на клавиатуре."
COURSE_CHOOSE = "Выберите курс"
COURSE_WRONG = "Неверно выбран курс. Выберите курс на клавиатуре."
LEAD_FIRST_NAME = "Введите ваше имя"
LEAD_LAST_NAME = "Введите вашу фамилию"
LEAD_EMAIL = "Введите ваш email"
LEAD_EMAIL_WRONG = "Неверно введен email. Введите email."
LEAD_PHONE_NUMBER = "Введите ваш номер телефона"
LEAD_PHONE_NUMBER_WRONG = "Неверно введен номер телефона. Введите номер телефона."
THANKS = "Спасибо!"


def course_selected(
    height: int,
    weight: int,
    category: Category,
    nosology: Nosology,
    course: Course,
    course_price: decimal.Decimal,
) -> str:
    return md.text(
        md.text("Рост:", md.bold(height)),
        md.text("Вес:", md.code(weight)),
        md.text("Категория:", md.italic(category.categoryName)),
        md.text("Подкатегория:", md.italic(nosology.nosologyName)),
        md.text("Курс:", course.Course),
        md.text("Цена:", f"{course_price:.2f}".replace(".", ",")),
        sep="\n",
    )
