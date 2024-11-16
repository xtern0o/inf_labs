def parse_value(value):
    """
    парсинг одиночных значений (например, элементов списка)
    """

    if value.strip()[0] == value.strip()[-1] and value[0] in ("'", '"'):
        value = value[1:-1]
    elif all(i.isdigit() for i in value):
        value = int(value)
    if value in ("true", "yes", "on"):
        value = True
    elif value in ("false", "no", "off"):
        value = False
    elif value == "none":
        value = None

    return value


def parse_oneline_list(s, current_i=0):
    """
    рекурсивная функция для парсинга однострочных списков
    """
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1].strip()
    
    # убираем повторяющиеся пробелы после запятых (они незначащие)
    while ",  " in s:
        s = s.replace(",  ", ", ")

    # Инициализируем переменную для хранения результата
    result = []
    current_element = ''
    depth = 0  # Уровень вложенности

    for char in s:

        if char == '[':
            # Увеличиваем уровень вложенности
            depth += 1
            if depth > 1:
                current_element += char

        elif char == ']':
            # Уменьшаем уровень вложенности
            depth -= 1
            if depth > 0:
                current_element += char
            elif depth == 0:
                # Если уровень вложенности вернулся к нулю, добавляем элемент в результат
                result.append(parse_oneline_list(current_element))
                current_element = ''

        elif char == ',':
            # Если запятая и уровень вложенности равен 1, добавляем элемент в результат
            if depth == 0 and current_element:
                result.append(parse_value(current_element))
                current_element = ''
            else:
                current_element += char

        elif char == " " and not current_element and depth < 1:
            continue

        else:
            current_element += char

    # Добавляем последний элемент, если он есть
    if current_element:
        result.append(parse_value(current_element))

    return result


print(parse_oneline_list('[  "main", [\'master\", v]  ]'))