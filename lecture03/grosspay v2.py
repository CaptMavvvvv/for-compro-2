def calcurate_grosspay(hour_worked, pay_rate):

    if hour_worked <= 40:
        total_salary = hour_worked * pay_rate
    else:
        total_salary = ((hour_worked - 40) * 1.5 * pay_rate) + (40 * pay_rate)

    return print(f'Your total gross pay is ${total_salary:.2f}')

def calcurate_triangle(width: int, length: int):

    area = width * length

width, length = int(inp )
hour_worked, pay_rate = int(input('Enter the number of hours worked: ')), int(input("Enter the hourly gross pay rate: "))

calcurate_grosspay(hour_worked, pay_rate) 