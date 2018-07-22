import io
import csv as csvlib

class csv(object):
    file_handle = None
    def create(name = "flashget.csv"):
        global file_handle
        file_handle = io.open(name, 'w', encoding="utf-8")

    def append(downloadPath, url):
        global file_handle
        spamwriter = csvlib.writer(file_handle, delimiter=',', quotechar='"', quoting=csvlib.QUOTE_ALL)
        spamwriter.writerow([downloadPath, url])
        # file_handle.write('"%s","%s"\n' % (downloadPath.replace('"', '\\"'), url.replace('"', '\\"')))

    def read(name = "flashget.csv"):
        with io.open(name, encoding="utf-8") as f:
            data = csvlib.reader(f, delimiter=',', quotechar='"')
            return list(data)

    def read_combined(name = "flashget.csv"):
        data = csv.read(name)
        combined = {}
        for line in data:
            entry = combined.get(line[0], [])
            combined[line[0]] = entry + [line[1]]
        return combined

    def close():
        global file_handle
        file_handle.close()
