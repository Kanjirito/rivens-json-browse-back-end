import os
'''This is here only so I don't have to remove
the files manually every time something breaks'''
PLATFORMS = ["PC", "PS4", "XB1", "SWI"]
PATH = os.path.dirname(os.path.realpath(__file__))
EDIT_PATH = PATH + "/data/{}/edited/"

for p in PLATFORMS:
    for file in os.listdir(EDIT_PATH.format(p)):
        file_path = os.path.join(EDIT_PATH.format(p), file)
        if os.path.isfile(file_path):
            os.unlink(file_path)
print("Done")
