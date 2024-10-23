BIT_NAME = [
    "OK",
    "r1",
    "r2",
    "i1",
    "r3",
    "i2",
    "i3",
    "i4",
]


def haming(msg: list) -> dict:
    """
    Функция для исправления некорректного сообщения
    используя код Хэмминга
    """
    s1 = msg[0] ^ msg[2] ^ msg[4] ^ msg[6]
    s2 = msg[1] ^ msg[2] ^ msg[5] ^ msg[6]
    s3 = msg[3] ^ msg[4] ^ msg[5] ^ msg[6]

    err_pos = s1 + s2 * 2 + s3 * 4
    if err_pos > 0:
        msg[err_pos - 1] ^= 1
    return {
        "correct_haming": "".join(list(map(str, msg))),
        "correct_value": "".join(list(map(str, [msg[2], msg[4], msg[5], msg[6]]))),
        "err_pos": err_pos,
        "err_type": BIT_NAME[err_pos],
    }
    
try:
    s = list(map(int, list(input())))
    if len(s) != 7:
        print("Некорректный ввод: введите 7 символов 0 или 1")
    else:
        for i in s:
            if i not in (0, 1):
                print("Некорректный ввод: только 0 и 1")
                break
        else:
            h = haming(s)
            if h["err_pos"] == 0:
                print("CORRECT!")
            else:
                print("ERROR!")
            for key, val in h.items():
                if key == "err_pos" and val == 0:
                    continue
                print(f"{key}: {val}")

except ValueError:
    print("Некорректный ввод: только 0 и 1")
