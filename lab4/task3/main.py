import re


__all__ = [
    "parse_object", 
    "yaml_to_dict",
]


def screening(s: str) -> str:
    """
    Экранирование служебных символов
    """

    new_s = s.replace('\"', '\\"')
    new_s = new_s.replace("\n", "\\n").replace("\t", "\\t")

    return new_s


def parse_key(s):
    """подходит для строк вида `key:` и `key` """
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

        if value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        elif all(i.isdigit() for i in value):
            value = int(value)

        if value == "true":
            value = True
        elif value == "false":
            value = False
        elif value == "null":
            value = None

        key = parse_key(key)
        
        return key, value
    except Exception:
        return None, None


# номера строк, которые уже распершены
parsed_numbers = set()


def parse_object(lines: list, current_indent: int, current_i: int=0):
    """рекурсивная функция для парсинга объектов ключ-значение"""

    obj_data = {}

    i = 0
    while i < len(lines):

        # перемещаемся на строку, которую еще не распарсили, пропуская уже обработанные
        if i + current_i in parsed_numbers:
            i += 1
            continue
        
        line = lines[i].rstrip()
        lstrip_line = line.lstrip()

        # инициализируем текущий отступ
        current_indent = len(line) - len(lstrip_line)
        if lstrip_line.startswith("-"):
            current_indent += 2
        
        # чтение литеральных и сглаженных блоков
        # работает упрощенно: сколь угодно отступов не сделай, а пробелы в начале строк не считает
        if re.match(r"^(?!- ).*(\||>)$", lstrip_line) and i + 1 < len(lines):
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
            key = lstrip_line[:-3]
            obj_data[key] = block_text

            parsed_numbers.add(current_i + i)           
        
            # далее перемещаемся сразу к проверке на выход из текущего уровня вложенности
        else:

            # TODO: не обрабатывается одиночная однострочная послдеовательность [[[[[[[[a, b, 1]]]]]]]]
            
            # кончается на :
            if re.match(r".*:$", lstrip_line):
                key = lstrip_line[:-1]
                indent_data = parse_object(lines[i + 1:], current_indent + 2, i + current_i + 1)
                if lstrip_line.startswith("-"):
                    if isinstance(obj_data, dict):
                        obj_data = []
                    obj_data.append({key[2:]: indent_data})
                else:
                    obj_data[key] = indent_data
                
                parsed_numbers.add(current_i + i)

            # элемент списка
            elif re.match(r"- .*", lstrip_line):

                # ЧАСТНЫЙ СЛУЧАЙ: Строка "-" означает разделение 
                # между списками в конструкции вложенных списков
                if lstrip_line == "-":
                    if isinstance(obj_data, dict):
                        obj_data = []
                    obj_data.append(parse_object(lines[i + 1:], current_indent + 2, i + current_i + 1))

                if isinstance(obj_data, dict):
                    obj_data = []
                key, value = parse_key_value(lstrip_line[2:])
                if key is not None or value is not None:
                    changed_lines = lines.copy()
                    changed_lines[i] = " " * current_indent + lstrip_line[2:]
                    obj_data.append(parse_object(changed_lines[i:], current_indent, i + current_i))
                else:
                    value = lstrip_line[2:]
                    if re.match(r"'.*'|\".*\"", lstrip_line):
                        value = value[1:-1]
                    obj_data.append(value)
                
                parsed_numbers.add(current_i + i)

            # ключ-значение
            else:
                key, value = parse_key_value(lstrip_line)

                # чтение однострочных последовательностей
                if isinstance(value, str):
                    if re.match(r"\[.*\]", value):
                        val_list = value[1:-1].strip().split(", ")
                        for k in range(len(val_list)):
                            val = val_list[k]
                            if val[0] == val[-1] and val[0] in ("'", '"'):
                                val_list[k] = val_list[k][1:-1]
                        value = val_list
                    
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

        i += 1

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
                json_value = str(value)
            elif isinstance(value, bool):
                json_value = ("false", "true")[value]
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
            value = screening(value)
            json_value = f'"{value}"'
        elif isinstance(value, (int, float)):
            json_value = str(value)
        elif isinstance(value, bool):
            json_value = 'true' if value else 'false'
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



if __name__ == "__main__":

    with open("data/ci_django.yaml", mode="r", encoding="utf-8") as in_file:
        yaml_string = in_file.read()
    
    # ИЗ ЯМЛ В СЛОВАРЬ
    data = yaml_to_dict(yaml_string)

    # ИЗ СЛОВАРЯ В JSON СТРОКУ
    json_dumped = dict_to_json_string(data)

    with open("task3/output.json", mode="w", encoding="utf-8") as json_file:
        json_file.write(json_dumped)
