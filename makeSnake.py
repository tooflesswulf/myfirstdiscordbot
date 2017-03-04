people = ['111','112','131', '411', '551']
order = list(range(len(people)))
p2 = [1, -1, 1, -1]

print(order)
l2 = []
for dir in p2:
    l2 += order[::dir]
to_print = [people[i] for i in l2]
print(' '.join(to_print))