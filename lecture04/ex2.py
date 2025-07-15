
keep_going = 'y'

while keep_going == 'y':
    wholesale = float(input("Enter the item's wholesale cost: "))
    retail = wholesale * 2.5

    print(f'Retail price: ${retail:.2f}')

    choice = input('Do you have another item' + \
                    'Enter y for yes: ')
    keep_going = choice.lower