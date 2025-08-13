from io import BytesIO


def create_shopping_list_file(shopping_cart):
    """Функция для создания тестового файла со списком продуктов."""
    file = BytesIO()
    for ingredient in shopping_cart:
        file.write(
            f"{ingredient['recipes__ingredients__name']}: "
            f"{ingredient['amount']} "
            f"{ingredient['recipes__ingredients__measurement_unit']}\n"
            .encode('utf-8')
        )
    file.seek(0)
    return file
