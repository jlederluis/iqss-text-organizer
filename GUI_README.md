This readme is for the GUI version of txtorg.

Getting Started
==============

Installation
--------------

Install the package as you would any other Python package (PyPI, Distutils, etc). For example...

- Navigate to the directory in which you cloned the repo. This should contain setup.py.

- Enter 'python setup.py install'

Launching Txtorg
--------------

From the command line, enter 'txtorg'

Using Txtorg
--------------
 
- Create a new corpus. To do so, click File -> New Corpus. You'll be prompted to select a place to store the corpus.

- The corpus should show up in the corpus window. Now select your corpus by clicking on it.

- Next, import some documents. With your corpus highlighted, click Corpus -> Import Documents. Next, select the format of your corpus.

To import all the documents in a directory, select 'Import an entire directory'. These must be .txt files.

To import documents from a .csv with a field containing the filepaths of all the documents in the corpus, select 'Import from a CSV file (not including content)'. Then select the field containing the filepaths.

To import documents from a .csv with a field containing the full documents, select 'Import from a CSV file (including content)'. Then select the field containing the documents.

- The documents should be imported. If successful, a window will pop up and tell you so.

- Now pick your analyzer. Corpus -> Change Analyzer. Just click on the analyzer you want and then click OK. To see the difference between the different analyzers, enter text in the sample window, and select an analyzer. The tokens output by that analzyer will appear in the main window.

- Now rebuild the index file by clicking Corpus -> Rebuild Index File.

- Now select docs. To select all the docs in the corpus, search for 'all'. To subset, use a valid Lucene query.

- To export the tdm for the selected docs, click Export TDM. Then select the format.

STM format will write a TDM, metadata file, and vocab list. The tdm will be in the format '[M] [term_1]:[count_1] [term_2]:[count_2] ... [term_N]:[count_3]', where [M] is the number of unique terms in the document, [term_i] is an integer associated with the i-th term in the vocabulary, and [count_i] is how many times the i-th term appeared in the document.

CTM format will be the same as STM format, except it will be delimited by commas and will include a field for the lucene ID.

Flat CSV will export a TDM, metadata file, and vocab list. The tdm will be a flat csv, with lots of zeros.


