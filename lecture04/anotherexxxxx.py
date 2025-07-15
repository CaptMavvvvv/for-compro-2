print('--------------')
print('MPH \t KPH')
print('--------------')

for mph in range(50, 131, 10):
    kph = mph // 0.6214
    print(f'{mph} \t {kph:.1f}')

print('--------------') 