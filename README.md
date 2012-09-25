iqss-text-organizer
===================

A simple python-based command line tool designed to make organizing data for textual analysis easy and scalable. Creates
an Apache Lucene index to which documents can be added. The user can select documents using Lucene queries. Selected 
documents can be exported in their original format or as a term-document matrix.

SETUP
----------

To use this program, clone the git repository into a directory on your computer and then add the directory to your PATH environment variable. On Ubuntu, this means editing your .bashrc file to contain the line 

export PATH=/path/to/iqss-text-organizer:$PATH

Now you can use the command `txtorg` to run the program from anywhere on your computer. It will create the Lucene index in the directory in which it is installed.

To use PyLucene, please see the installation instructions here:
http://lucene.apache.org/pylucene/install.html

USAGE
-----------

### Adding files to the database

From anywhere on your computer, you can run the command `txtorg -a [DIRECTORY]` to add all the files in `DIRECTORY` (and subdirectories) to the database. 

### Adding metadata to files
Once you have imported files to the database, you can add metadata to the files by running `txtorg -c [file.csv]` where `file.csv` is a file containing a list of metadata fields and values for each file. The file should be in the format of `sample_metadata_file.csv` in the root folder of this repository.

Since `txtorg -c` must remove, edit, and re-add each individual document, it can take a long time to run for large corpora. If this is a problem, you can use the command `txtorg -C [file.csv]` instead of `txtorg -a [DIRECTORY]` to do the initial import. This will import each document in the CSV file, as well as the metadata contained.

### Custom Analyzers
Adding files with the command `txtorg -a` or `txtorg -C` will index the documents using the default analyzer. This analyzer is appropriate only for English text, recognizes only one-word tokens, and does not perform any stemming. Various other analyzers are available that allow indexing documents in other languages, or that perform various processing steps like stemming. To import documents using an analyzer other than the default, use the `-n` switch when importing. For instance, `txtorg -n -a .` imports all documents in the current working directory, but it allows the user to choose which analyzer Lucene will use for indexing. Currently available analyzers include:

* StandardAnalyzer (default)
* SmartChineseAnalyzer (use for Chinese text)
* PorterStemmerAnalyzer
  * This analyzer includes all n-grams (phrases) listed in the file `phrases.txt` as tokens for indexing and TDM export. For instance, if `phrases.txt` included the line `Barack Obama`, then exported TDMs would contain a column for `Barack Obama`. Using the default analyzer, this would be split over two columns: `Barack` and `Obama`. To enable this functionality, place the file `phrases.txt`, containing one entry per line, in the same directory as the `txtorg` executable.
  * This analyzer also performs a Porter Stemming algorithm on all documents so that, for example, the words `document` and `documents` are counted as the same term in the TDM.


### Selecting and exporting files

To run iqss-text-organizer in interactive mode, you can simply run `txtorg` from the command line. At the prompt (> ), you can choose how to subset the data and what to do with the subsetted data. Current supported commands are `select`, `export`, `view`, `analyzer`, and `quit`.

#### select

* `select [QUERY]` --- runs lucene query QUERY on the database, and prints the number of documents selected.
  * To search by a metadata field, use a query of the form `fieldname:value`. Note that since metadata fields are set to NOT_ANALYZED in the Lucene database, this must be an exact-text match,


#### export

* `export files` --- exports the full text of all selected documents to a directory.
* `export tdm` --- exports a term-document matrix for all selected documents. This command creates two files; one containing the TDM in the format `filepath, name, number of terms, term_id1: count1, [term_id2: count2], [...]`, and the other containing the vocabulary of all selected documents in the format `term_id, term`.

#### view

* `view fields` --- prints the names and values of all defined metadata fields for each of the selected documents.

#### analyzer

* `analyzer` --- prints a list of all available analyzers and allows the user to choose one for use in searching/exporting.
