#!/usr/bin/python
# 
# The script walks through the folder recursively and finds duplicate files 
# that are either whitelisted or not blacklisted. To run the script:
#   python filewalker.py /home/user/folder
#
from pathlib import Path, PurePath
from datetime import datetime, timezone
import hashlib
import sqlite3
import sys
import time

class DuplicateFinder:

    UTF_8_BOM = "\xEF\xBB\xBF"

    files = []
    stack = []

    dir_blacklist  = [ ".git", "target" ]
    file_blacklist = [ ".gif", ".png", ".jpg", ".jpeg", ".ico", ".xml", ".htm", ".html", ".md", ".gitignore" ]
    file_whitelist = []

    empty_files    = []

    chunk_size = 256
    count = 0

    def openOutput(self, filename):
        if (Path(filename).is_file()):
            self.outfile = open(filename, "a", encoding="utf-8");
        else:
            self.outfile = open(filename, "w", encoding="utf-8");
            self.outfile.write("Path;Absolute Path;MD5;Filename;Extension;Modified;Size\n")

    def closeOutput(self):
        self.outfile.close()

    def write_to_file(self, f):
        self.outfile.write(f"{f[0]};{f[1]};{f[2]};{f[3]};{f[4]};{f[5]};{f[6]}\n")

    def dir_blacklisted(self, d):
        for e in self.dir_blacklist:
            if str(d).find(e) > 0:
                return True
        return False


    def file_blacklisted(self, f):
        return ( f.suffix.lower() in self.file_blacklist )


    def file_whitelisted(self, f):
        return ( f.suffix.lower() in self.file_whitelist )


    def file_of_interest(self, f):
        if (f.stat().st_size == 0):
            self.empty_files.append(f)
            return False
            
        if (self.file_whitelist):
            return self.file_whitelisted(f)
        else:
            return not (self.file_blacklisted(f)) 


    def is_regular_file(self, p):
        return (p.is_file() &  (not p.is_symlink()))


    def md5(self, f):
        m = hashlib.md5()
        with open(f, "rb") as f:
            while True:
                bytes = f.read(self.chunk_size)
                if bytes:
                    m.update(bytes)
                else:
                    break
        return m.hexdigest()


    def list_files_in_dir(self, path):
        try:
            for p in path.iterdir():
                absName = p.resolve()
                try:
                    if absName.is_dir():
                        if not self.dir_blacklisted(absName):
                            self.stack.append(absName)
                    elif self.is_regular_file(absName):
                        self.count+=1
                        if self.file_of_interest(absName):
                            pp = PurePath(absName);
                            st = p.stat()
                            modified = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
                            #print("File: {} Ext: {} Size: {} MTime: {}".format(pp.name, pp.suffix, st.st_size, modified))                        
                            self.write_to_file((
                                path,                       # path                        
                                absName,                    # absolute path
                                "", #self.md5(str(absName)),     # md5
                                pp.name,                    # name
                                pp.suffix,                  # extension
                                modified,                   # modified time
                                st.st_size                  # size
                                ))
                            #self.files.append((absName, self.md5(str(absName))))

                except Exception as ex:
                    print("         Failed to process file {0} with error {1}".format(absName.name, ex))
        except Exception as ex:
            print("*** Failed to process folder {0} with error {1}".format(path.name, ex))


    def start(self):
        self.tsbegin = time.time()
        while True:
            if self.stack:
                e = self.stack.pop()
                self.list_files_in_dir(e)
            else:
                break
                
        #self.files.sort(key=lambda f: f[1])
        self.tsend = time.time()


    def addInputFolder(self, *args):
        for f in args:
            self.stack.append(Path(f));
            

    def setFileBlacklist(self, blacklist):
        self.file_blacklist = blacklist
    
    
    def addFileBlacklist(self, ext):
        self.file_blacklist.append(ext)

        
    def setFileWhitelist(self, whitelist):
        self.file_whitelist = whitelist
        
        
    def addFileWhitelist(self, ext):
        self.file_whitelist.append(ext)        
        
        
    def setDirBlacklist(self, blacklist):
        self.dir_blacklist = blacklist

        
    def addDirBlacklist(self, dir):
        self.dir_blacklist.append(dir)        

        
    def getResult(self):
        return self.files
        
    def getEmptyFiles(self):
        return self.empty_files


    def getNumberOfFilesProcessed(self):
        return self.count


    def getTimeElapsed(self):
        return (self.tsend-self.tsbegin)*1000


    def printResult(self):
         i = 0
         j = -1
         s = ""

         for (p, m) in self.files:
             if s != m:
                if i < j:
                   for f in self.files[i:j+1]:
                      print(f[0])
                   print("\n")
                j += 1
                i = j
                s = m
             else:
                j += 1


if __name__ == '__main__':
    if len(sys.argv) > 1:
        finder = DuplicateFinder()
        
        for i in range(1,len(sys.argv)):
            finder.addInputFolder(sys.argv[i])

        finder.setDirBlacklist([ ".git" ])
        finder.setFileBlacklist([ ".gif", ".png", ".jpg", ".jpeg", ".ico", ".xml", ".htm", ".html", ".md" ])
        finder.setFileWhitelist([])
        finder.openOutput("result.csv")
        finder.start()
        finder.printResult()
        finder.closeOutput()
        
        print("{0} files processed".format(finder.getNumberOfFilesProcessed())) 
        print("Completed in {0} ms".format(finder.getTimeElapsed())) 
        
        print("Empty files: " + str(finder.getEmptyFiles()))
