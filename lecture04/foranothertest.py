keep_going = 'y'
while keep_going.lower == 'y':
    wholeale = input("Enter the item's wholesale cost: ")
    retail = wholeale * 2.5
    print(f'Retail price is {retail}')
    keep_going = input("Do you want to do another calcurate? \
                       If you want to, press y for yes: ") 