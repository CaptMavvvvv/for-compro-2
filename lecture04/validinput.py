score = int(input("Enter a test score: "))
while score < 0 or score > 100:
    print(f'ERROR: The score cannot be negative or greater than 100')
    score = int(input("Enter the correct score: "))

print(f'The score is {score}')