import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient

FIELD_NAMES = ['name', 'measurement_unit']

data_files = {
    'ingredient': 'data/ingredients.csv',
}

class Command(BaseCommand):
    """Command for import csv into database."""
    help = 'Import csv files to database.'

    def handle(self, *args, **options):
        """Handle function."""
        for model, file_path in data_files.items():
            print(f'Importing {file_path} to {model}...')
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
            print(f'Success import {file_path}.')

    def create_object(self, model_name, data):
        """Create object from django ORM."""
        if model_name == 'ingredient':
            return Ingredient(**data)