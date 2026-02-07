# torgi-opendata
torgi-opendata

Задача: Сделать загрузку открытых данных с портала https://torgi.gov.ru/new/public/opendata/reg

1. Исходные данные.
1.1 Файл list.json содержит перечень разделов данных.
1.2 Используй uv python manager
1.3 Делай так чтобы функционал создания и заполнения таблиц можно было выбирать параметром запуска main.py. Если параметр не задан, то функционал не выполняется.

2. Общие требования
2.1 Создай sqlite db: torgi.db
2.2 Во всех создаваемых таблицах предусмотри:
- первичный ключ globalid. Значение этого поля должно генерироваться, как uuid при внесении записи в таблицу.
- поле createdate. Значение этого поля должно генерироваться, как текущие дата и время в формате YYYY-MM-DDThh:mm:ss при внесении записи в таблицу.
- поле updatedate. Значение этого поля должно генерироваться, как текущие дата и время в формате YYYY-MM-DDThh:mm:ss при внесении записи в таблицу. При обновлении записи значение этого поля должно актуализировать датой и временем изменения данных.

3. Добавь в main.py функционал создания таблицы privatisationplans. Состав полей возьми из файла ./privatisationplans/structure-* tag "definitions":"PlanListObject":"properties". Поле globalid должно быть уникальным первичным ключом. Заполнение таблицы данными сделай из файлов ./privatisationplans/data-*

4. Добавь в main.py функционал создания таблицы privatisationplanlist, связанной с privatisationplans по foreinkey regnum. Состав полей возьми из файла ./privatisationplans/privatizationPlan_*
Расширь состав полей таблицы privatisationplanlist. Добавь недостающие поля из файлов planReport*.json & privatizationDecision*.json.

Если поле имеет вложенную структуру, то сделай несколько полей с именами <основной тег>_<вложенный тег>. Заполнение таблицы данными сделай из файлов, которые надо скачать по ссылкам из поля href для всех записей таблицы privatisationplanlist.

Данные из поля privatizationObjects надо записать в отдельную таблицу privatizationobjects . Записи связываем foreinkey по полю id . Поля таблицы - это все вложенные теги поля privatizationObjects. Если поле имеет вложенную структуру, то сделай несколько полей с именами <основной тег>_<вложенный тег>.

5. Сделай возможность загружать данные в созданные таблицы из файлов данных data*.json в соответствующие таблицы при указании атрибутов --noticeupload (таблицы notice, notice_notice, noticeclarification) & --privplansupload (таблицы privatisationplans, privatisationplanlist, privatizationObjects)

6. Сделай отдельный модуль metadownload.py . Этот модуль должен скачать все файлы указанные в теге source файлов meta.json в каталоге privatisationplans. Скачиваемые файлы надо разместить в подкаталоге loaded. Загружай файлы только если их нет в подкаталоге loaded.

7. Сделай отдельный модуль createexcel_privplans.py . Этот модуль должен выгрузить в excel данные таблиц: privatisationplans, privatisationplanlist, privatizationobjects. Каждую таблицу нужно на отдельный лист с названием этой таблицы.

8. Сделай отдельный модуль masterdata.py . Этот модуль должен создать таблицы с названиями из тега NSIType файла ./masterdata/data-20220101T0000-20251222T0000-structure-20250101.json с добавлением префикса nsi_ .
Атрибуты таблиц нужно брать из файла, расположенного по ссылке из тега href.

Если значение тега имеет вложенную структуру, то сделай несколько полей с именами <основной тег>_<вложенный тег>. Заполнение таблицы данными сделай значениями соответствующих тегов.
Первичным уникальным ключом всех таблиц должно быть первое поле "code".

2026-01-26
pls correct download_data.zsh, чтобы можно было загружать планы приватизации не только с самой свежей датой, но и за любой период. Период должен задаваться атрибутом в календарных днях. То есть за две недели, значение атрибута будет 14.

2026-02-07
add .env file with parameter TORGIDB with defaut value SQLITE. Add the possibility to store all project in MS SQL Server Instead of SQLite? when parameter TORGIDB=SQLSERVER

#- Поддержка различных типов баз данных

Проект теперь поддерживает работу как с SQLite, так и с MS SQL Server базами данных. Для выбора типа базы данных используйте переменную окружения `TORGIDB` в файле `.env`:

- Для использования SQLite: `TORGIDB=SQLITE` (по умолчанию)
- Для использования MS SQL Server: `TORGIDB=SQLSERVER`

При использовании MS SQL Server также укажите дополнительные параметры в файле `.env`:
- `SQL_SERVER` - имя сервера SQL Server (по умолчанию: localhost)
- `SQL_DATABASE` - имя базы данных (по умолчанию: torgi)
- `SQL_USERNAME` - имя пользователя (необязательно при использовании Windows аутентификации)
- `SQL_PASSWORD` - пароль (необязательно при использовании Windows аутентификации)
- `SQL_DRIVER` - драйвер ODBC (по умолчанию: {ODBC Driver 17 for SQL Server})

### Установка для MS SQL Server (Linux)
Если вы планируете использовать MS SQL Server, установите системные зависимости:
```bash
# Для Ubuntu/Debian:
sudo apt-get update
sudo apt-get install -y unixodbc-dev
# Затем установите драйвер MS ODBC:
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql17

# Для CentOS/RHEL:
sudo curl -o /etc/yum.repos.d/msprod.repo https://packages.microsoft.com/config/rhel/7/prod.repo
sudo yum update
sudo ACCEPT_EULA=Y yum install -y msodbcsql17

# Для Arch Linux:
sudo pacman -S msodbcsql17  # или установите из AUR если пакет недоступен в основном репозитории
```

Дополнительную информацию по устранению неполадок с подключением к SQL Server см. в файле `SQLSERVER_CONNECTION_TROUBLESHOOTING.md`.