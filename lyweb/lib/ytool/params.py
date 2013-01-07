def str2intlist(string, spliter=','):
    ''' String to integer list

    Input:  '1, 2, 3, 4, 5, a, b, c, ...'
    Output: ([1, 2, 3, 4, 5, ...], ['a', 'b', 'c', ...])
    '''

    if not string: string = ''

    OK, FAIL = [], []
    L = [ x.strip() for x in string.split(spliter) ]
    for x in L:
        try:
            x = int(x)
            OK.append(x)
        except:
            FAIL.append(x)

    return OK, FAIL
            
    
