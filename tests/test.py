w = '01234'

for i in range(-len(w) * 2, 2 * len(w)):
    for j in range(-len(w) * 2, 2 * len(w)):
        a = w[i:j]
        if len(a) == 0:
            print(' ' * (len(w) + 1), end='', sep='')
        else:
            print(' ' * int(a[0]), a, ' ' * (len(w) - int(a[-1])), end='', sep='')
    print()
