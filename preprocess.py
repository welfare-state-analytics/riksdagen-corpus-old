import re

folder = "../../Downloads/riksdagens_protokoll_1920-2020/"
filename = "prot_1920__ak__6.txt"
filename = "prot_201920__148.txt"
path = folder + filename

s = open(path).read()
#print(s)

expression_1920 = re.compile("\nherr [a-zäöå0-9., ]{0,60}:")
expression_2020 = re.compile("Anf.[a-zäöåA-Z0-9.,()  ]{0,60}:")

for match in re.findall(expression_2020, s):
    print(match)