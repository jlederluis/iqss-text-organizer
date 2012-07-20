from lucene import QueryParser, IndexSearcher, StandardAnalyzer, SimpleFSDirectory, File, VERSION, initVM, Version, IndexReader, Term, BooleanQuery, BooleanClause, TermQuery, Field, IndexWriter, Document
import os
import sys
import csv
import codecs

def docs_from_filepath(searcher,reader,filepath):
    query = TermQuery(Term("path",filepath))
    scoreDocs = searcher.search(query, reader.maxDoc()).scoreDocs
    return scoreDocs

def add_metadata_to_doc(lucenedoc,fieldnames,values):
    edited_doc = Document()
    filepath = lucenedoc.get("path")
    assert filepath is not None

    # Include all original fields that are not in the list of updates
    original_fields = []
    for f in lucenedoc.getFields():
        field = Field.cast_(f)
        if field.name() not in fieldnames:
            original_fields.append(field)

    for field in original_fields:
        edited_doc.add(field)
                
    # Now, add back the unstored "contents" field
    try:
        file = open(filepath)
        contents = unicode(file.read(), 'iso-8859-1')
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

    # Now include new fields
    for idx in range(len(fieldnames)):
        edited_doc.add(Field(fieldnames[idx],values[idx],Field.Store.YES,Field.Index.NOT_ANALYZED))

    return edited_doc

def add_metadata_from_csv(searcher,reader,writer,csvfile):
    csvreader = csv.reader(codecs.open(csvfile,encoding='UTF-8'),delimiter=',',quotechar='"')
    for count,line in enumerate(csvreader):

        # read fieldnames from first line. May want to alert user if first line doesn't seem to be fieldnames
        if count == 0:
            fieldnames = line[1:]
            continue

        filepath = line[0]

        if not os.path.exists(filepath): 
            print "Could not read file {0}, skipping".format(filepath)
            continue

        scoreDocs = docs_from_filepath(searcher,reader,filepath)
        if len(scoreDocs) == 0:
            print "Could not locate document", filepath

        for scoreDoc in scoreDocs:
            print "Updating document",filepath,"..."
            old_doc = searcher.doc(scoreDoc.doc)
            edited_doc = add_metadata_to_doc(old_doc,fieldnames,line[1:])
            if edited_doc is None: 
                continue

            writer.updateDocument(Term("path",filepath),edited_doc)

    print "Optimizing index..."
    writer.optimize()

if __name__ == '__main__':
    STORE_DIR = "/home/sam/Documents/IQSS/iqss-text-organizer/lucene_index/"
    initVM()
    print 'lucene', VERSION
    directory = SimpleFSDirectory(File(STORE_DIR))

    searcher = IndexSearcher(directory, True)
    reader = IndexReader.open(directory, True)
    analyzer = StandardAnalyzer(Version.LUCENE_CURRENT)
    writer = IndexWriter(directory, analyzer, False, IndexWriter.MaxFieldLength.LIMITED)

    add_metadata_from_csv(searcher,reader,writer,sys.argv[1])

    searcher.close()
