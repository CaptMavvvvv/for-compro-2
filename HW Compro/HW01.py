def format_strings(*args):
    if len(args) == 1:
        result = args[0].replace(' ', '-')
    else:
        result = '-'.join(args)
    result = result.upper()
    return result

if __name__ == '__main__':
    result = format_strings("Hello", "world", "this", "is", "a", "test")
    print(result)  # Output: "HELLOWORLDTHISISATEST"

    result = format_strings("Python", "is", "fun")
    print(result)  # Output: "PYTHONISFUN"

    result = format_strings("Hello world")
    print(result)  # Output: "HELLO-WORLD"
