import json
import random
from abc import ABC, abstractmethod
from time import time

from bs4 import BeautifulSoup

import requests

# comment for test
# new
#  more


# Абстрактные классы
class ExcelAbc(ABC):
    """ExcelAbc
    Абстрактный класс для
    записи и чтения данных из Excel

    Arguments:
        ABC {abc.ABCMeta} -- вспомогательный класс для создания интерфейсов
    """
    def __init__(self):
        """Init
        Инициализация класса
        """
        super().__init__()

    @abstractmethod
    def read_file(self, file_path):
        """Read file
        Считывает excel файл и приводит его в нормальный вид
        {
            'header': [..., {str}, ...],
            'data': [
                {
                    hader_item: value_item,
                    {str}: {str},
                    ...
                },
                ...
            ]
        }

        Arguments:
            file_path {str} -- путь до файла

        Returns:
            {dict} -- данные приведенные в нормалный вид
        """
        return {}

    @abstractmethod
    def write_file(self, file_path, data):
        """Write file
        Принимает данные в нормальном виде
        Записывает их в файл

        Arguments:
            file_path {str} -- путь до файла
            data {str} -- данные в нормальном виде

        Returns:
            {bool} -- статус
        """
        return False


# Абстрактный класс для Парсинга
class ParserAbc(ABC):
    """ParserAbc
    Абстрактный класс для парсинга данных

    Arguments:
        ABC {[type]} -- [description]
    """

    def __init__(self, link, params):
        # Open user-agent list
        with open('user_agents.json', 'r', encoding='utf8') as f:
            self.user_agents = json.load(f)
        # Add arguments
        self.link = link
        self.set_params(params)
        super().__init__()

    def set_params(self, params):
        self._params = params

    def get_random_user_agent(self):
        """Get random_user_agent
        Получить случайный user-agent

        Returns:
            {str} -- user-agent
        """
        return random.choice(self.user_agents)

    def make_query(self, *, params={}, verify=False):
        """Make query
        Делаем запрос к сайту

        Keyword Arguments:
            params {dict} -- get параметры (default: {{}})
            verify {bool} -- аргумент в requests (default: {False})

        Returns:
            {requests.models.Response} -- объект с результатом запроса
        """
        return requests.get(
            self.link,
            headers={'User-Agent': self.get_random_user_agent()},
            params=params,
            verify=verify
        )

    def verify_response(self, res):
        """Verify response
        Проверяет резальтат на валидность

        Arguments:
            {requests.models.Response} -- объект с результатом запроса

        Returns:
            {bool} -- Статус
        """
        return True if res.status_code == 200 else False

    @abstractmethod
    def normalize_html(self, html_data):
        """Normalize html
        На вход принимает html, арсит с него искомые данные
        и приводит их к нормальному виду
        {
            'header': [..., {str}, ...],
            'data': [
                {
                    hader_item: value_item,
                    {str}: {str},
                    ...
                },
                ...
            ]
        }

        Arguments:
            html_data {requests.models.Response} -- Res

        Returns:
            {dict} -- словарь с данными
        """
        return {}

    def pipeline_one(self, params):
        # Конвейер
        if self.verify_response(curr:=self.make_query(params={**params, **self._params})):  # noqa
            return self.normalize_html(curr)
        return None


# Классы для парсинга
class Fss(ParserAbc):
    def normalize_html(self, html_data):
        return {}


class Sud(ParserAbc):
    def normalize_html(self, html_data):
        self.data = {'header': [], 'data': []}
        soup = BeautifulSoup(html_data.content)
        if not soup.table:
            return {}
        for row_i, row in enumerate(soup.table.find_all('tr')):
            if row_i == 0:
                self.data['header'] = [x.text for x in row.find_all('td')]
            else:
                _data = {}
                for col_i, column in enumerate(row.find_all('td')):
                    if column.find('a'):
                        _data[self.data['header'][col_i]] = column.a['href']
                    else:
                        _data[self.data['header'][col_i]] = column.text
                self.data['data'].append(_data)
        return self.data


# Классы для работы с Excel
class ExcelSud(ExcelAbc):
    data = {'header': [], 'data': []}

    def read_file(self, file_path):
        self.data = {'header': [], 'data': []}
        self.data['header'] = 'f_name'
        data = pd.read_excel(file_path)
        for i in range(len(data['Фамилия'])):
            self.data['data'].append({
                'f_name': f"{data['Фамилия'][i]} {data['Имя'][i]} {data['Отчество'][i]}"
            })
        return self.data

    def write_file(self, file_path, data):
        df1 = pd.DataFrame(
            {
                header: [x[header] for x in data['data']]
                for i, header in enumerate(data['header'])
            }
        )
        with pd.ExcelWriter(file_path) as writer:
            df1.to_excel(writer, sheet_name='1')


# ! Пример
def analize(file_path):
    # для работы с excel
    ex = ExcelSud()
    # default get параметры
    params = {
        'id': '300',
        'act': 'go_sp_search',
        'searchtype': 'sp',
        'page': '1',
        'court_subj': '77',
    }
    # для работы с базой данных
    sud = Sud('https://sudrf.ru/index.php', params)
    for x in (curr:=ex.read_file(file_path))['data']:  # noqa
        curr_table = sud.pipeline_one(x)
        if curr_table:
            ex.write_file(
                'data/'+str(time()).split('.')[0]+".xls",
                curr_table
            )
