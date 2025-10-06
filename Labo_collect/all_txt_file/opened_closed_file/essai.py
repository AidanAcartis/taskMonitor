with open('Opened_file.txt', 'r', encoding='utf-8') as line:
    open_lines = line.readlines()

with open('Closed_file.txt', 'r', encoding='utf-8') as line:
    close_lines = line.readlines()

open_modified_lines = []
close_modified_lines = []

def  treat_lines(lines):
    for line in lines:
        line = line.strip() #enlever les espaces au debut et a la fin de ligne 

        #Chercher le point '.' dans la ligne
        dot_index = line.rfind('.')

        if dot_index != -1:
            #diviser en deux chaines
            chaine1 = line[:dot_index]
            chaine2 = line[dot_index+1:]

            chaine2 = chaine2.split()[0]

            result = chaine1 + '.' + chaine2

        else:
            result = line

        open_modified_lines.append(result)
        close_modified_lines.append(result)

    with open('Opened_file_true.txt', 'w', encoding='utf-8') as file:
        file.writelines(line + '\n' for line in open_modified_lines)

    with open('Closed_file_true.txt', 'w', encoding='utf-8') as file:
        file.writelines(line + '\n' for line in close_modified_lines)

    print("Les fichiers ont été modifié avec succès.")

treat_lines(open_lines)
treat_lines(close_lines)








