import asyncio
import decimal
import typing
import unicodedata

from httpx import AsyncClient
from logfmt_logger import getLogger
from pydantic import BaseModel, ValidationError, validator

from cost_my_chemo_bot.config import SETTINGS

logger = getLogger(__name__, level=SETTINGS.LOG_LEVEL)


class CategoryNotFound(Exception):
    ...


class NosologyNotFound(Exception):
    ...


class CourseNotFound(Exception):
    ...


class Category(BaseModel):
    categoryid: str
    categoryName: str


class Nosology(BaseModel):
    nosologyid: str
    nosologyName: str
    categoryid1: str | None


class Course(BaseModel):
    Courseid: str
    Course: str
    categoryid: str
    coefficient: decimal.Decimal
    nosologyid1: str
    nosologyid2: str
    nosologyid3: str
    nosologyid4: str
    nosologyid5: str
    fixPrice: bool

    @validator("coefficient", pre=True)
    def normalize_coefficient(cls, v: typing.Any) -> decimal.Decimal:
        if isinstance(v, str):
            normalized = unicodedata.normalize("NFKD", v)
            normalized = normalized.replace(" ", "").replace(",", "")
            try:
                return decimal.Decimal(normalized)
            except decimal.InvalidOperation:
                logger.exception("can't parse coefficient, raw value: %s", normalized)
                return decimal.Decimal("0")

        return v

    def price(self, bsa: float) -> decimal.Decimal:
        if self.fixPrice:
            return self.coefficient

        return self.coefficient * decimal.Decimal(str(bsa)) * decimal.Decimal("0.75")


class DB:
    _courses: typing.ClassVar[list[Course] | None] = None
    _categories: typing.ClassVar[list[Category] | None] = None
    _nosologies: typing.ClassVar[list[Nosology] | None] = None
    loaded: typing.ClassVar[bool] = False
    client = AsyncClient(
        base_url=SETTINGS.ONCO_MEDCONSULT_API_URL,
        auth=(
            SETTINGS.ONCO_MEDCONSULT_API_LOGIN,
            SETTINGS.ONCO_MEDCONSULT_API_PASSWORD.get_secret_value(),
        ),
        headers={"Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"},
    )

    @property
    def courses(self) -> list[Course]:
        assert DB.loaded
        return DB._courses

    @property
    def categories(self) -> list[Category]:
        assert DB.loaded
        return DB._categories

    @property
    def nosologies(self) -> list[Nosology]:
        assert DB.loaded
        return DB._nosologies

    @staticmethod
    def parse_courses(values: list[list]) -> list[Course]:
        courses: list[Course] = []
        if not values:
            return courses

        header = values[0]
        for i, row in enumerate(values[1:]):
            course = dict(zip(header, row))
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

    async def _fetch_courses(self) -> list[Course]:
        resp = await self.client.get("", params={"action": "Course"})
        resp.raise_for_status()
        result = resp.json()["result"]
        return [Course(**course_raw) for course_raw in result]

    async def _fetch_categories(self) -> list[Category]:
        resp = await self.client.get("", params={"action": "category"})
        resp.raise_for_status()
        result = resp.json()["result"]
        return [Category(**category_raw) for category_raw in result]

    async def _fetch_nosologies(self) -> list[Nosology]:
        resp = await self.client.get("", params={"action": "nosology"})
        resp.raise_for_status()
        result = resp.json()["result"]
        return [Nosology(**nosology_raw) for nosology_raw in result]

    async def load_db(self) -> None:
        logger.debug("loading db")
        if DB.loaded:
            logger.debug("already loaded!")
            return

        DB._courses = await self._fetch_courses()
        DB._categories = await self._fetch_categories()
        DB._nosologies = await self._fetch_nosologies()
        DB.loaded = True
        logger.debug("loaded db successfully")

    async def reload_db(self) -> None:
        logger.debug("reloading db")
        DB.loaded = False
        await self.load_db()

    async def find_courses(
        self, category_id: str, nosology_id: str | None
    ) -> list[Course]:
        await self.reload_db()
        if nosology_id is None:
            return [
                course for course in self.courses if course.categoryid == category_id
            ]

        found = []
        for course in self.courses:
            if course.categoryid == category_id and (
                course.nosologyid1 == nosology_id
                or course.nosologyid2 == nosology_id
                or course.nosologyid3 == nosology_id
                or course.nosologyid4 == nosology_id
                or course.nosologyid5 == nosology_id
            ):
                found.append(course)

        return found

    async def find_course_by_name(self, name: str) -> Course:
        for course in self.courses:
            if course.Course != name:
                continue
            return course

        raise CourseNotFound(f"no such course: {name}")

    async def find_course_by_id(self, course_id: str) -> Course:
        for course in self.courses:
            if course.Courseid != course_id:
                continue
            return course

        raise CourseNotFound(f"no such course: {course_id}")

    async def find_category_by_id(self, category_id: str) -> Category:
        for category in self.categories:
            if category.categoryid != category_id:
                continue
            return category

        raise CategoryNotFound(f"no such category: {category_id}")

    async def find_nosology_by_id(self, nosology_id: str) -> Nosology:
        await self.reload_db()

        for nosology in self.nosologies:
            if nosology.nosologyid != nosology_id:
                continue
            return nosology

        raise NosologyNotFound(f"no such nosology: {nosology_id}")

    async def find_nosologies_by_category_id(self, category_id: str) -> list[Nosology]:
        return [
            nosology
            for nosology in self.nosologies
            if nosology.categoryid1 == category_id
        ]

    @classmethod
    async def close(cls):
        await cls.client.aclose()


if __name__ == "__main__":
    db = DB()
    asyncio.run(db.load_db(), debug=True)
    print(db.courses)
    print(db.categories)
    print(db.nosologies)
    print(db.categories[0].categoryid)
    print(
        asyncio.run(
            db.find_nosologies_by_category_id(category_id=db.categories[0].categoryid)
        )
    )
