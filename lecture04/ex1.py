userstrings = input("Please enter your input: ")
modified_string = ""
vowels = "aeiouAEIOU"

for char in userstrings:
    upper_char= char.upper()
    if upper_char == vowels:
        modified_string += "*"
    else: 
        modified_string += upper_char

print(f'Modified string: {modified_string}')