testStr = 'hey:you-are weird'
for i in [':','-',' ']:
    testStr = testStr.replace(i, '')
print(testStr)