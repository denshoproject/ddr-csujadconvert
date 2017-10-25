import sys, datetime, csv, shutil, os, re
import argparse
import collections

DESCRIPTION_SHORT = """Tool to convert CSUJAD CONTENTdm CSV to DDR import CSV format."""

DESCRIPTION_LONG = """
Converts CSUJAD CONTENTdm CSV file to correct format for DDR import.

USAGE
$ ddr-csujadconvert-entities DDR_COLLECTION_ID CSUJAD_CSV_INPUT_FILE DDR_CSV_OUTPUT_BASE_PATH CREDIT_TEXT
$ ddr-csujadconvert-entities ddr-csujad-1 ./raw/csujaddata.csv ./transformed 'Courtesy of the Ikemoto Collection'
---"""

# Constants
TOPDATAPATH = './data/topicmapping.csv'
FACDATAPATH = './data/facilities.csv'
LOGFILE = './logs/{:%Y%m%d-%H%M%S}-csujadconvert-entities.log'.format(datetime.datetime.now()) 

CSU_FIELDS = ['Local ID', 'Project ID', 'Title/Name', 'Creator', 'Date Created', 'Description', 'Location', 'Facility', 'Subjects', 'Type', 'Genre', 'Language', 'Source Description', 'Collection', 'Collection Finding Aid', 'Collection Description', 'Digital Format', 'Project Name', 'Contributing Repository', 'View Item', 'Rights', 'Notes', 'Object File Name', 'OCLC number', 'Date created', 'Date modified', 'Reference URL', 'CONTENTdm number', 'CONTENTdm file name', 'CONTENTdm file path']

DDR_ENTITY_FIELDS =  ['id','status','public','title','description','creation','location','creators','language','genre','format','extent','contributor','alternate_id','digitize_person','digitize_organization','digitize_date','credit','topics','persons','facility','chronology','geography','parent','rights','rights_statement','notes','sort','signature_id']

CSU_DELIM = ';'

# Support functions

def load_data(csvpath):
    csvfile = open(csvpath, 'rb')
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

# Process fields

def get_alternate_id(rawlocalid, rawprojectid):
    alternate_id = "CSUJAD Local ID: {}, CSUJAD Project ID: {}".format(rawlocalid, rawprojectid)
    return alternate_id

def get_description(rawdescription, rawreferenceurl):
    description = "{0} See this object in the California State Universities Japanese American Digitization project site: <a href=\"{1}\" target=\"_blank\">{1}</a>".format(rawdescription, rawreferenceurl)
    return description

def get_facility(rawfacility):
    facility = ''
    csufacilities = [x.strip() for x in rawfacility.split(CSU_DELIM)]
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
    csutopics = [x.strip() for x in rawtopics.split(CSU_DELIM)]
    for csutopic in csutopics:
        for row in topdata:
            if row['CSU term'] == csutopic:
                topics += 'term:' + row['Densho term'] + '|id:' + row['Densho term ID'] + ';'
                break
    return topics

def get_format(rawtype):
    #TODO need complete list of CSU Types
    ddrformat = ''
    formatmap = [['Text', 'doc'], ['Image','img'], ['Moving Image','av'],['Sound','av']]
    for item in formatmap:
        if item[0] == rawtype:
            ddrformat = item[1]
            break
    return ddrformat

def get_genre(rawgenre):
    genre = rawgenre.split(CSU_DELIM)[0].strip()
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
try:
    credittext = sys.argv[4]
except IndexError:
    credittext = ''


print '{} : Begin run.'.format(datetime.datetime.now())

# Load data
print '{} : Loading data...'.format(datetime.datetime.now())
facdata = load_data(FACDATAPATH)
topdata = load_data(TOPDATAPATH)
csudata = load_data(csucsvpath)
print '{} : Data loaded. CSU data: {} rows; topic data: {} rows; facility data: {} rows.'.format(datetime.datetime.now(), str(len(csudata)), str(len(topdata)), str(len(facdata)))

#print 'csudata first row: {}'.format(csudata[0])
#print 'csudata first row \'Local ID\': {}'.format(csudata[0]['Local ID'])

rownum = 0
processedobject = 0
partobject = 0
for rawentity in csudata:
    rownum += 1
    #check that row contains an object record; not a part of compound object
    if rawentity['Project ID'] != '':
        outfile = os.path.join(outputpath, '{:%Y%m%d-%H%M}-entities.csv'.format(datetime.datetime.now()))
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
        converted['description'] = get_description(rawentity['Description'], rawentity['Reference URL'])
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
    
        converted['status'] = 'completed'
        converted['public'] = '1'
        converted['rights'] = 'cc'
        
        converted['credit'] = credittext
    
        processedobject +=1
        
        converted['id'] = ddrcollectionid + '-' + str(processedobject)
        
        #write converted data    
        odatafile = open(outfile,'a')
        outwriter = csv.writer(odatafile)
        outwriter.writerow(converted.values())
        odatafile.close()
    else:
        partobject +=1
        print '{} : Row #{} did not have \'Project ID\'. Looks like a compound object part.'.format(datetime.datetime.now(), rownum)

print '{} : Run ended.'.format(datetime.datetime.now())
print '{} : {} rows processed. {} new entity rows created. {} partial object rows discarded.'.format(datetime.datetime.now(), rownum, processedobject, partobject)

#end
