fibo_arr = []   # список, содержащий все ЧФ <= n
num = []        # искомое число в ФСС


def ten2fib(n, k):
    """
    n - число, для которого необходимо узнать запись в ФСС
    k - индекс ближайшего ЧФ
    """
    if k < 0: return    # условие выхода из рекурсии - отрицательный индекс

    f = fibo_arr[k]
    if f > n:
        num.append(0)   
    else:               # если существует ЧФ <= n, то оно нам подходит
        num.append(1)   # и остается провернуть то же самое 
        n -= f          # для их разности

    ten2fib(n, k - 1)


try:
    n = int(input())
except ValueError:
    print("ЧИСЛО!!!!!!")

if n < 0:
    print("Запись ФСС существует только для целых чисел >= 0")
elif n == 0:
    print(0)
else:
    f0, f1 = 1, 1
    while f1 <= n:
        fibo_arr.append(f1)
        f0, f1 = f1, f0 + f1

    ten2fib(n, len(fibo_arr) - 1)

    print("".join(list(map(str, num))))
