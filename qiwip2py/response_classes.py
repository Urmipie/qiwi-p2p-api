import datetime
from typing import Optional


def qiwi_format_to_datetime(string: str) -> datetime.datetime:
    """Переводит время, которое присылает Qiwi в datetime UTC"""
    return datetime.datetime.strptime(string.split('.')[0].split('+')[0], '%Y-%m-%dT%H:%M:%S')


class BaseResponse:
    """Базовый класс-дескриптор"""
    def __init__(self, json=None):
        if json is None:
            json = {}
        self.__dict__ = json
        self.json = self.json

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__class__) + ': ' + str(self.__dict__)

    def __getitem__(self, item):
        return self.__dict__[item]

    def __bool__(self):
        return False


class Bill(BaseResponse):
    """
    Класс, возвращаемый вместо JSON с данными счёта. Атрибут .json Содержит исходный dict
    Названия атрибутов совпадают с названиями из документации Qiwi, но "питонизированы"
    (Например, customFields переименован в custom_fields,
    creationDateTime - в creation_datetime, expirationDateTime - в expiration_datetime)
    """
    def __init__(self, json: dict):
        self.site_id: str = json.get('siteId')
        self.bill_id: str = json.get('billId')
        self.amount: dict = json.get('amount', {})
        self.amount_value: Optional[float] = float(self.amount.get('value')) if self.amount.get('value') else None
        self.status: dict = json.get('status', {})
        self.status_value = self.status.get('value')
        self.costumer = json.get('costumer')
        self.custom_fields = json.get('customFields')
        self.comment = json.get('comment')
        self.creation_datetime = qiwi_format_to_datetime(json.get('creationDateTime'))
        self.expiration_datetime = qiwi_format_to_datetime(json.get('expirationDateTime'))
        self.pay_url = json.get('payUrl')
        self.json = json

    def __bool__(self):
        return True


class ErrorResponse(BaseResponse):
    def __init__(self, json: dict, status_code=404):
        self.service_name = json.get('invoicing-api')
        self.error_code = json.get('errorCode')
        self.description = json.get('description')
        self.user_message = json.get('userMessage')
        self.datetime = qiwi_format_to_datetime(json.get('dateTime'))
        self.trace_id = json.get('traceId')
        self.json = json
        self.status_code = status_code

    def __str__(self):
        return str(self.status_code) + ': ' + self.user_message

    def __bool__(self):
        return False
