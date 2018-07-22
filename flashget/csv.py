import io

file_handle = None

class csv(object):
    def create():
        global file_handle
        file_handle = io.open("flashget.csv", 'w', encoding="utf-8")

    def append(downloadPath, url):
        global file_handle
        file_handle.write('"%s", "%s"\n' % (downloadPath.replace('"', '\\"'), url.replace('"', '\\"')))

    def close():
        global file_handle
        file_handle.close()
