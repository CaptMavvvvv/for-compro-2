global_variable = "I'm outside the func"

def myfunc():
    print(global_variable)

myfunc()

print(global_variable)