from lucene import QueryParser, IndexSearcher, SimpleFSDirectory, File, VERSION, initVM, Version, IndexReader, Term, BooleanQuery, BooleanClause, TermQuery, Field, IndexWriter, Document
import os
import sys
import csv
import codecs
import uuid

def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell, 'utf-8') for cell in row]

def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')

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
    doc.add(Field("txtorg_id", str(uuid.uuid1()),
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

def add_new_document_with_metadata_and_content(writer, fieldnames, values, content_field):
    doc = Document()
    doc.add(Field("txtorg_id", str(uuid.uuid1()),
                         Field.Store.YES,
                         Field.Index.NOT_ANALYZED))

    for idx, name in enumerate(fieldnames):
        if name == content_field: 
            doc.add(Field(fieldnames[idx].lower(),values[idx].lower(),Field.Store.YES,Field.Index.ANALYZED,Field.TermVector.YES))
        else:
            doc.add(Field(fieldnames[idx].lower(),values[idx].lower(),Field.Store.YES,Field.Index.NOT_ANALYZED))

    writer.addDocument(doc)

def add_metadata_from_csv(searcher,reader,writer,csvfile,new_files=False):
    csvreader = unicode_csv_reader(codecs.open(csvfile, encoding='UTF-8'), delimiter=',', quotechar='"')
    failed = False

    successful_rows = 0
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
                successful_rows += 1
                old_doc = searcher.doc(scoreDoc.doc)
                edited_doc = add_metadata_to_doc(old_doc,fieldnames,line[1:])
                if edited_doc is None: 
                    continue

                writer.updateDocument(Term("path",filepath),edited_doc)
            
    writer.optimize()

    # return the number of rows changed
    return successful_rows


def add_metadata_and_content_from_csv(searcher, reader, writer, csvfile, content_field):
    csvreader = unicode_csv_reader(codecs.open(csvfile, encoding='UTF-8'),delimiter=',',quotechar='"')

    successful_rows = 0
    for count,line in enumerate(csvreader):

        # read fieldnames from first line. May want to alert user if first line doesn't seem to be fieldnames
        if count == 0:
            fieldnames = line
            if content_field not in fieldnames: raise ValueError
            continue

        add_new_document_with_metadata_and_content(writer, fieldnames, line, content_field)
        successful_rows += 1
            

    print "Optimizing index..."
    writer.optimize()

    # return the number of rows changed
    return successful_rows