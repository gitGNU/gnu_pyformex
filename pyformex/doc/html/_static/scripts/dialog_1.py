res = askItems([
    dict(name='m',value=10,text='number of modules in axial direction'),
    dict(name='n',value=8,text='number of modules in tangential direction'),
    dict(name='r',value=10.,text='barrel radius'),
    dict(name='a',value=180.,text='barrel opening angle'),
    dict(name='l',value=30.,text='barrel length'),
    ])
if not res:
    exit()

globals().update(res)
