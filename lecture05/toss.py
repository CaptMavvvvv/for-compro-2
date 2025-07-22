import random

heads = 1
tails = 2
tosses = 5

def tossescoin():
    for toss in range(tosses):
        if random.randint(heads, tails) == heads:
            print("heads")
        else:
            print("tails")

tossescoin()