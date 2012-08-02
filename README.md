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

### Selecting and exporting files

To run iqss-text-organizer in interactive mode, you can simply run `txtorg` from the command line. At the prompt (> ), you can choose how to subset the data and what to do with the subsetted data. Current supported commands are 'select', 'export', and 'quit'.

#### select

* `select [QUERY]` --- runs lucene query QUERY on the database, and prints the number of documents selected.
  * To search by a metadata field, use a query of the form `fieldname:value`. Note that since metadata fields are set to NOT_ANALYZED in the Lucene database, this must be an exact-text match,


#### export

* `export files` --- exports the full text of all selected documents to a directory.
* `export tdm` --- exports a term-document matrix for all selected documents to a file. The exported file is a CSV file where the columns are terms and the rows are files.

#### view

* `view fields` --- prints the names and values of all defined metadata fields for each of the selected documents.
