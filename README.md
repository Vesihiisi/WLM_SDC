## About This Repository
A Python 3 script to extract basic data from Wiki Loves Monuments photos on Wikimedia Commons and save them as a CSV file [compatible with batch-SDC uploader](https://github.com/Vesihiisi/batch-SDC).

Requires Pywikibot.

This is a prototyope version, currently supported countries are:
* Sweden (extracting _depicts_ from _BBR_, _Arbetslivsmuseum_, _Fornminne_ and _K-Fartyg_ templates).

The following statements are processed:
* Participant in (both local and main WLM competition, i.e. _Wiki Loves Monuments 2020_ and _Wiki Loves Monuments 2020 in Sweden_)
* Depicts (based on WLM templates)

## Usage

A file containing a list of photos, one per line (such as a Pagepile, or assembled manually) is taken as input:
````
File:Gravfält (Raä-nr Resmo 40-1) N om Mysinge hög 0513.jpg
File:Hångers källa 02.jpg
File:Uddagårdens gånggrift (RAÄ-nr Karleby 105) utgrävning 2005-06-03 0080.JPG
````

Load the file after the --data flag:
````
python3 app.py --data pagepile.txt
````

It saves the result to a csv file with the same name as the input file. The file can then be loaded into the [batch-SDC tool](https://github.com/Vesihiisi/batch-SDC) to upload the statements to Commons.
