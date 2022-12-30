"""
This module has mongo storage for finite-state machine
    based on `motor <https://github.com/mongodb/motor>`_ driver
"""

import asyncio
from typing import AnyStr, Dict, List, Optional, Tuple, Union

try:
    from google.cloud import firestore
except ModuleNotFoundError as e:
    import warnings

    warnings.warn("Install motor with `pip install google-cloud-firestore`")
    raise e

from aiogram.dispatcher.storage import BaseStorage

# from aiogram.contrib.fsm_storage.mongo import MongoStorage

STATE = "aiogram_state"
DATA = "aiogram_data"
BUCKET = "aiogram_bucket"
COLLECTIONS = (STATE, DATA, BUCKET)


class FirestoreStorage(BaseStorage):
    """
    Firestore-based storage for FSM.

    Usage:

    .. code-block:: python3

        storage = FirestoreStorage(host='localhost', port=27017, db_name='aiogram_fsm')
        dp = Dispatcher(bot, storage=storage)

    And need to close Mongo client connections when shutdown

    .. code-block:: python3

        await dp.storage.close()
        await dp.storage.wait_closed()
    """

    def __init__(self, db_name="aiogram_fsm"):
        self._db_name: str = db_name
        self._db: Optional[firestore.Client] = firestore.Client()

        # self._index = index

    @staticmethod
    async def apply_index(db: firestore.Client):
        for collection in COLLECTIONS:
            db.collection(collection).create_index(
                keys=[("chat", 1), ("user", 1)],
                name="chat_user_idx",
                unique=True,
                background=True,
            )

    async def close(self):
        if self._db:
            self._db.close()

    async def wait_closed(self):
        return True

    async def set_state(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        state: Optional[AnyStr] = None,
    ):
        chat, user = self.check_address(chat=chat, user=user)
        db = self._db

        if state is None:
            result = (
                db.collection(STATE)
                .where("user", "==", user)
                .where("chat", "==", chat)
                .stream()
            )
            for r in result:
                print(r)
        else:
            db.collection(STATE).document(str(user)).set(
                {"chat": chat, "user": user, "state": self.resolve_state(state)}
            )

    async def get_state(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        default: Optional[str] = None,
    ) -> Optional[str]:
        chat, user = self.check_address(chat=chat, user=user)
        db = self._db

        result = (
            db.collection(STATE)
            .where("chat", "==", chat)
            .where("user", "==", user)
            .get()
        )
        print(f"{result=}")
        return (
            result[0].to_dict().get("state") if result else self.resolve_state(default)
        )

    async def set_data(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        data: Dict = None,
    ):
        chat, user = self.check_address(chat=chat, user=user)
        db = self._db
        if not data:
            docs: list[firestore.DocumentSnapshot] = (
                db.collection(STATE)
                .where("chat", "==", chat)
                .where("user", "==", user)
                .stream()
            )
            for doc in docs:
                doc.reference.delete()
        else:
            db.collection(DATA).document(str(user)).set(
                {"chat": chat, "user": user, "data": data}
            )

    async def get_data(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        default: Optional[dict] = None,
    ) -> Dict:
        chat, user = self.check_address(chat=chat, user=user)
        db = self._db
        result: list[firestore.DocumentSnapshot] = (
            db.collection(DATA)
            .where("chat", "==", chat)
            .where("user", "==", user)
            .get()
        )

        return result[0].get("data") if result else default or {}

    async def update_data(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        data: Dict = None,
        **kwargs,
    ):
        if data is None:
            data = {}
        temp_data = await self.get_data(chat=chat, user=user, default={})
        temp_data.update(data, **kwargs)
        await self.set_data(chat=chat, user=user, data=temp_data)

    def has_bucket(self):
        return True

    async def get_bucket(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        default: Optional[dict] = None,
    ) -> Dict:
        chat, user = self.check_address(chat=chat, user=user)
        db = self._db
        result = (
            db.collection(BUCKET)
            .where("chat", "==", chat)
            .where("user", "==", user)
            .get()
        )
        return result.to_dict().get("bucket") if result else default or {}

    async def set_bucket(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        bucket: Dict = None,
    ):
        chat, user = self.check_address(chat=chat, user=user)
        db = self._db

        db.collection(BUCKET).where("chat", "==", chat).where(
            "user", "==", user
        ).update({"bucket": bucket})

    async def update_bucket(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        bucket: Dict = None,
        **kwargs,
    ):
        if bucket is None:
            bucket = {}
        temp_bucket = await self.get_bucket(chat=chat, user=user)
        temp_bucket.update(bucket, **kwargs)
        await self.set_bucket(chat=chat, user=user, bucket=temp_bucket)

    def delete_collection(
        self, coll_ref: firestore.CollectionReference, batch_size: int
    ):
        docs: list[firestore.DocumentReference] = coll_ref.list_documents(
            page_size=batch_size
        )
        deleted = 0

        for doc in docs:
            print(f"Deleting doc {doc.id} => {doc.get().to_dict()}")
            doc.delete()
            deleted = deleted + 1

        if deleted >= batch_size:
            return self.delete_collection(coll_ref, batch_size)

    async def reset_all(self, full=True):
        """
        Reset states in DB

        :param full: clean DB or clean only states
        :return:
        """
        db = self._db

        self.delete_collection(db.collection(STATE), batch_size=10)

        if full:
            self.delete_collection(db.collection(DATA), batch_size=10)
            self.delete_collection(db.collection(BUCKET), batch_size=10)

    async def get_states_list(self) -> List[Tuple[int, int]]:
        """
        Get list of all stored chat's and user's

        :return: list of tuples where first element is chat id and second is user id
        """
        db = self._db
        items = db.collection(STATE).list_documents()
        return [(int(item["chat"]), int(item["user"])) for item in items]


if __name__ == "__main__":
    storage = FirestoreStorage()
    print(asyncio.run(storage.get_states_list()))
    print(asyncio.run(storage.reset_all()))
