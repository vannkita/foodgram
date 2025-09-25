import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов из CSV файла'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Путь к CSV файлу')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        self.stdout.write(
            self.style.SUCCESS(f'Импорт данных из {csv_file}...')
        )
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                name, measurement_unit = row
                Ingredient.objects.update_or_create(
                    name=name.strip(),
                    defaults={'measurement_unit': measurement_unit.strip()},
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Добавлен/обновлён: {name} ({measurement_unit})'
                    )
                )
        self.stdout.write(self.style.SUCCESS('Импорт завершён!'))
