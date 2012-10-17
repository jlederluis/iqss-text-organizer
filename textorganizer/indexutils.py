from lucene import \
    SimpleFSDirectory, File, IndexReader, Term, Term, IndexWriter, Version, StandardAnalyzer, TermQuery, IndexSearcher, Document, Field

import threading, sys, time, os, csv, re, codecs

class IndexManager():
    def __init__(self,dir_name):
        self.directory = SimpleFSDirectory(File(dir_name))
        self.reader = IndexReader.open(self.directory, True)
        self.searcher = IndexSearcher(self.directory, True)

    def get_broken_index_items(self):
        l = []
        for i in xrange(self.reader.maxDoc()):
            if self.reader.isDeleted(i): continue
            doc = self.reader.document(i)
            if not os.path.isfile(doc.get("path")):
                l.append(doc)
        return l

    def cleanup_index(self):
        writer = IndexWriter(self.directory, StandardAnalyzer(Version.LUCENE_CURRENT), False, IndexWriter.MaxFieldLength.LIMITED)
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
            writer.deleteDocuments(Term("path",fp))

        writer.close()


    def reindex(self, scoreDocs, analyzer):
        
        writer = IndexWriter(self.directory, analyzer, False, IndexWriter.MaxFieldLength.LIMITED)
        
        for scoreDoc in scoreDocs:
            doc = self.searcher.doc(scoreDoc.doc)
            filepath = doc.get('path')
            new_doc = self.reassemble_doc(doc,filepath)
            writer.updateDocument(Term("path",filepath),new_doc,analyzer)

        print "Optimizing index..."
        writer.optimize()
        writer.close()
            
    def reassemble_doc(self, lucenedoc, filepath):

        assert filepath is not None

        edited_doc = Document()
        for f in lucenedoc.getFields():
            edited_doc.add(Field.cast_(f))
            
                    
        # Now, add back the unstored "contents" field
        try:
            file = open(filepath)
            contents = unicode(file.read(), 'UTF-8')
            file.close()

            if len(contents) > 0:
                edited_doc.add(Field("contents", contents,
                                     Field.Store.NO,
                                     Field.Index.ANALYZED,
                                     Field.TermVector.YES))
            else:
                print "warning: no content in %s" % filename
        except:
            print "Could not read file; skipping"
            return None

        return edited_doc
