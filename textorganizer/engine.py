import Queue
import threading
import lucene
import codecs
import datetime
import os
from . import searchfiles, indexfiles, indexutils, addmetadata

class Corpus:
    scoreDocs = None
    allTerms = None
    allDicts = None

    def __init__(self, path, analyzer_str = None, field_dict = None):
        self.path = path
        self.field_dict = {} if field_dict is None else field_dict
        if analyzer_str is None: analyzer_str = "StandardAnalyzer"

        self.analyzer_str = analyzer_str
        self.analyzer = self.get_analyzer_from_str(analyzer_str)
        

    def get_analyzer_from_str(self, analyzer_str):
        if analyzer_str == 'StandardAnalyzer':
            return lucene.StandardAnalyzer(lucene.Version.LUCENE_CURRENT)



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
        if "import_csv" in self.action.keys():
            self.import_csv(self.action['import_csv'])
        if "import_csv_with_content" in self.action.keys():
            self.import_csv_with_content(*self.action['import_csv_with_content'])
        if "rebuild_metadata_cache" in self.action.keys():
            self.rebuild_metadata_cache(*self.action['rebuild_metadata_cache'])
        if "reindex" in self.action.keys():
            self.reindex()
        

    def _init_index(self):

        if not os.path.exists(self.corpus.path):
            os.mkdir(self.corpus.path)
        try:
            searcher = lucene.IndexSearcher(lucene.SimpleFSDirectory(lucene.File(self.corpus.path)), True)
        except lucene.JavaError:
            analyzer = self.corpus.analyzer
            writer = lucene.IndexWriter(lucene.SimpleFSDirectory(lucene.File(self.corpus.path)), analyzer, True, lucene.IndexWriter.MaxFieldLength.LIMITED)
            writer.setMaxFieldLength(1048576)
            writer.optimize()
            writer.close()

        self.lucene_index = lucene.SimpleFSDirectory(lucene.File(self.corpus.path))
        self.searcher = lucene.IndexSearcher(self.lucene_index, True)
        self.reader = lucene.IndexReader.open(self.lucene_index, True)
        self.analyzer = self.corpus.analyzer



    def import_directory(self, dirname):
        indexfiles.IndexFiles(dirname, self.corpus.path, self.analyzer)

    def import_csv(self, csv_file):
        writer = lucene.IndexWriter(lucene.SimpleFSDirectory(lucene.File(self.corpus.path)), self.analyzer, False, lucene.IndexWriter.MaxFieldLength.LIMITED)
        changed_rows = addmetadata.add_metadata_from_csv(self.searcher, self.reader, writer, csv_file, new_files=True)
        writer.close()
        self.parent.write({'message': "CSV import complete: %s rows added." % (changed_rows,)})

    def import_csv_with_content(self, csv_file, content_field):
        writer = lucene.IndexWriter(lucene.SimpleFSDirectory(lucene.File(self.corpus.path)), self.analyzer, False, lucene.IndexWriter.MaxFieldLength.LIMITED)
        changed_rows = addmetadata.add_metadata_and_content_from_csv(self.searcher, self.reader, writer, csv_file, content_field)
        writer.close()
        self.parent.write({'message': "CSV import complete: %s rows added." % (changed_rows,)})        

    def reindex(self):
        writer = lucene.IndexWriter(lucene.SimpleFSDirectory(lucene.File(self.corpus.path)), self.corpus.analyzer, False, lucene.IndexWriter.MaxFieldLength.LIMITED)
        indexutils.reindex_all(self.reader, writer, self.corpus.analyzer)
        writer.optimize()
        writer.close()
        self.parent.write({'message': "Reindex successful. Corpus analyzer is now set to %s." % (self.corpus.analyzer_str,)})
        self.parent.write({'status': "Ready!"})

    def run_searcher(self, command):
        start_time = datetime.datetime.now()
        try:
            self.parent.write({'status': 'Running Lucene query %s' % (command,)})
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

        end_time = datetime.datetime.now()
        self.parent.write({'query_results': (scoreDocs, allTerms, allDicts)})
        self.parent.write({'status': 'Query completed in %s seconds' % ((end_time - start_time).microseconds*.000001)})

    def export_TDM(self, outfile):
        if self.corpus.scoreDocs is None or self.corpus.allTerms is None or self.corpus.allDicts is None:
            self.parent.write({'error': "No documents selected, please run a query before exporting a TDM."})
            return

        searchfiles.write_CTM_TDM(self.corpus.scoreDocs, self.corpus.allDicts, self.corpus.allTerms, self.searcher, outfile)
        self.parent.write({'message': "TDM exported successfully!"})

    def rebuild_metadata_cache(self, cache_filename, corpus_directory):
        metadata_dict = indexutils.get_fields_and_values(self.reader)
        # finds the section of the old file to overwrite, and stores the old file in memory
        old_file = []
        start = -1
        stop = -1
        idx = 0
        with codecs.open(cache_filename, 'r', encoding='UTF-8') as inf:
            for idx, line in enumerate(inf):
                if "CORPUS:" in line and line.strip().endswith(corpus_directory):
                    start = idx
                elif "CORPUS:" in line and start != -1 and stop == -1:
                    stop = idx
                old_file.append(line)
            if stop == -1: stop = idx+1

        new_segment = ["CORPUS: " + corpus_directory + '\n', "_ANALYZER: " + self.corpus.analyzer_str +'\n']

        for k in metadata_dict.keys():
            metadata_dict[k] = metadata_dict[k]
            # sanitize various characters from input. 
            new_segment.append(k + ": [" + "|".join(metadata_dict[k]).replace('\n','').replace(']','').replace('[','').replace(':','') + "]\n")

        if start == -1:
            new_file = old_file + new_segment
        else:
            new_file = old_file[:start] + new_segment + old_file[stop:]

        with codecs.open(cache_filename, 'w', encoding='UTF-8') as outf:
            for line in new_file:
                outf.write(line)

        self.parent.write({'rebuild_cache_complete': None})
        self.parent.write({'message': 'Finished rebuilding cache file.'})