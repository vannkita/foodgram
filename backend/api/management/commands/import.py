import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient

FIELD_NAMES = ['name', 'measurement_unit']

data_files = {
    'ingredient': 'data/ingredients.csv',
}


class Command(BaseCommand):
    """Команда для импорта CSV в базу данных."""
    help = 'Импорт CSV-файлов в базу данных.'

    def handle(self, *args, **options):
        """Функция обработки."""
        for model, file_path in data_files.items():
            print(f'Импорт {file_path} в {model}...')
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if not row:
                        continue
                    data = {
                        'name': row[0],
                        'measurement_unit': row[1]
                    }
                    obj = self.create_object(model, data)
                    if obj:
                        obj.save()
            print(f'Успешный импорт {file_path}.')

    def create_object(self, model_name, data):
        """Создание объекта с использованием Django ORM."""
        if model_name == 'ingredient':
            return Ingredient(**data)
