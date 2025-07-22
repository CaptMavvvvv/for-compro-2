def is_armstrong(number):
    num_str = str(number)
    num_digits = len(num_str)

    armstrong_sum = 0
    for digits_char in num_str:
        digits = int(digits_char)
        armstrong_sum += digits ** num_digits

    return armstrong_sum == number
    
print(is_armstrong(153))
print(is_armstrong(9474))
print(is_armstrong(123))