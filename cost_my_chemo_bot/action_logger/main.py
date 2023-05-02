import io

import httpx
import logging
import pandas as pd
import datetime
from cost_my_chemo_bot.config import SETTINGS, ACTION_LOGGER_SETTINGS


logger = logging.getLogger(__name__)

# columns which we save from Sematext log system
LOG_COLUMNS = ['@timestamp', 'username', 'user_id', 'message', 'is_invitation', 'invite_link']


class ActionLogger:
    """
        Wrapper for sending logs to Sematext online log platform

        More about logs: https://sematext.com/docs/logs/
    """

    def __init__(self):
        self.client = httpx.AsyncClient()

    async def send_message(self, message: str, user_id: int, username: str, extra_parameters: dict = None):
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

        if extra_parameters is not None:
            try:
                json_payload.update(extra_parameters)
            except Exception as error:
                logger.error(msg=f"Can't add extra parameters to sematext: Error: {error}")

        response = await self.client.post(ACTION_LOGGER_SETTINGS.upload_logs_url, json=json_payload)

    async def get_logs(self) -> pd.DataFrame:
        """
            Get logs from Sematext

            Input:
                None
            Output:
                pandas dataframe with valid logs
        """

        headers = {'Authorization': f'apiKey {ACTION_LOGGER_SETTINGS.ACTION_LOGGER_API_KEY}'}

        response = await self.client.get(url=ACTION_LOGGER_SETTINGS.get_logs_url, headers=headers)

        response_body = response.json()

        logs = response_body['hits']['hits']

        df = pd.DataFrame()

        for log in logs:
            log_fields = log['_source']
            df = pd.concat([df, pd.DataFrame(data=log_fields, index=[0])])

        df = df.sort_values(by="@timestamp").reset_index(drop = True)

        df['@timestamp'] = pd.to_datetime(df['@timestamp']).dt.tz_convert(tz="Europe/Moscow").dt.tz_localize(None)
        df['@timestamp_date'] = df['@timestamp'].dt.date

        df['user_id'] = df['user_id'].astype('Int64', errors='ignore')

        left_time_border = datetime.datetime.now() - datetime.timedelta(days=ACTION_LOGGER_SETTINGS.ACTION_LOGGER_SAVE_PERIOD_DAYS,
                                                                        hours=ACTION_LOGGER_SETTINGS.ACTION_LOGGER_SAVE_PERIOD_HOURS,
                                                                        minutes=ACTION_LOGGER_SETTINGS.ACTION_LOGGER_SAVE_PERIOD_MINUTES)

        right_time_border = datetime.datetime.now()

        # cut time and save only date
        left_time_border = left_time_border.date()
        right_time_border = right_time_border.date()

        # filter out only valid dates
        df = df[(left_time_border < df['@timestamp_date']) & (df['@timestamp_date'] <= right_time_border)].reset_index(drop=True)

        return df[LOG_COLUMNS]

    async def save_logs_bitrix(self, df: pd.DataFrame):
        """
            Save logs in table format (Pandas DataFrame) to Bitrix24
        """

        response = await self.client.get(
            f"{SETTINGS.BITRIX_DISK_URL}/{SETTINGS.BITRIX_DISK_TOKEN.get_secret_value()}"
            f"/disk.folder.uploadfile.json?id={SETTINGS.BITRIX_DISK_FOLDER_ID}",
        )

        response_json = response.json()

        upload_url = response_json['result']['uploadUrl']

        current_date = datetime.date.today()

        log_filename = f"{current_date}_logs.xlsx"

        # convert dataframe to bytes in Excel format
        df_bytes = io.BytesIO()
        df.to_excel(excel_writer=df_bytes)
        df_bytes.seek(0)

        # Bitrix can't upload 2 files with the same name.
        # In this case we try to add a suffix (10 times) to filename to make it unique
        for i in range(1, 50):
            response = await self.client.post(url=upload_url,
                                              files={response_json['result']['field']: (log_filename,
                                                                                        df_bytes,
                                                                                        "text/plain")})
            if response.status_code == 200:
                break
            else:
                log_filename = f"{current_date}_logs_{i}.xlsx"

    async def close(self):
        """ Actions when we stop logging """
        await self.client.aclose()


action_logger = ActionLogger()