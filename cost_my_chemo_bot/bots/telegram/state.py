import math

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from pydantic import BaseModel, EmailStr


class StateData(BaseModel):
    height: int | None = None
    weight: int | None = None
    category_id: str | None = None
    category_name: str | None = None
    nosology_id: str | None = None
    nosology_name: str | None = None
    course_id: str | None = None
    is_custom_course: bool | None = None
    course_name: str | None = None
    course_price: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone_number: str | None = None

    @property
    def is_accompanying_therapy(self) -> bool:
        return self.category_id == "e11397b4-8229-11ed-810b-002590c014a5"

    @property
    def bsa(self) -> float:
        assert self.height is not None and self.weight is not None
        return math.sqrt(self.height * self.weight / 3600)


# States
class Form(StatesGroup):
    welcome = State()
    start = State()
    height = State()
    weight = State()
    category = State()
    nosology = State()
    course = State()
    custom_course = State()
    data_confirmation = State()
    contacts_input = State()
    first_name = State()
    last_name = State()
    email = State()
    phone_number = State()
    lead_confirmation = State()


async def parse_state(state: FSMContext) -> StateData:
    data = await state.get_data()
    return StateData(**data)
