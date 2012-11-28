import Queue
import threading
import lucene
import os
from . import searchfiles, indexfiles

class Corpus(threading.Thread):
    scoreDocs = None
    allTerms = None
    allDicts = None

    def __init__(self, parent, path, fields = None):
        self.parent = parent
        self.path = path
        self.fields = [] if fields is None else fields

        self._init_index()

    def _init_index(self):
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        try:
            searcher = lucene.IndexSearcher(lucene.SimpleFSDirectory(lucene.File(self.path)), True)
        except lucene.JavaError:
            analyzer = lucene.StandardAnalyzer(lucene.Version.LUCENE_CURRENT)
            writer = lucene.IndexWriter(lucene.SimpleFSDirectory(lucene.File(self.path)), analyzer, True, lucene.IndexWriter.MaxFieldLength.LIMITED)
            writer.setMaxFieldLength(1048576)
            writer.optimize()
            writer.close()

        self.lucene_index = lucene.SimpleFSDirectory(lucene.File(self.path))
        self.searcher = lucene.IndexSearcher(self.lucene_index, True)
        self.reader = lucene.IndexReader.open(self.lucene_index, True)
        self.analyzer = lucene.StandardAnalyzer(lucene.Version.LUCENE_CURRENT)

    def import_directory(self, dirname):
        indexfiles.IndexFiles(dirname, self.path, self.analyzer)


    def run_searcher(self, command):
        try:
            print "Running Lucene query \"%s\"" % (command,)
            new_scoreDocs, new_allTerms, new_allDicts = searchfiles.run(self.searcher, self.analyzer, self.reader, command)
            self.scoreDocs, self.allTerms, self.allDicts = new_scoreDocs, new_allTerms, new_allDicts

            # # searching within selection is disabled until we have a UI for it

            # if self.scoreDocs is None or self.allTerms is None or self.allDicts is None:
            #     pass
            # else:
            #     # intersect active search with this one
            #     print 'Searching within previous selection. To clear your selections, type "clear"'
            #     new_scoredoc_ids = [d.doc for d in new_scoreDocs]
            #     intersected_scoredoc_indices = [i for i in range(len(self.scoreDocs)) if self.scoreDocs[i].doc in new_scoredoc_ids]

            #     self.scoreDocs = [self.scoreDocs[i] for i in intersected_scoredoc_indices]
            #     self.allTerms = set(self.allTerms).intersection(new_allTerms)
            #     self.allDicts = [self.allDicts[i] for i in intersected_scoredoc_indices]
                
        except lucene.JavaError as e:
            if 'ParseException' in str(e):
                self.parent.write({'error': "Invalid query; see Lucene documentation for information on query syntax"})
                return
            elif 'IllegalArgumentException' in str(e):
                self.parent.write({'error': "Index is empty and cannot be queried"})
                return
            else:
                raise e

        self.parent.write({'query_results': (len(self.scoreDocs), len(self.allTerms))})

    def export_TDM(self, outfile):
        if self.scoreDocs is None or self.allTerms is None or self.allDicts is None:
            self.parent.write({'error': "No documents selected, please run a query before exporting a TDM."})

        searchfiles.write_CTM_TDM(self.scoreDocs, self.allDicts, self.allTerms, self.searcher, outfile)
        self.parent.write({'message': "TDM exported successfully!"})