def screening(s: str) -> str:
    """
    Экранирование служебных символов
    """

    new_s = s.replace("\'", "\\'").replace('\"', '\\"')
    new_s = new_s.replace("\n", "\\n").replace("\t", "\\t")

    return new_s


def parse_key(s):
    """
    подходит для строк вида `key:` и `key`
    """
    key = s
    if ':' in s:
        key = key[:-1]

    if key[0] == key[-1] and key[0] in ("'", '"'):
        key = key[1:-1]

    return key


def parse_key_value(s):
    """подходит для строк вида: `key: 'value'` и других вида ключ-значение"""

    try:
        key, value = s.split(": ", 1)

        # если мы обрабатываем однострочный объект,
        # то нужно обрезать внешние фиг. скобки
        if key[0] == "{" and value[-1] == "}":
            key = key[1:]
            value = value[:-1]

        value = parse_value(value)
        key = parse_key(key)

        return key, value
    except Exception:
        return None, s


def parse_value(value):
    """
    парсинг одиночных значений (например, элементов списка) ИЛИ однострочных списков
    """
    if value == "[" + value[1:-1] + "]":
        value = parse_oneline_list(value)
    elif value.strip()[0] == value.strip()[-1] and value[0] in ("'", '"'):
        value = value[1:-1]
    elif all(i.isdigit() for i in value):
        value = int(value)
    else:
        # частный случай однострочного объекта
        # объект вида {key: value} - и такое yaml поддерживает (x_x)
        if value == "{" + value[1:-1] + "}":
            # value = value[1:-1]
            value = parse_oneline_object(value)
            return value
        else:
            key, value = parse_key_value(value)
            if key is not None:
                return {key: value}
    
    if value in ("true", "yes", "on"):
        value = True
    elif value in ("false", "no", "off"):
        value = False
    elif value == "null":
        value = None        

    return value


def parse_oneline_list(s):
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

    obj_depth = 0

    for char in s:

        if char == '[':
            # увеличиваем уровень вложенности
            current_element += char
            depth += 1

        elif char == ']':
            # уменьшаем уровень вложенности
            depth -= 1
            current_element += char

        # частный случай вложенного объекта
        # рассмотриваем как отдельную вложенность,
        # чтобы не было проблем с запятыми        
        elif char == "{":
            obj_depth += 1
            current_element += char
        
        elif char == "}":
            obj_depth -= 1
            current_element += char

        elif char == ',' and not obj_depth:
            # Если запятая и уровень вложенности равен 1, добавляем элемент в результат
            if depth == 0:
                if current_element:
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


def parse_oneline_object(s):
    """
    функция для парсинга однострочных объектов вида {key: val, {kk: vv}}
    """

    if s.startswith("{") and s.endswith("}"):
        s = s[1:-1].strip()
    
    # убираем повторяющиеся пробелы после запятых (они незначащие)
    while ",  " in s:
        s = s.replace(",  ", ", ")
    
    result = {}
    current_element = ''
    depth = 0

    key = ''

    for char in s:

        if char == "{":
            current_element += char
            depth += 1
        
        elif char == "}":
            depth -= 1
            current_element += char
        
        elif char == "," and depth == 0:
            if current_element:
                if key:
                    result[key] = parse_value(current_element)
                    key = ''
                    current_element = ''
        
        elif char == ":" and depth == 0:
            if current_element:
                key = parse_key(current_element)
                current_element = ''
            
        
        # {key: {k1: v1, k2: v2}}
        
        elif char == " " and not current_element and depth < 1:
            continue
        
        else:
            current_element += char
    
    if current_element:
        result[key] = parse_value(current_element)
    
    return result
    

# номера строк, которые уже распершены
parsed_numbers = set()


