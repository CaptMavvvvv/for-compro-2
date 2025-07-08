first, second, third = int(input('Enter your first score: ')), int(input('Enter your second score: ')), int(input('Enter your third score: '))
list = (first, second, third)
average = sum(list) / len(list)
if average >= 95:
    print(f'Your average is {average} Congratulations! You pass this')
else:
    print(f'Your average is {average} You failed me man. Nice try.')