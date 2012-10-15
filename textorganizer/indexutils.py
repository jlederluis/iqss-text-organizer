from lucene import \
    SimpleFSDirectory, File, IndexReader, Term, Term, IndexWriter, Version, StandardAnalyzer, TermQuery

import threading, sys, time, os, csv, re, codecs

class IndexCleaner():
    def __init__(self,dir_name):
        self.directory = SimpleFSDirectory(File(dir_name))
        self.reader = IndexReader.open(self.directory, True)
        self.writer = IndexWriter(self.directory, StandardAnalyzer(Version.LUCENE_CURRENT), False, IndexWriter.MaxFieldLength.LIMITED)

    def get_broken_index_items(self):
        l = []
        for i in xrange(self.reader.maxDoc()):
            if self.reader.isDeleted(i): continue
            doc = self.reader.document(i)
            if not os.path.isfile(doc.get("path")):
                l.append(doc)
        return l

    def cleanup_index(self):
        broken_docs = self.get_broken_index_items()
        print "%s broken links found. Enter 'v' to view, 'd' to delete all index items with broken links, or 'q' to cancel" % (len(broken_docs),)
        while True:
            choice = raw_input('> ')
            if choice not in ['v', 'd', 'q']:
                print "Invalid input. Enter 'v' to view, 'd' to delete all index items with broken links, or 'q' to cancel"
                continue
            elif choice == 'v':
                for d in broken_docs:
                    print d.get("path")
                print "Enter 'd' to delete all index items with broken links, or 'q' to cancel"
                continue
            elif choice =='q':
                return
            elif choice == 'd':
                break
        
        for d in broken_docs:
            fp = d.get("path")
            print "Deleting", fp
            self.writer.deleteDocuments(Term("path",fp))

        self.writer.close()
