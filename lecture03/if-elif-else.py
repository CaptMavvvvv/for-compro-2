inchar = input("Input one character: ")
if inchar >= 'A' and inchar <= 'Z':
    print(f'You input Upper Case Letter : {inchar}')
elif inchar >= 'a' and inchar <= 'z':
    print(f'You input Lower Case Letter : {inchar}')
elif inchar >= '0' and inchar <= '9':
    print(f'You input Number : {inchar}')
else:
    print(f"It's not a letter or number : {inchar}")