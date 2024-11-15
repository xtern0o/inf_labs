from pprint import *


__all__ = [
    "parse_object", 
    "yaml_to_dict",
]


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


parsed_numbers = set()


def parse_object(lines: list, current_indent: int, current_i: int=0):
    """рекурсивная функция для парсинга объектов ключ-значение"""

    obj_data = {}

    i = 0
    while i < len(lines):
        if i + current_i in parsed_numbers:
            i += 1
            continue
        
        line = lines[i].rstrip()
        lstrip_line = line.lstrip()
        current_indent = len(line) - len(lstrip_line)
        if lstrip_line.startswith("-"):
            current_indent += 2
        
        # чтение литеральных и сглаженных блоков
        # работает упрощенно: сколь угодно отступов не сделай, а пробелы в начале строк не считает
        if lstrip_line[-1] in ("|", ">") and i + 1 < len(lines) and lstrip_line[0] != "-":
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
            continue
                
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

        # элемент списка
        elif lstrip_line.startswith("-"):
            if isinstance(obj_data, dict):
                obj_data = []
            key, value = parse_key_value(lstrip_line[2:])
            if key is not None or value is not None:
                changed_lines = lines.copy()
                changed_lines[i] = " " * current_indent + lstrip_line[2:]
                obj_data.append(parse_object(changed_lines[i:], current_indent, i + current_i))
            else:
                value = lstrip_line[2:]
                obj_data.append(value)
            
            parsed_numbers.add(current_i + i)

        # ключ-значение
        else:
            key, value = parse_key_value(lstrip_line)

            # чтение однострочных последовательностей
            if isinstance(value, str):
                if value == "[" + value[1:-1] + "]":
                    value = value[1:-1].split(", ")
                

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
    lines = s.split("\n")
    
    # убираем пустые строки
    lines = list(filter(lambda l: l and not all(c == " " for c in l), lines))

    # убираем закомментированные строки
    lines = list(filter(lambda l: l[0] != "#", lines)) 

    # TODO: сделать работающие переносы заменой символов

    # искомый словарь
    data = {}

    data = parse_object(lines, 0)
    return data


if __name__ == "__main__":

    with open("data/example.yaml", mode="r", encoding="utf-8") as in_file:
        yaml_string = in_file.read()
    
    while "\n\n" in yaml_string:
        yaml_string = yaml_string.replace("\n\n", "\n")


    data = yaml_to_dict(yaml_string)

    pprint(data)