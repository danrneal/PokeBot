import json

dicts = {}
users = []
male_only = [
    'nidoranm', 'nidorino', 'nidoking', 'hitmonlee', 'hitmonchan',
    'tauros', 'tyrogue', 'hitmontop'
]
female_only = [
    'nidoranf', 'nidorina', 'nidoqueen', 'chansey', 'kangaskhan', 'jynx',
    'smoochum', 'militank', 'blissey'
]
genderless = [
    'magnemite', 'magneton', 'voltorb', 'electrode', 'staryu', 'starmie',
    'porygon', 'porygon2'
]

with open('./notifications.txt', 'r') as notifications_file:
    next(notifications_file)
    for line in notifications_file:
        linelist = line.split()
        for user_id in linelist[2:]:
            if user_id not in users:
                users.append(user_id)

count = 0
for user in users:
    count += 1
    if count % 10 == 0:
        print(str(round(100 * count/len(users))) + '% done')
    dicts[user] = {'pokemon': {}, 'paused': False, 'areas': []}
    with open('./notifications.txt', 'r') as notifications_file:
        next(notifications_file)
        skip = ''
        for line in notifications_file:
            linelist = line.split()
            if (user in linelist[2:] and
                linelist[0] not in genderless and
                linelist[0] not in male_only and
                linelist[0] not in female_only and
                    linelist[0] != skip):
                dicts[user]['pokemon'][linelist[0]] = {
                    'male': {
                        'cp': '10',
                        'lvl': '1',
                        'iv': linelist[1]
                        },
                    'female': {
                        'cp': '10',
                        'lvl': '1',
                        'iv': linelist[1]
                        }
                    }
                skip = linelist[0]
            elif (user in linelist[2:] and
                  linelist[0] in genderless and
                  linelist[0] != skip):
                dicts[user]['pokemon'][linelist[0]] = {
                    'genderless': {
                        'cp': '0',
                        'lvl': '1',
                        'iv': linelist[1]
                        }
                    }
                skip = linelist[0]
            elif (user in linelist[2:] and
                  linelist[0] in male_only and
                  linelist[0] != skip):
                dicts[user]['pokemon'][linelist[0]] = {
                    'male': {
                        'cp': '0',
                        'lvl': '1',
                        'iv': linelist[1]
                        }
                    }
                skip = linelist[0]
            elif (user in linelist[2:] and
                  linelist[0] in female_only and
                  linelist[0] != skip):
                dicts[user]['pokemon'][linelist[0]] = {
                    'female': {
                        'cp': '0',
                        'lvl': '1',
                        'iv': linelist[1]
                        }
                    }
                skip = linelist[0]
    with open('./paused.txt', 'r') as paused_file:
        next(paused_file)
        for line in paused_file:
            linelist = line.split()
            if user in linelist[1:] and linelist[0] == 'paused':
                dicts[user]['paused'] = True

with open('users.json', 'w') as fp:
    json.dump(dicts, fp, indent=4)
