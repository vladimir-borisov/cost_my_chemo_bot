import asyncio
import decimal
import logging
import typing
import unicodedata
from collections import defaultdict

from google.oauth2.service_account import Credentials
from gspread_asyncio import AsyncioGspreadClientManager, AsyncioGspreadWorksheet
from pydantic import BaseModel, ValidationError

from cost_my_chemo_bot.config import SETTINGS

logger = logging.getLogger(__name__)


FIELDS_MAPPING = {
    "название курса": "name",
    "коэффициент": "coefficient",
    "подкатегория 1": "category",
    "нозология 1": "subcategory_1",
    "нозология 2": "subcategory_2",
    "нозология 3": "subcategory_3",
    "нозология 4": "subcategory_4",
    "нозология 5": "fixed_price",
}


class Course(BaseModel):
    id: int
    name: str
    coefficient: decimal.Decimal
    category: str
    subcategory_1: str
    subcategory_2: str
    subcategory_3: str
    subcategory_4: str
    fixed_price: bool

    def price(self, bsa: float) -> decimal.Decimal:
        if self.fixed_price:
            return self.coefficient

        return self.coefficient * decimal.Decimal(str(bsa)) * decimal.Decimal("0.6")


class DB:
    _courses: typing.ClassVar[list[Course] | None] = None
    _categories: typing.ClassVar[set[str] | None] = None
    _subcategories: typing.ClassVar[dict[str, set[str]] | None] = None
    loaded: typing.ClassVar[bool] = False

    def __init__(self):
        self.agcm = AsyncioGspreadClientManager(self.get_creds)

    @property
    def courses(self) -> list[Course]:
        assert DB.loaded
        return DB._courses

    @property
    def categories(self) -> set[str]:
        assert DB.loaded
        return DB._categories

    @property
    def subcategories(self) -> dict[str, set[str]]:
        assert DB.loaded
        return DB._subcategories

    @staticmethod
    def get_creds():
        creds = Credentials.from_service_account_file(SETTINGS.SERVICE_ACCOUNT_KEY)
        scoped = creds.with_scopes(
            [
                "https://www.googleapis.com/auth/spreadsheets",
            ]
        )
        return scoped

    @staticmethod
    def parse_courses(values: list[list]) -> list[Course]:
        courses: list[Course] = []
        if not values:
            return courses

        header = values[0]
        for i, row in enumerate(values[1:]):
            course = dict(zip(header, row))
            course = DB.map_course_fields(course)
            course["id"] = i
            course["fixed_price"] = bool(course.pop("fixed_price", False))
            course["coefficient"] = (
                course.pop("coefficient", "0").replace(",", ".").replace(" ", "")
            )
            try:
                parsed_course = Course(**course)
            except ValidationError:
                logger.exception("can't parse")
                continue
            courses.append(parsed_course)

        return courses

    @staticmethod
    def filter_empty_keys(values: list[list]) -> list[list]:
        filtered_list = []
        if not values:
            return filtered_list

        header = values[0]
        header = [key for key in header if key != ""]
        filtered_list.append(header)
        for row in values[1:]:
            row = row[: len(header) + 1]
            filtered_list.append(row)

        return filtered_list

    @staticmethod
    def map_course_fields(course: dict) -> dict:
        course_with_mapped_fields = {}
        for key in course:
            mapped_field = FIELDS_MAPPING.get(key)
            if not mapped_field:
                continue
            value = course[key]
            # normalize latin from sheets to unicode, mainly for coefficient's nbsps
            value = unicodedata.normalize("NFKD", value)
            course_with_mapped_fields[mapped_field] = value.replace("\n", " ")
        return course_with_mapped_fields

    async def _fetch_courses(self) -> list[Course]:
        agc = await self.agcm.authorize()
        spreadsheet = await agc.open_by_url(SETTINGS.SPREADSHEET_URL)

        general_spreadsheet: AsyncioGspreadWorksheet = (
            await spreadsheet.get_worksheet_by_id(SETTINGS.WORKSHEET_ID)
        )
        spreadsheet_values = await general_spreadsheet.get_all_values()
        filtered_values = self.filter_empty_keys(values=spreadsheet_values)
        return self.parse_courses(values=filtered_values)

    async def _fetch_categories(self) -> set[str]:
        categories = set()
        for course in DB._courses:
            categories.add(course.category)

        return categories

    async def _fetch_subcategories(self) -> dict[str, set[str]]:
        subcategories = defaultdict(set)
        for course in DB._courses:
            course_subcategories = [
                v for k, v in course if v and k.startswith("subcategory_")
            ]
            subcategories[course.category].update(course_subcategories)

        return dict(subcategories)

    async def load_db(self) -> None:
        logger.debug("loading db")
        if self.loaded:
            logger.debug("already loaded!")
            return

        DB._courses = await self._fetch_courses()
        DB._categories = await self._fetch_categories()
        DB._subcategories = await self._fetch_subcategories()
        DB.loaded = True
        logger.debug("loaded db successfully")

    async def find_courses(self, category: str, subcategory: str) -> list[Course]:
        found = []
        for course in self.courses:
            if course.category == category and subcategory in course.dict().values():
                found.append(course)

        return found

    async def find_course_by_name(self, name: str) -> Course:
        for course in self.courses:
            if course.name != name:
                continue
            return course


if __name__ == "__main__":
    db = DB()
    asyncio.run(db.load_db(), debug=True)
    print(db.courses)
    print(db.categories)
    print(db.subcategories)
