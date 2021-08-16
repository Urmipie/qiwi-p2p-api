import requests

from typing import Optional, Union
from urllib.parse import urlencode
from json.decoder import JSONDecodeError
import datetime
from . import response_classes


class QiwiP2P:
    def __init__(self, secret_key: str = '', public_key: str = ''):
        """
        Если не указать какой-то из ключей, то при попытке вызвать метод, для которого не указан ключ,
        будет возвращено AssertionError
        """
        self.secret_key = secret_key
        self.public_key = public_key

    def _secret_key_required(f):
        """Декоратор, вызывающий ошибку, если нет нужного ключа"""

        def decorated_function(self, *args, **kwargs):
            assert self.secret_key, 'secret key required'
            return f(self, *args, **kwargs)

        return decorated_function

    def _public_key_required(f):
        """Декоратор, вызывающий ошибку, если нет нужного ключа"""

        def decorated_function(self, *args, **kwargs):
            assert self.public_key, 'public key required'
            return f(self, *args, **kwargs)

        return decorated_function

    @_public_key_required
    def _check_public_key(self):
        """Метод для проверки наличия публичного ключа, если декоратор неприменим"""
        pass

    @_secret_key_required
    def _secret_request(self, method: str, url: str, headers: dict = {}, **kwargs):
        """Запрос с заранее добвленными стандартными хедерами. В остальном - requests.request()"""
        headers['Authorization'] = 'Bearer ' + self.secret_key
        headers['Accept'] = 'application/json'
        response = requests.request(method=method, url=url, headers=headers, **kwargs)
        if response.status_code == 401:
            raise AttributeError('Wrong secret_key: 401 Unauthorized')
        return response

    @staticmethod
    def _get_bill_from_response(response: requests.Response) -> response_classes.BaseResponse:
        """Переводит response в класс из response_classes"""
        if response.status_code == 200:
            return response_classes.Bill(json=response.json())
        try:
            json = response.json()
        except JSONDecodeError:
            json = {}
        return response_classes.ErrorResponse(status_code=response.status_code, json=json)

    def create_bill(self,
                    bill_id: Optional[str] = None,
                    amount: Optional[Union[float, int]] = None,
                    amount_currency: str = 'RUB',
                    phone: str = '',
                    email: str = '',
                    account: str = '',
                    comment: str = '',
                    expiration_datetime: Optional[datetime.timedelta] = None,
                    custom_fields: dict = None,
                    return_pay_link: bool = False,
                    success_url: str = None,
                    **kwargs) -> Union[str, response_classes.BaseResponse]:
        """
        Выставление оплаты через форму или по API
        Поля совпадают с таковыми в документации, за исключением "питонофикации": например, billId изменён на bill_id,
        а expirationDateTime - expiration_datetime
        Кроме того, lifetime в выставлении через форму заменено на expiration_datetime

        :param bill_id: Идентификатор выставляемого счета в вашей системе.
                        Он должен быть уникальным и генерироваться на вашей стороне любым способом.
                        Идентификатором может быть любая уникальная последовательность букв или цифр.
                        Также разрешено использование символа подчеркивания (_) и дефиса (-)

        :param amount: Сумма, на которую выставляется счет, округленная в меньшую сторону до 2 десятичных знаков

        :param amount_currency: Валюта для оплаты, дефлотно рубли, указать KZT для тенге
                                Если выдаётся ссылка на форму, тенге недоступны

        :param phone: Номер телефона пользователя (в международном формате)

        :param email: E-mail пользователя

        :param account: Идентификатор пользователя в вашей системе

        :param comment: Комментарий к счету

        :param expiration_datetime: Отрезок времени, по которой счет будет доступен для перевода.
                    Если перевод по счету не будет произведен до этого отрезка,
                    ему присваивается финальный статус EXPIRED и последующий перевод станет невозможен.
                    По истечении 45 суток от даты выставления счет автоматически будет переведен в финальный статус

        :param return_pay_link: Вместо создания формы и возвращения bill вернёт ссылку на оплату и вернёт url если True
                                    (Вместо секретного ключа требуется публичный)
        :param custom_fields: Словарь с пользовательскими данными

        :param success_url: URL для переадресации на ваш сайт в случае успешного перевода (Только в форме!)

        :param kwargs: Именнованные параметры для передачи в requests.request

        :return: Bill, если return_pay_link == False, иначе ссылку на форму оплаты
        """
        if amount:
            amount = f'{float(amount):.2f}'

        if expiration_datetime:
            time = datetime.datetime.utcnow()
            time += expiration_datetime + datetime.timedelta(hours=3)  # перевожу дельту во время и перевожу UTC в МСК
            expiration_datetime = time.strftime('%Y-%m-%dT%H%M' if return_pay_link else '%Y-%m-%dT%H:%M:00+03:00')

        if return_pay_link:
            params = {'billId': bill_id,
                      'amount': amount,
                      'phone': phone,
                      'email': email,
                      'account': account,
                      'comment': comment,
                      'lifetime': expiration_datetime,
                      'publicKey': self.public_key,
                      'successUrl': success_url}
        else:
            params = {'amount': {'value': amount, 'currency': amount_currency},
                      'customer': {
                                    'phone': phone,
                                    'email': email,
                                    'account': account
                                    },
                      'comment': comment,
                      'expirationDateTime': expiration_datetime,
                      'customFields': custom_fields}
        params = dict(filter(lambda item: item[1], params.items()))  # убирает пустые значения

        if return_pay_link:
            self._check_public_key()
            assert amount_currency == 'RUB', ('Для формы поддерживается только оплата рублями. Воспользуйтесь'
                                              ' оплатой через API')
            url = 'https://oplata.qiwi.com/create?'
            if custom_fields:
                for key, item in custom_fields.items():
                    params[f'customFields[{key}]'] = item
            return url + urlencode(params)

        else:
            return self._get_bill_from_response(
                self._secret_request(method='PUT', url=f'https://api.qiwi.com/partner/bill/v1/bills/{bill_id}',
                                     headers={'Content-Type': 'application/json'}, json=params, **kwargs)
            )

    def get_bill(self, bill_id, **kwargs) -> response_classes.BaseResponse:
        """Метод позволяет проверить статус перевода по счету"""
        response = self._secret_request('GET', 'https://api.qiwi.com/partner/bill/v1/bills/' + bill_id, **kwargs)
        return self._get_bill_from_response(response)

    def reject_bill(self, bill_id, **kwargs):
        response = self._secret_request('POST', f'https://api.qiwi.com/partner/bill/v1/bills/{bill_id}/reject',
                                        headers={'Content-Type': 'application/json'}, **kwargs)
        return self._get_bill_from_response(response)