def parse_object(lines: list, current_indent: int, current_i: int=0):
    """рекурсивная функция для парсинга объектов ключ-значение"""

    # искомый объект на этом уровне
    obj_data = {}

    for i in range(len(lines)):

        # перемещаемся на строку, которую еще не распарсили, пропуская уже обработанные
        if i + current_i in parsed_numbers:
            continue
        
        line = lines[i].rstrip()
        lstrip_line = line.lstrip()

        # инициализируем текущий отступ
        current_indent = len(line) - len(lstrip_line)
        if lstrip_line.startswith("-"):
            current_indent += 2
        
        # чтение литеральных и сглаженных блоков
        # работает упрощенно: сколь угодно отступов не сделай, а пробелы в начале строк не считает
        if lstrip_line[-1] in ("|", ">") and i + 1 < len(lines):
            block_data = []
            k = i + 1
            while k < len(lines):
                if len(lines[k]) - len(lines[k].lstrip()) > current_indent:
                    block_data.append(lines[k].strip())
                    parsed_numbers.add(current_i + k)
                    k += 1
                else:
                    break
            if lstrip_line[-1] == "|":
                block_text = "\n".join(block_data)
            else:
                block_text = " ".join(block_data)
            
            # а что если поставить текст на место переноса?
            # upd: РАБОТАЕТ
            lstrip_line = lstrip_line.replace("|", block_text)
            lines[i] = lstrip_line        
        
            # после этого рассматриваем обычный случай
                
        # кончается на :
        if lstrip_line.endswith(":"):
            key = lstrip_line[:-1]
            indent_data = parse_object(lines[i + 1:], current_indent + 2, i + current_i + 1)
            if lstrip_line.startswith("-"):
                if isinstance(obj_data, dict):
                    obj_data = []
                obj_data.append({key[2:]: indent_data})
            else:
                obj_data[key] = indent_data
            
            parsed_numbers.add(current_i + i)

        # чтение элемента списка
        elif lstrip_line.startswith("-"):

            # ЧАСТНЫЙ СЛУЧАЙ: Строка "-" означает разделение 
            # между списками в конструкции вложенных списков
            if lstrip_line == "-":
                if isinstance(obj_data, dict):
                    obj_data = []
                obj_data.append(parse_object(lines[i + 1:], current_indent + 2, i + current_i + 1))

                # выходим из рекурсии, ибо "следующая" строка будет "-",
                # во избежание некорректного вывода
                parsed_numbers.add(current_i + i)
                continue

            else:

                # в любом случае это будет список
                if isinstance(obj_data, dict):
                    obj_data = []

                key, value = parse_key_value(lstrip_line[2:])
                if key is not None:

                    # на мой взгляд, удобно запустить рекурсию с измененным первым символом с "-" на пробел
                    # так можно распарсить один объект, а после вернуть его, перейдя к следующему,
                    # не нарушая логики вложенности
                    changed_lines = lines.copy()
                    changed_lines[i] = " " * current_indent + lstrip_line[2:]
                    obj_data.append(parse_object(changed_lines[i:], current_indent, i + current_i))

                else:
                    value = parse_value(lstrip_line[2:])
                    obj_data.append(value)
                
            parsed_numbers.add(current_i + i)

        # ключ-значение
        else:
            if lstrip_line[0] == "[" and lstrip_line[-1] == "]":
                obj_data = parse_oneline_list(lstrip_line)
            else:                    
                key, value = parse_key_value(lstrip_line)

                if key is None:
                    # случай когда мы разделили вложенные списки строкой "-"
                    obj_data = parse_value(value)
                else:   
                    if isinstance(obj_data, dict):
                        obj_data[key] = value
                    else:
                        obj_data.append({key: value})
            
            parsed_numbers.add(current_i + i)

        # условия выхода из рекурсии
        if i + 1 < len(lines):
            # следующей считаем ближайшую после текущей не распаршенную строку
            if max(parsed_numbers) <= current_i + i:
                next_line = lines[i + 1]
            else:
                if max(parsed_numbers) - current_i + 1 < len(lines):
                    next_line = lines[max(parsed_numbers) - current_i + 1]
                else:
                    return obj_data

            next_indent = len(next_line) - len(next_line.lstrip())
            if next_line[next_indent] == "-":
                next_indent += 2
            
            if isinstance(obj_data, list):
                if next_indent < current_indent:
                    return obj_data
            else:
                if next_indent < current_indent or next_line.lstrip().startswith("-") and next_indent == current_indent:
                    return obj_data
            
            # частный случай сепаратора внутри вложенного списка (строка "-")
            if next_line.strip() == "-" and next_indent <= current_indent:
                return obj_data

    return obj_data


