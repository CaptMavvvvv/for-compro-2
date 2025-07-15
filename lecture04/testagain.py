max = int(input("Enter the maximum number you want to calcurate: "))
total = 0.0

print(f'This program calcurates the sum of {max} number you will enter')

for counter in range(max):
    number = int(input(f"Enter the #{counter + 1}: "))
    total = total + number

print(f'The total is {total}')