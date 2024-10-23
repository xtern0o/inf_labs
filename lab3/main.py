import re


# SMILE = "[<{="


def task_1(s: str) -> int:
    if not s: return

    return len(re.findall(r"\[\<\{\=", s))


def task_2(s: str)-> list:
    if not s: return

    regex = re.compile(
        r"\b\w*[уеыаоэяиюё]{2,}\w*\b(?=[\s\W_]+(?=\w)" + 
        r"(?:[уеыаоэяиюё]*[бвгджзйклмнпрстфхцчшщ]{,1}){3}" + 
        r"[уеыаоэяиюё]*(?!\w))",
        re.IGNORECASE,
    )
    return regex.findall(s)


def task_3(s: str, a: str, b: str, c: str, l: int) -> list | None:
    """
    a, b, c - буквы;
    l - расстояние
    """
    if not (len(a) == len(b) == len(c) and len(a) == 1): return

    tail = rf"[^{a}{b}{c}\W]*"
    between = rf"[^{a}{b}{c}\W]{{{l}}}"
    letter = lambda x: rf"{x}{{1}}"
    
    regex = re.compile(
        r"\b" + tail + letter(a) + between + letter(b) + between + letter(c) + tail + r"\b", 
        re.IGNORECASE,
    )
    return regex.findall(s)


if __name__ == "__main__":

    try:
        task_number = int(input("Введите номер задачи (1, 2, 3): "))
        if not (1 <= task_number <= 3):
            raise ValueError
        
        if task_number == 1:
            print(task_1(input("Введите строку (кириллица): ")))
        elif task_number == 2:
            print(task_2(input("Введите строку (кириллица): ")))
        else:
            try:
                s = input("Введите строку: ")
                a, b, c = input("Введите 3 буквы (кириллицы) через пробел: ").split()
                l = int(input("Введите расстояние между этими буквами: "))
                print(task_3(s, a, b, c, l))
            except ValueError:
                print("[!] Некорректный ввод")

    except ValueError:
        print("[!] Введите целое число от 1 до 3")
