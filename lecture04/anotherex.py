userinput = input("Enter your message: ")
result = ""
vowels = "aeiouAEIOU"
for string in userinput:
    upper_string = string.upper()
    if string == vowels: 
        result += '*'
    else:
        result += upper_string

print(result)                         