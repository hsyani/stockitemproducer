from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

import os

GAUTHFILE = 'data/client_secrets.json'
FID = "1xJYDD_-R23ag_zaRQRhmvvVKuohCsSWY"

def uploadfile(path='../itemlist', filename='20180223.csv'):

    dir = os.path.dirname(os.path.abspath(__file__)).split('userutil')[0]

    gauth = GoogleAuth()
    gauth.LoadClientConfigFile(dir + GAUTHFILE)
    drive = GoogleDrive(gauth)

    file_list = drive.ListFile({'q': "'%s' in parents and trashed=false" % FID}).GetList()

    for file1 in file_list:
        # print('title: %s, id: %s' % (file1['title'], file1['id']))
        if(file1['title'] == filename):
            print("file exits")
            return

    metadata = {
                'title' : filename,
                'parents': [{
                    "kind": "drive#stockitemlist",
                    "id": FID
                }]
    }

    f = drive.CreateFile(metadata)
    f.SetContentFile(path + '/' + filename)
    f.Upload()
    print('File Uploaded: %s, mimeType: %s' % (f['title'], f['mimeType']))


if __name__ == "__main__":
    print('test code executed')
    uploadfile()