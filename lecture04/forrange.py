print('KPH \t MPH')
print('------------')

for num in range(60, 130+1, 10):
    mph =  num * 0.6214
    print(num, '\t', f"{mph:.1f}")