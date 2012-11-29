import Queue
import threading
import lucene
import os
from . import searchfiles, indexfiles

class Corpus:
    scoreDocs = None
    allTerms = None
    allDicts = None

    def __init__(self, path, fields = None):
        self.path = path
        self.fields = [] if fields is None else fields

class Worker(threading.Thread):

    def __init__(self, parent, corpus, action):
        
        # This is a subclass of threading.Thread that makes sure all the processor-intensive Lucene functions take place
        # in a separate thread. To use it, pass Worker a reference to the main txtorgui instance (it will communicate back
        # to this instance using parent.write()) a Corpus class, and an "action" dictionary that tells the threading.Thread.run() 
        # method what action to take. For example, action = {'search': 'query'} would run the lucene query 'query' and action = 
        # {'export_tdm': 'outfile.csv'} would export a TDM to outfile.csv

        self.parent = parent
        self.corpus = corpus
        self.action = action
        self._init_index()

        super(Worker,self).__init__()
        
    def run(self):

        vm_env = lucene.getVMEnv()
        vm_env.attachCurrentThread()

        if "search" in self.action.keys():
            self.run_searcher(self.action['search'])
        if "export_tdm" in self.action.keys():
            self.export_TDM(self.action['export_tdm'])
        if "import_directory" in self.action.keys():
            self.import_directory(self.action['import_directory'])
        

    def _init_index(self):

        if not os.path.exists(self.corpus.path):
            os.mkdir(self.corpus.path)
        try:
            searcher = lucene.IndexSearcher(lucene.SimpleFSDirectory(lucene.File(self.corpus.path)), True)
        except lucene.JavaError:
            analyzer = lucene.StandardAnalyzer(lucene.Version.LUCENE_CURRENT)
            writer = lucene.IndexWriter(lucene.SimpleFSDirectory(lucene.File(self.corpus.path)), analyzer, True, lucene.IndexWriter.MaxFieldLength.LIMITED)
            writer.setMaxFieldLength(1048576)
            writer.optimize()
            writer.close()

        self.lucene_index = lucene.SimpleFSDirectory(lucene.File(self.corpus.path))
        self.searcher = lucene.IndexSearcher(self.lucene_index, True)
        self.reader = lucene.IndexReader.open(self.lucene_index, True)
        self.analyzer = lucene.StandardAnalyzer(lucene.Version.LUCENE_CURRENT)

    def import_directory(self, dirname):
        indexfiles.IndexFiles(dirname, self.corpus.path, self.analyzer)


    def run_searcher(self, command):
        try:
            print "Running Lucene query \"%s\"" % (command,)
            scoreDocs, allTerms, allDicts = searchfiles.run(self.searcher, self.analyzer, self.reader, command)
                
        except lucene.JavaError as e:
            if 'ParseException' in str(e):
                self.parent.write({'error': "Invalid query; see Lucene documentation for information on query syntax"})
                return
            elif 'IllegalArgumentException' in str(e):
                self.parent.write({'error': "Index is empty and cannot be queried"})
                return
            else:
                raise e

        self.parent.write({'query_results': (scoreDocs, allTerms, allDicts)})

    def export_TDM(self, outfile):
        if self.corpus.scoreDocs is None or self.corpus.allTerms is None or self.corpus.allDicts is None:
            self.parent.write({'error': "No documents selected, please run a query before exporting a TDM."})

        searchfiles.write_CTM_TDM(self.corpus.scoreDocs, self.corpus.allDicts, self.corpus.allTerms, self.searcher, outfile)
        self.parent.write({'message': "TDM exported successfully!"})