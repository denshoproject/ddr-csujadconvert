import sys, datetime, csv, shutil, os, re
import argparse
import collections

DESCRIPTION_SHORT = """Tool to convert CSUJAD CONTENTdm CSV to DDR import CSV format."""

DESCRIPTION_LONG = """
Converts CSUJAD CONTENTdm CSV file to correct format for DDR import.

USAGE
$ ddr-csujadconvert-entities DDR_COLLECTION_ID CSUJAD_CSV_INPUT_FILE DDR_CSV_OUTPUT_BASE_PATH
$ ddr-csujadconvert-entities ddr-csujad-1 ./raw/csujaddata.csv ./transformed
---"""

# Constants
TOPDATAPATH = './data/topicmapping.csv'
FACDATAPATH = './data/facilities.csv'
GENREDATAPATH = './data/genres.csv'
LOGFILE = './logs/{:%Y%m%d-%H%M%S}-csujadconvert-entities.log'.format(datetime.datetime.now()) 

CSU_FIELDS = ['Local ID', 'Project ID', 'Title/Name', 'Creator', 'Date Created', 'Description', 'Location', 'Facility', 'Subjects', 'Type', 'Genre', 'Language', 'Source Description', 'Collection', 'Collection Finding Aid', 'Collection Description', 'Digital Format', 'Project Name', 'Contributing Repository', 'View Item', 'Rights', 'Notes', 'Object File Name', 'OCLC number', 'Date created', 'Date modified', 'Reference URL', 'CONTENTdm number', 'CONTENTdm file name', 'CONTENTdm file path', 'DDR Rights', 'DDR Credit Text']

DDR_ENTITY_FIELDS =  ['id','status','public','title','description','creation','location','creators','language','genre','format','extent','contributor','alternate_id','digitize_person','digitize_organization','digitize_date','credit','topics','persons','facility','chronology','geography','parent','rights','rights_statement','notes','sort','signature_id']

CSU_DELIM = ';'

# Support functions

def load_data(csvpath):
    csvfile = open(csvpath, 'rU')
    csvreader = csv.DictReader(csvfile)
    data = []
    for row in csvreader:
        data.append(row)
    return data

def build_dict(seq, key):
    return dict((d[key], dict(d, index=index)) for (index, d) in enumerate(seq))

def write_log(message):
    logfile = open(LOGFILE,'a')
    logfile.write(message + "\n")
    logfile.close()
    return

def _make_attribute_list(rawatt):
    return [x.strip() for x in rawatt.split(CSU_DELIM)]

# Process fields

def get_alternate_id(rawlocalid, rawprojectid):
    alternate_id = "CSUJAD Local ID: {}, CSUJAD Project ID: {}".format(rawlocalid, rawprojectid)
    return alternate_id

def get_description(rawdescription, rawreferenceurl, rawlocalid):
    description = "{0} See this object in the California State Universities Japanese American Digitization project site: <a href=\"{1}\" target=\"_blank\" rel=\"noopener noreferrer\">{2}</a>".format(rawdescription, rawreferenceurl, rawlocalid)
    return description

def get_facility(rawfacility):
    facility = ''
    csufacilities = _make_attribute_list(rawfacility)
    for csufacility in csufacilities:
        if csufacility:
            checkfacility = csufacility.split('--')[1]
            for row in facdata:
                if row['title'] == checkfacility:
                    facility += 'term:' + row['title'] + '|id:' + row['DESC_camp_id'] + ';'
                    break
    return facility

def get_topics(rawtopics):
    topics = ''
    csutopics = _make_attribute_list(rawtopics)
    for csutopic in csutopics:
        for row in topdata:
            if row['CSU term'] == csutopic:
                #topics += 'term:' + row['Densho term'] + '|id:' + row['Densho term ID'] + ';'
                topics += 'term:' + row['CSU term'].replace('--',': ') + '|id:' + row['Densho term ID'] + ';'
                break
    return topics

#CSU data export may have multiple values for format; if *any* value maps to an av type, we use that
#TODO: better parsing for oral history vs. plain av types
def get_format(rawtypes):
    csuformats = _make_attribute_list(rawtypes)
    ddrformats = []
    formatmap = [['Text', 'doc'], ['Image','img'], ['Moving Image','av'],['Sound','av']]
    for csuformat in csuformats:
        for item in formatmap:
            if item[0] == csuformat:
                ddrformats.append(item[1])
                break
    if 'av' in ddrformats:
        ddrformat = 'av'
    else:
        ddrformat = ddrformats[0]
    return ddrformat

