
a1 = [2,7,8,9,1, 10,15]

a1.sort(reverse=True)

b2 = []
i = 0
j = 1
while j < len(a1):
    b2.append((a1[i]-a1[j], i, j))
    i = j
    j += 1


print(b2)