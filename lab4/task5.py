import time

from task1.main import main as task1_main
from task2.main import main as task2_main
from task3.main import main as task3_main
from task4.main import main as task4_main


def timer(func, n=1):
    """
    функция для вычисления времени n-кратного
    выполнения функции
    """
    start_time = time.time()
    for _ in range(n):
        func()
    return time.time() - start_time


for name, func in [
    ("task1       ", task1_main),
    ("task2 (dop1)", task2_main),
    ("task3 (dop2)", task3_main),
    ("task4 (dop3)", task4_main),
]:
    print(
        f"{name}: \t{timer(func, 100)}"
    )