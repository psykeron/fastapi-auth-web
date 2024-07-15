from dataclasses import dataclass
from typing import Any, Dict, List

import gspread
import gspread_asyncio
import pandas as pd
from google.oauth2.service_account import Credentials


class AsyncGoogleSheetService:
    def __init__(
        self,
        project_id,
        private_key_id,
        private_key,
        client_email,
        client_id,
        auth_uri,
        token_uri,
        auth_provider_x509_cert_url,
        client_x509_cert_url,
    ):
        self.__key_file_info = {
            "type": "service_account",
            "project_id": project_id,
            "private_key_id": private_key_id,
            "private_key": private_key,
            "client_email": client_email,
            "client_id": client_id,
            "auth_uri": auth_uri,
            "token_uri": token_uri,
            "auth_provider_x509_cert_url": auth_provider_x509_cert_url,
            "client_x509_cert_url": client_x509_cert_url,
            "universe_domain": "googleapis.com",
        }

    def get_google_credentials(self) -> Credentials:
        creds = Credentials.from_service_account_info(self.__key_file_info)
        scoped = creds.with_scopes(
            [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
        )
        return scoped

    async def get_google_sheet_client(self) -> gspread_asyncio.AsyncioGspreadClient:
        async_gspread_client_manager = gspread_asyncio.AsyncioGspreadClientManager(
            self.get_google_credentials
        )
        async_gspread_client = await async_gspread_client_manager.authorize()
        return async_gspread_client

    async def read_worksheet(
        self, spreadsheet_url, worksheet_name, drop_empty_colname=None, colname_index=0
    ) -> pd.DataFrame:
        async_gspread_client = await self.get_google_sheet_client()
        google_sheet = await async_gspread_client.open_by_url(spreadsheet_url)
        worksheet_tab = await google_sheet.worksheet(worksheet_name)
        data = await worksheet_tab.get_all_values()
        df = pd.DataFrame.from_records(
            data[colname_index + 1 :], columns=data[colname_index]
        )
        if drop_empty_colname:
            df = df[df[drop_empty_colname] != ""]
        return df


class GoogleSheetService:
    def __init__(
        self,
        project_id,
        private_key_id,
        private_key,
        client_email,
        client_id,
        auth_uri,
        token_uri,
        auth_provider_x509_cert_url,
        client_x509_cert_url,
    ):
        self.google_sheet_client = gspread.service_account_from_dict(
            {
                "type": "service_account",
                "project_id": project_id,
                "private_key_id": private_key_id,
                "private_key": private_key,
                "client_email": client_email,
                "client_id": client_id,
                "auth_uri": auth_uri,
                "token_uri": token_uri,
                "auth_provider_x509_cert_url": auth_provider_x509_cert_url,
                "client_x509_cert_url": client_x509_cert_url,
                "universe_domain": "googleapis.com",
            }
        )

    def read_worksheet(
        self,
        spreadsheet_url,
        worksheet_name,
        drop_empty_colname=None,
        colname_index=0,
    ) -> pd.DataFrame:
        spreadsheet = self.google_sheet_client.open_by_url(spreadsheet_url)
        worksheet = spreadsheet.worksheet(worksheet_name)
        data = worksheet.get_all_values()
        df = pd.DataFrame.from_records(
            data[colname_index + 1 :], columns=data[colname_index]
        )
        if drop_empty_colname:
            df = df[df[drop_empty_colname] != ""]
        return df


@dataclass
class UpdateCellAction:
    row: int
    col: int
    value: str

    def to_cell(self) -> gspread.Cell:
        return gspread.Cell(row=self.row, col=self.col, value=self.value)


class GSheetDataHelper:
    def __init__(
        self, data: List[List[str]], header_row_index: int, key_column_name: str
    ):
        self.sheet_data = data
        self.header_row_index = header_row_index
        self.actions: List[UpdateCellAction] = []
        self.key_column_name = key_column_name

        self.column_headers_to_column_index = (
            self.build_column_headers_to_column_index()
        )
        self.keys_to_row_index = self.build_keys_to_row_index()

    def build_keys_to_row_index(self) -> Dict[str, int]:
        key_column_name = self.key_column_name
        rows = self.sheet_data
        header_row_index = self.header_row_index

        if header_row_index >= len(rows):
            return {}

        key_column_index = self.column_headers_to_column_index.get(key_column_name, -1)
        if key_column_index == -1:
            return {}

        return dict(
            (row[key_column_index], index + header_row_index + 1)
            for index, row in enumerate(rows[header_row_index + 1 :])
        )

    def build_column_headers_to_column_index(self) -> Dict[str, int]:
        header_row_index = self.header_row_index
        rows = self.sheet_data
        if header_row_index >= len(rows):
            return {}

        return dict(
            (column_name, index)
            for index, column_name in enumerate(rows[header_row_index])
        )

    def upsert_headers(self, column_names: List[str]):
        if len(self.sheet_data) == 0:
            self.sheet_data.append([])

        current_columns = self.sheet_data[self.header_row_index]
        headers_to_column_index = self.column_headers_to_column_index
        header_row_index = self.header_row_index
        actions = self.actions

        for column_name in column_names:
            if column_name not in headers_to_column_index:
                current_columns.append(column_name)
                headers_to_column_index[column_name] = len(current_columns) - 1
                actions.append(
                    UpdateCellAction(
                        row=header_row_index + 1,
                        col=len(current_columns),
                        value=column_name,
                    )
                )

    def upsert_record(self, record: Dict[str, Any]):
        headers_to_column_index = self.column_headers_to_column_index
        data = self.sheet_data
        actions = self.actions
        key_column_name = self.key_column_name

        record_copy = record.copy()
        # convert all values to strings.
        for key, value in record_copy.items():
            record_copy[key] = str(value)

        if key_column_name not in record:
            raise ValueError(f"Key column name {key_column_name} not found in record")

        # setup headers if they don't exist.
        for column_name, _ in record.items():
            column_index = headers_to_column_index.get(column_name, -1)

            # upsert the column if it doesn't exist.
            if column_index == -1:
                self.upsert_headers([column_name])

        # find the row for the key.
        row_key = str(record_copy[key_column_name])
        keys_to_row_index = self.keys_to_row_index
        data_row_index = keys_to_row_index.get(row_key, -1)
        if data_row_index == -1:
            # add a new row since one doesn't
            # exist for the given key.
            data.append([""] * len(headers_to_column_index))
            data_row_index = len(data) - 1
            keys_to_row_index[row_key] = data_row_index

        # upsert the values.
        for column_name, value in record_copy.items():
            column_index = headers_to_column_index.get(column_name, -1)

            if column_index == -1:
                raise Exception(f"Column name {column_name} not found in headers")

            # extend the data row if it isn't long enough
            # for the column index provided.
            if len(data[data_row_index]) <= column_index:
                data[data_row_index].extend(
                    [""] * (column_index - len(data[data_row_index]) + 1)
                )

            # update the value if it's different.
            if data[data_row_index][column_index] != value:
                data[data_row_index][column_index] = value
                actions.append(
                    UpdateCellAction(
                        row=data_row_index + 1, col=column_index + 1, value=value
                    )
                )

    def get_actions(self) -> List[UpdateCellAction]:
        return self.actions

    def pop_actions(self) -> List[UpdateCellAction]:
        actions = self.actions
        self.actions = []
        return actions
