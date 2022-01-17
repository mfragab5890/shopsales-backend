def alternatingSort(a):
    n = len(a)
    b = [ 0 ] * n
    y = 0
    for i in range(0, n):
        if i % 2 == 0 or i == 0:
            b[ i ] = a[ i // 2 ]
        else:
            b[ i ] = a[ n - 1 - y ]
            y += 1
    return b


print(alternatingSort([ 1, 3, 5, 7, 8, 9, 6, 4, 2 ]))