def get_genre(rawgenres):
    genres = []
    csugenres = _make_attribute_list(rawgenres)
    for csugenre in csugenres:
        for row in genredata:
            if row['title'].lower() == csugenre.lower():
                genres.append(row['id'])
                break
    if 'interview' in genres:
        genre = 'interview'
    elif not genres:
        genre = genres[0]
    else:
        genre = 'misc_document'
    return genre

def get_contributor(rawcontributor):
    contributor = rawcontributor.split(CSU_DELIM)[0].strip()
    return contributor

def get_notes(rawnotes, rawcreated, rawmodified):
    notes = "[csujad_Notes: {}] [csujad_Date created: {}] [csujad_Date modified: {}]".format(rawnotes, rawcreated, rawmodified)
    return notes

# Main
# Get script args
ddrcollectionid = sys.argv[1]
csucsvpath = sys.argv[2]
try:
    outputpath = sys.argv[3]
except IndexError:
    outputpath = './'


print ('{} : Begin run.'.format(datetime.datetime.now()))

# Load data
print ('{} : Loading data...'.format(datetime.datetime.now()))
facdata = load_data(FACDATAPATH)
topdata = load_data(TOPDATAPATH)
genredata = load_data(GENREDATAPATH)
csudata = load_data(csucsvpath)
print ('{} : Data loaded. CSU data: {} rows; topic data: {} rows; facility data: {} rows; genre data: {}.'.format(datetime.datetime.now(), str(len(csudata)), str(len(topdata)), str(len(facdata)), str(len(genredata))))

#print ('csudata first row: {}'.format(csudata[0]))
#print ('csudata first row \'Local ID\': {}'.format(csudata[0]['Local ID']))

rownum = 0
processedobject = 0
partobject = 0
for rawentity in csudata:
    rownum += 1
    #check that row contains an object record; not a part of compound object
    if rawentity['Project ID'] != '':
        outfile = os.path.join(outputpath, '{}-entities-{:%Y%m%d-%H%M}.csv'.format(ddrcollectionid, datetime.datetime.now()))
        #write header row if first pass
        if not os.path.isfile(outfile):
            odatafile = open(outfile,'w')
            outwriter = csv.writer(odatafile)
            outwriter.writerow(DDR_ENTITY_FIELDS)
            odatafile.close()

        #setup row dict
        converted = collections.OrderedDict.fromkeys(DDR_ENTITY_FIELDS)

        #convert data
        converted['alternate_id'] = get_alternate_id(rawentity['Local ID'], rawentity['Project ID'])
        converted['title'] = rawentity['Title/Name']
        converted['creators'] = rawentity['Creator']
        converted['creation'] = rawentity['Date Created']
        converted['description'] = get_description(rawentity['Description'], rawentity['Reference URL'], rawentity['Local ID'])
        converted['location'] = rawentity['Location']
        converted['facility'] = get_facility(rawentity['Facility'])
        converted['topics'] = get_topics(rawentity['Subjects'])
        converted['format'] = get_format(rawentity['Type'])
        converted['genre'] = get_genre(rawentity['Genre'])
        converted['language'] = rawentity['Language']
        converted['extent'] = rawentity['Source Description']
        converted['contributor'] = get_contributor(rawentity['Contributing Repository'])
        converted['rights_statement'] = rawentity['Rights']
        converted['notes'] = get_notes(rawentity['Notes'], rawentity['Date created'], rawentity['Date modified'])
        converted['rights'] = rawentity['DDR Rights']
        converted['credit'] = rawentity['DDR Credit Text']

        converted['status'] = 'completed'
        converted['public'] = '1'

        processedobject +=1

        converted['id'] = ddrcollectionid + '-' + str(processedobject)

        #write converted data
        odatafile = open(outfile,'a')
        outwriter = csv.writer(odatafile)
        outwriter.writerow(converted.values())
        odatafile.close()
    else:
        partobject +=1
        print ('{} : Row #{} did not have \'Project ID\'. Looks like a compound object part.'.format(datetime.datetime.now(), rownum))

print ('{} : Run ended.'.format(datetime.datetime.now()))
print ('{} : {} rows processed. {} new entity rows created. {} partial object rows discarded.'.format(datetime.datetime.now(), rownum, processedobject, partobject))

#end
