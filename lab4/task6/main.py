from pprint import *


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

        value = parse_value(value)
        key = parse_key(key)
        
        return key, value
    except Exception:
        return None, s


def parse_value(value):
    """
    парсинг одиночных значений (например, элементов списка, однострочных объектов)
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
            value = value[1:-1]
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

    for i, char in enumerate(s):

        if char == '[':
            # увеличиваем уровень вложенности
            current_element += char
            depth += 1

        elif char == ']':
            # уменьшаем уровень вложенности
            depth -= 1
            current_element += char

        elif char == ',':
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
        

# номера строк, которые уже распершены
parsed_numbers = set()


def parse_object(lines: list, current_indent: int, current_i: int=0):
    """
    рекурсивная функция для парсинга объектов ключ-значение
    """

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


def main():

    with open("data/schedule.yaml", mode="r", encoding="utf-8") as in_file:
            yaml_string = in_file.read()
        
    # ИЗ ЯМЛ В СЛОВАРЬ
    data = yaml_to_dict(yaml_string)
    
    scsv_doc = "name;day;month;year;title;class-format;type;teacher;address;classroom;begin;end\n"
    scsv_lines = []
    
    for day_info in data["day"]:
        date = day_info["date"]

        name = day_info["name"]
        day = date["day"]
        month = date["month"]
        year = date["year"]

        schedule = day_info["schedule"]
        for lesson in schedule:
            title = lesson["title"]
            class_format = lesson["class-format"]
            address = lesson["place"]["address"]
            classroom = lesson["place"]["classroom"]
            teacher = lesson["teacher"]
            begin = lesson["time"]["begin"]
            end = lesson["time"]["end"]
            type_ = lesson["type"]

            row = [
                name, day, month, year, title, 
                class_format, type_, teacher, 
                address, classroom, begin, end,
            ]

            line = ";".join(list(map(str, row)))
            scsv_lines.append(line)
    
    scsv_doc += "\n".join(scsv_lines)

    with open("task6/output.csv", mode="w", encoding="utf-8") as out_file:
        out_file.write(scsv_doc)


if __name__ == "__main__":
    main()
