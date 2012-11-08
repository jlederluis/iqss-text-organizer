from lucene import QueryParser, IndexSearcher, SimpleFSDirectory, File, VERSION, initVM, Version, IndexReader, Term, BooleanQuery, BooleanClause, TermQuery, Field, IndexWriter, Document
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

    # Now include new fields
    for idx in range(len(fieldnames)):
        edited_doc.add(Field(fieldnames[idx].lower(),values[idx].lower(),Field.Store.YES,Field.Index.NOT_ANALYZED))

    return edited_doc

def add_new_document_with_metadata(writer,filepath,fieldnames,values):
    file = open(filepath)
    contents = unicode(file.read(), 'UTF-8')
    file.close()

    doc = Document()
    # add name, path, and contents fields
    doc.add(Field("name", os.path.basename(filepath),
                         Field.Store.YES,
                         Field.Index.NOT_ANALYZED))
    doc.add(Field("path", os.path.realpath(filepath),
                         Field.Store.YES,
                         Field.Index.NOT_ANALYZED))
    if len(contents) > 0:
        doc.add(Field("contents", contents,
                             Field.Store.NO,
                             Field.Index.ANALYZED,
                             Field.TermVector.YES))
    else:
        print "warning: no content in %s" % filename

    for idx in range(len(fieldnames)):
        doc.add(Field(fieldnames[idx].lower(),values[idx].lower(),Field.Store.YES,Field.Index.NOT_ANALYZED))

    writer.addDocument(doc)

def add_metadata_from_csv(searcher,reader,writer,csvfile,new_files=False):
    csvreader = csv.reader(codecs.open(csvfile,encoding='UTF-8'),delimiter=',',quotechar='"')
    failed = False

    for count,line in enumerate(csvreader):

        # read fieldnames from first line. May want to alert user if first line doesn't seem to be fieldnames
        if count == 0:
            fieldnames = line[1:]
            continue

        filepath = line[0]

        if not os.path.exists(filepath): 
            print "Could not read file {0}, skipping".format(filepath)
            continue

        # if passed the new_files flag, just add documents to the index without checking whether or not they exist. This speeds things up considerably.
        if new_files:
            print "Adding document {0}".format(filepath)
            add_new_document_with_metadata(writer,filepath,fieldnames,line[1:])
            continue

        # otherwise, look for a document pointing to this filepath in the index. If it's there, update it; otherwise add it.
        scoreDocs = docs_from_filepath(searcher,reader,filepath)
        if len(scoreDocs) == 0:
            print "Could not locate document {0}; adding to index.".format(filepath)
            add_new_document_with_metadata(writer,filepath,fieldnames,line[1:])
        else:
            for scoreDoc in scoreDocs:
                print "Updating document",filepath,"..."
                old_doc = searcher.doc(scoreDoc.doc)
                edited_doc = add_metadata_to_doc(old_doc,fieldnames,line[1:])
                if edited_doc is None: 
                    continue

                writer.updateDocument(Term("path",filepath),edited_doc)

    print "Optimizing index..."
    writer.optimize()

    if failed:
        print "Could not locate index entries for some paths. Use txtorg -a [directory] to add files to index before adding metadata."

# def update_fieldname_index(available_attributes_filename, index_path, fieldnames):
#     lines = []
#     with codecs.open(available_attributes_filename, encoding='UTF-8','r') as inf:
#         for line in inf:
#             if line.startswith(index_path):
                

