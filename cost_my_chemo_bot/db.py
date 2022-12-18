import asyncio
import logging
import typing
import unicodedata
from collections import defaultdict

from google.oauth2.service_account import Credentials
from gspread_asyncio import AsyncioGspreadClientManager, AsyncioGspreadWorksheet

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


class DB:
    _courses: typing.ClassVar[list[dict] | None] = None
    _categories: typing.ClassVar[set[str] | None] = None
    _subcategories: typing.ClassVar[dict[str, set[str]] | None] = None
    loaded: typing.ClassVar[bool] = False

    def __init__(self):
        self.agcm = AsyncioGspreadClientManager(self.get_creds)

    @property
    def courses(self) -> list[dict]:
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
    def parse_courses(values: list[list]) -> list[dict]:
        courses: list[dict] = []
        if not values:
            return courses

        header = values[0]
        for row in values[1:]:
            courses.append(dict(zip(header, row)))

        courses_with_mapped_fields = []
        for course in courses:
            course_with_mapped_fields = {}
            for key in course:
                mapped_field = FIELDS_MAPPING.get(key)
                if not mapped_field:
                    continue
                course_with_mapped_fields[mapped_field] = course[key]
            courses_with_mapped_fields.append(course_with_mapped_fields)

        return courses_with_mapped_fields

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
    def normalize_courses_strings(courses: list[dict]) -> list[dict]:
        normalized_courses: list[dict] = []
        for course in courses:
            normalized_course = {}
            for k, v in course.items():
                normalized_course[
                    unicodedata.normalize("NFKD", k)
                ] = unicodedata.normalize("NFKD", v)
            normalized_courses.append(normalized_course)

        return normalized_courses

    async def _fetch_courses(self) -> list[dict]:
        agc = await self.agcm.authorize()
        spreadsheet = await agc.open_by_url(SETTINGS.SPREADSHEET_URL)

        general_spreadsheet: AsyncioGspreadWorksheet = (
            await spreadsheet.get_worksheet_by_id(SETTINGS.WORKSHEET_ID)
        )
        spreadsheet_values = await general_spreadsheet.get_all_values()
        filtered_values = self.filter_empty_keys(values=spreadsheet_values)
        courses = self.parse_courses(values=filtered_values)
        courses = self.normalize_courses_strings(courses=courses)

        return courses

    async def _fetch_categories(self) -> set[str]:
        categories = set()
        for course in DB._courses:
            categories.add(course["category"])

        return categories

    async def _fetch_subcategories(self) -> dict[str, set[str]]:
        subcategories = defaultdict(set)
        for course in DB._courses:
            course_copy = course.copy()
            course_subcategories = [
                v for k, v in course_copy.items() if v and k.startswith("subcategory_")
            ]
            subcategories[course["category"]].update(course_subcategories)

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

    async def find_courses(self, category: str, subcategory: str) -> list[dict]:
        found = []
        for course in self.courses:
            course_copy = course.copy()
            if course["category"] == category and subcategory in course_copy.values():
                found.append(course)

        return found

    async def find_course_by_name(self, name: str) -> dict:
        for course in self.courses:
            if course["name"] != name:
                continue
            return course


if __name__ == "__main__":
    db = DB()
    asyncio.run(db.load_db(), debug=True)
    print(db.courses)
    print(db.categories)
    print(db.subcategories)
