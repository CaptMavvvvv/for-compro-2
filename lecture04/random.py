import random

print('What is my magic number (1 to 100) ?')
mynumber = random.randint(1, 100)
ntries = 1
yourguess = -1
while ntries < 7 and yourguess != mynumber:
    msg = str(ntries) + ">> "
    if ntries == 6:
        print('Your last chance goddamnit')
    yourguess = int(input(msg))
    if yourguess > mynumber:
        print("--> too high bro")
    else:
        print("..> too low for fuck sake")
    ntries += 1

if yourguess == mynumber:
    print(f"YES YES YES IT MY NUMBER {mynumber}")
else:
    print(f'HAHAHAHAHAH my number is {mynumber} you dumb')