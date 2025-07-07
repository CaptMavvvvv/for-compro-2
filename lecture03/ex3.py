def calcurate_grosspay(hourly_worked, hourly_rate):

    total_salary = 0

    if hourly_worked <= 40:
        total_salary = hourly_worked * hourly_rate
    else:
        total_salary = 40 * hourly_rate
        overtime_hours = hourly_worked - 40
        overtime_salary = overtime_hours * hourly_rate * 1.5
        total_salary += overtime_salary

    return print(f'The gross pay is {total_salary:.2f}')

hourly_worked = int(input("Enter the number of hours worked: "))
hourly_rate = int(input("Enter the hourly pay rate: "))

calcurate_grosspay(hourly_worked, hourly_rate)