def yaml_to_dict(s):
    while "\n\n" in s:
        s = s.replace("\n\n", "\n")

    lines = s.split("\n")
    
    # убираем пустые строки
    lines = list(filter(lambda l: l and not all(c == " " for c in l), lines))

    # убираем закомментированные строки
    lines = list(filter(lambda l: l[0] != "#", lines)) 

    # искомый словарь
    data = {}

    data = parse_object(lines, 0)

    return data


def dict_to_json_string(data, current_indent: int=1):
    """
    преобразует словарь в строку формата json
    """

    if isinstance(data, dict):
        items = []
        for key, value in data.items():

            # преобразуем ключ
            key = screening(key)
            json_key = f'"{key}"'

            # преобразуем значение
            if isinstance(value, str):
                if value[0] == value[-1] and value[0] in ("'", '"'):
                    value = value[1:-1]
                value = screening(value)
                json_value = f'"{value}"'

            elif isinstance(value, (int, float)):
                # интересный факт: любой bool попадает в это условие, 
                # поэтому оно смещено ниже, чем проверка на bool
                json_value = str(value)

            elif isinstance(value, (int, float)):
                json_value = str(value)

            elif value is None:
                json_value = "null"

            elif isinstance(value, list):
                json_value = list_to_json_string(value, current_indent + 1)

            elif isinstance(value, dict):
                json_value = dict_to_json_string(value, current_indent + 1)

            else:
                raise TypeError(f"Неизвестный тип: {type(value)}")
            
            items.append("\t" * current_indent + f"{json_key}: {json_value}")
        
        return "{\n" + ",\n".join(items) + "\n" + "\t" * (current_indent - 1) + "}"
    
    elif isinstance(data, list):
        return list_to_json_string(data)
    else:
        raise TypeError(f"Неизвестный тип входных данных: {type(data)}")


def list_to_json_string(data, current_indent: int=1):
    """
    преобразует список в строку формата json
    """
    items = []
    for value in data:

        # преобразуем значения
        if isinstance(value, str):
            if value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            value = screening(value)
            json_value = f'"{value}"'

        elif isinstance(value, bool):
            json_value = ('false', 'true')[value]

        elif isinstance(value, (int, float)):
            # интересный факт: любой bool попадает в это условие, 
            # поэтому оно смещено ниже, чем проверка на bool
            json_value = str(value)

        elif value is None:
            json_value = 'null'

        elif isinstance(value, list):
            json_value = list_to_json_string(value, current_indent + 1)

        elif isinstance(value, dict):
            json_value = dict_to_json_string(value, current_indent + 1)

        else:
            raise TypeError(f"Неизвестный тип: {type(value)}")

        items.append("\t" * current_indent + json_value)
    return "[\n" + ",\n".join(items) + "\n" + "\t" * (current_indent - 1) + "]"


def main():

    with open("data/schedule_1day.yaml", mode="r", encoding="utf-8") as in_file:
            yaml_string = in_file.read()
        
    # ИЗ ЯМЛ В СЛОВАРЬ
    data = yaml_to_dict(yaml_string)

    # ИЗ СЛОВАРЯ В JSON СТРОКУ
    json_dumped = dict_to_json_string(data)

    with open("task4/schedule_1day.json", mode="w", encoding="utf-8") as json_file:
        json_file.write(json_dumped)


if __name__ == "__main__":
    main()
