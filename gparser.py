from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools


def gparser(path='../itemlist', filename='20180226.csv'):
    try :
        import argparse
        flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
    except ImportError:
        flags = None

    SCOPES = 'https://www.googleapis.com/auth/drive.file'
    store = file.Storage('storage.json')
    creds = store.get()

    if not creds or creds.invalid:
        print("make new storage data file ")
        flow = client.flow_from_clientsecrets('./data/client_secret.json', SCOPES)
        creds = tools.run_flow(flow, store, flags) \
                if flags else tools.run(flow, store)

    DRIVE = build('drive', 'v3', http=creds.authorize(Http()))

    FILES = (
        path+'/'+filename,
    )
    folder_id = "1xJYDD_-R23ag_zaRQRhmvvVKuohCsSWY"
    for file_title in FILES :
        print(file_title)
        file_name = file_title.split('/')[1]

        metadata = {'name': file_name,
                    'parents': [folder_id]
                    }

        res = DRIVE.files().create(body=metadata,
                                   media_body=file_name,
                                   fields='id').execute()
        if res:
            print('Uploaded "%s" ' % (file_name))

if __name__ == "__main__":
    print('test')
    gparser()