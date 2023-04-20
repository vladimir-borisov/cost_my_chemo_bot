import httpx
from cost_my_chemo_bot.config import ACTION_LOGGER_SETTINGS


class ActionLogger:
    """
        Wrapper for sending logs to Sematext online log platform

        More about logs: https://sematext.com/docs/logs/
    """

    def __init__(self):
        self.client = httpx.AsyncClient()

    async def send_message(self, message: str, user_id: int, username: str):
        """
            Send log message to a server

            Input:
                message: str message to write
        """

        # KEY:VALUE pairs of tags which we want to send to server
        json_payload = {
            "message": message,
            "user_id": user_id,
            "username": username
        }

        response = await self.client.post(ACTION_LOGGER_SETTINGS.get_api_url, json=json_payload)

    async def close(self):
        """ Actions when we stop logging """
        await self.client.aclose()


action_logger = ActionLogger()
