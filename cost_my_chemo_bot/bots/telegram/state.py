import math

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from pydantic import BaseModel


class StateData(BaseModel):
    height: int | None = None
    weight: int | None = None
    category_id: str | None = None
    nosology_id: str | None = None
    course_id: str | None = None

    @property
    def bsa(self) -> float:
        assert self.height is not None and self.weight is not None
        return math.sqrt(self.height * self.weight / 3600)


# States
class Form(StatesGroup):
    height = State()
    weight = State()
    category = State()
    nosology = State()
    course = State()
    lead = State()


async def parse_state(state: FSMContext) -> StateData:
    data = await state.get_data()
    return StateData(**data)
