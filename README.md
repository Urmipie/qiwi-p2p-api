# qiwi-p2p-api
Простое Python SDK для p2p Qiwi API
Параметры функций, кроме lifetime в оплате через форму, идентичны параметрам из [официальной документации QIWi p2p](https://developer.qiwi.com/ru/p2p-payments), но изменены для соответствия PEP.
Так billId переименовано в bill_id, а все параметры с *DateTime переименованы в *_datetime

# Установка
1. Скачать этот репозиторий
2. Распаковать в папке вашего проекта или в папке с модулями
3. `pip install requests`

# Примеры
Создание счёта и печать ссылки на него
```python
from qiwip2py import QiwiP2P
from datetime import timedelta

qiwi_p2p = QiwiP2P(secret_key=SECRET_KEY)
bill = qiwi_p2p.create_bill(bill_id='test', amount=1.99, custom_fields={'themeCode': THEME_CODE},
                            expiration_datetime=timedelta(hours=3))
print(bill.pay_url)
```

Проверка существования счёта
```python
bill = qiwi_p2p.get_bill_status('test')
if bill:
    print(f'Счёт на {bill.amount_value} {bill.amount[""]} существует')
else:
   print('Счета не существует')

```

## QiwiP2P
При создании можно не задавать какой-то из ключей, если его использование не планируется, однако, при использовании метода, для которого этот ключ нужен, будет возвращено Assertion Error или AttributeError, если секретный ключ неверен.
Во всех случаях, кроме оплаты через форму, используется секретный ключ.

Во все методы можно передать иные именованные аргументы, вроде proxy, и те передадутся в requests.request
### create_bill
Если return_pay_link == False или не указан, то создаст счёт и вернёт то же самое, что и QiwiP2P.get_bill_status() с созданным bill_id. Иначе вернёт url формы оплаты. В этом случае требуется публичный, а не секретный ключ

Таблица параметров и соответствия с Qiwi p2p

Параметр | Через API | Через форму | Описание
------------ | ------------- |------------ | ------------ |
bill_id|передаётся в url|billId|Уникальный идентификатор выставляемого счета в вашей системе
amount|amount.value|amount|Сумма, на которую выставляется счет, округленная в меньшую сторону до 2 десятичных знаков
amount_currency|amount.currency|недоступно. Только через RUB|	Валюта суммы счета. Возможные значения: RUB - рубли (по умолчанию), KZT - тенге
phone|customer.phone|phone|Номер телефона пользователя (в международном формате)
email|customer.email|email|E-mail пользователя	
account|customer.account|account|Идентификатор пользователя в вашей системе
comment|comment|comment|Комментарий к счету	(Виден пользователю при оплате)
expiration_datetime|expirationDateTime|lifetime|datetime.timedelta промежуток, который доступен счёт
custom_fields|customFields|customFields|dict с дополнительными полями (themeCode, paySourcesFilter, свои поля)
success_url|недоступно|successUrl|URL для переадресации в случае успешного перевода
return_pay_link|-|-|Если True, возвращает строку с ссылкой на форму, вместо создания счёта и возвращения Bill

### get_bill_status
- bill_id: str
Возвращает данные по счёту с bill_id
(См. Возвращаемые объекты)

### reject_bill
- bill_id: str
Отменяет счёт с bill_id и возвращает данные по нему
(См. Возвращаемые объекты)

## Возвращаемые объекты
Все методы, кроме create_bill(return_pay_link=True) возвращают один из этих двух объектов, кроме случаев с неуказанным или неверным секретным ключом:

### Bill
Объект с данными о счёте

bool(Bill) == True

Атрибут | QIWI | Тип | Описание
------------ | ------------- | ------------ | ------------ |
site_id|siteId|str|siteId
bill_id|billId||
amount|amount|dict|Данные о сумме счета
amount_value|amount.value|float|Сумма счета
status|status|dict|Данные о статусе счета
status_value|status.value	|str: 'WAITING', 'PAID', 'REJECTED' или 'EXPIRED'| Статус счёта
costumer|customer|dict|Идентификаторы пользователя
custom_fields|customFields|dict|строковые данные, переданные вами
comment|comment|str|Комментарий к счёту
creation_datetime|creationDateTime|datetime.datetime|Системная дата создания счета
expiration_datetime|expirationDateTime|datetime.datetime|Срок действия созданной формы для перевода
pay_url|payUrl|str|Ссылка для переадресации пользователя на созданную форму|
json|-|dict|Преобразованный в dict json из ответа Qiwi

### ErrorResponse
Объект, возвращаемый при коде, отличном от 200

bool(ErrorResponse) == False

* status_code: status_code: int - код ошибки
* json: dict - Преобразованный в dict json из ответа Qiwi
* service_name
* error_code
* description
* user_message
* datetime
* trace_id

# Аналог(и)
* https://github.com/WhiteApfel/pyQiwiP2P
