def basic_math_ops(ops_form, first, second):

    result = 0

    if ops_form == 1:
        result = first + second
    elif ops_form == 2:
        result = first - second
    elif ops_form == 3:
        result = first * second
    elif ops_form == 4:
        result = first / second

    return print(f'The result is {result}')

ops_form = int(input("Select operations form 1, 2 ,3, 4 : "))
first = int(input("Enter the first number: "))
second = int(input("Enter the second number: "))

basic_math_ops(ops_form, first, second)