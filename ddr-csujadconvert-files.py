import sys, datetime, csv, shutil, os, re, hashlib, mimetypes
import argparse
import collections

DESCRIPTION_SHORT = """Tool to create DDR files import CSV from CSUJAD data."""

DESCRIPTION_LONG = """
Uses CSUJAD CONTENTdm CSV file and directory of binary files to create a CSV 
file for DDR import.

USAGE
$ ddr-csujadconvert-files DDR_COLLECTION_ID DDR_FILE_ROLE CSUJAD_CSV_INPUT_FILE CSUJAD_BINARY_DIRECTORY DDR_CSV_OUTPUT_BASE_PATH
$ ddr-csujadconvert-files ddr-csujad-1 master ./raw/csujaddata.csv ./binaries/preservation ./transformed
---"""

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

#TODO make this work for other edge cases!!
def parse_csufilename(rawfilename):
    #remove file extension
    rawlocalid = rawfilename[:rawfilename.rfind('.')]
    fsort = '1'
    is_ext = '0'
    #check whether file is external
    #DEBUG
    #print 'rawfilename ext={}'.format(rawfilename[rawfilename.rfind('.'):])
    if rawfilename[rawfilename.rfind('.')+1:] in CSU_AVTYPES:
        is_ext = '1'
        #DEBUG
        #print 'filename: {} - is_ext={}'.format(rawfilename,is_ext) 
    #detect 'ike_01_01_003_Part3.pdf'
    if '_Part' in rawlocalid:
        localid = rawlocalid[:rawlocalid.rfind('_')]
        fsort = rawlocalid[rawlocalid.rfind('t') + 1:]
    #detect 'ike_05_23_012b.jpg'
    elif rawlocalid.rstrip()[-1].isalpha():
        localid = rawlocalid[:-1]
        fsort = str(ord(rawlocalid.rstrip()[-1]) - 96)
    #detect 'nis_05_035_174_0001.tif' where localid == 'nis_05_035_174'
    #CSU_LOCALID_PARTS = number of _ separated parts in base localid
    elif len(rawlocalid.split('_')) > CSU_LOCALID_PARTS:
        localid = rawlocalid[:rawlocalid.rfind('_')]
        fsort = int(rawlocalid[rawlocalid.rfind('_')+1:])
    else:
        localid = rawlocalid
    return localid, fsort, is_ext

def do_filehash(path,algo='sha1'):
    if algo == 'sha256':
        h = hashlib.sha256()
    elif algo == 'md5':
        h = hashlib.md5()
    else:
        h = hashlib.sha1()
    block_size=65536
    f = open(path, 'rb')
    while True:
        data = f.read(block_size)
        if not data:
            break
        h.update(data)
    f.close()
    return h.hexdigest()


def get_csufiles(csubinpath):
    csufiles_ = []
    for root, dirs, files in os.walk(csubinpath):
        for file_ in files:
            #remove hidden/system files
            if file_.startswith('.'):
                continue
            #print 'processing file: {}'.format(file_)
            csufile_ = collections.OrderedDict.fromkeys(['csu_localid','csu_filename','csu_filesort','csu_isext','csu_hash'])
            csufile_['csu_filename'] = file_
            csufile_['csu_localid'], csufile_['csu_filesort'], csufile_['csu_isext'] = parse_csufilename(file_)
            #gen the ddr file id hash string if external so IA url works
            if csufile_['csu_isext'] == '1':
                thefile = os.path.join(csubinpath,file_)
                csufile_['csu_sha1'] = do_filehash(thefile,'sha1')
                csufile_['csu_sha256'] = do_filehash(thefile,'sha256')
                csufile_['csu_md5'] = do_filehash(thefile,'md5')
                csufile_['csu_size'] = os.path.getsize(thefile)
                csufile_['csu_mimetype'] = mimetypes.MimeTypes().guess_type(thefile)[0]
            else:
                csufile_['csu_sha1'] = ''
                csufile_['csu_sha256'] = ''
                csufile_['csu_md5'] = ''
                csufile_['csu_size'] = ''
            csufiles_.append(csufile_)
    return csufiles_

def do_id_match(localid,fileid):
    ismatch = False
    altsort = 0
    if localid == fileid:
        ismatch = True
    # find files like 'nis_05_06_0090' where localid == 'nis_05_06_0089-0096'
    elif '-' in localid and '-' not in fileid and localid[:localid.rfind('_')] == fileid[:fileid.rfind('_')]:
        #DEBUG
        #print 'in is_id_match: localid={}; fileid={}'.format(localid,fileid)
        rbegin = int(localid[localid.rfind('_')+1:localid.rfind('-')])                       
        rend = int(localid[localid.rfind('-')+1:])
        #DEBUG
        #print 'rbegin={}; rend={}'.format(str(rbegin),str(rend))
        if rbegin <= int(fileid[fileid.rfind('_')+1:]) <= rend:                                                                                   
            ismatch = True
            altsort = int(fileid[fileid.rfind('_')+1:])
    return ismatch, altsort

# Main
LOGFILE = './logs/{:%Y%m%d-%H%M%S}-csujadconvert-files.log'.format(datetime.datetime.now()) 

# file extensions of av types
CSU_AVTYPES = ['mp3','mp4','m4v','wav','mpg']

DDR_MODELS = ['master','mezzanine','transcript','administrative']

CSU_FIELDS = ['Local ID', 'Project ID', 'Title/Name', 'Creator', 'Date Created', 'Description', 'Location', 'Facility', 'Subjects', 'Type', 'Genre', 'Language', 'Source Description', 'Collection', 'Collection Finding Aid', 'Collection Description', 'Digital Format', 'Project Name', 'Contributing Repository', 'View Item', 'Rights', 'Notes', 'Object File Name', 'OCLC number', 'Date created', 'Date modified', 'Reference URL', 'CONTENTdm number', 'CONTENTdm file name', 'CONTENTdm file path', 'DDR Rights', 'DDR Credit Text']

# number of '_'-separated parts in collection's 'Local ID'; e.g., 'ike_01_01_006'
CSU_LOCALID_PARTS = 3

DDR_FILES_FIELDS = ['id','external','role','basename_orig','mimetype','public','rights','sort','thumb','label','digitize_person','tech_notes','external_urls','links', 'sha1', 'sha256', 'md5','size']

# Get script args
ddridbase = sys.argv[1]
ddrmodel = sys.argv[2]
csucsvpath = sys.argv[3]
csubinpath = sys.argv[4]
try: 
    outputpath = sys.argv[5]
except IndexError:
    outputpath = './'

print '{} : Begin run. CSU_LOCALID_PARTS=={}'.format(datetime.datetime.now(),str(CSU_LOCALID_PARTS))

# Bail on invalid file role arg
if ddrmodel not in DDR_MODELS:
    print '{} : \'{}\' is not a valid DDR file role. Run terminated.'.format(datetime.datetime.now(),ddrmodel)
    exit(1)

# Load data
csudata = load_data(csucsvpath)
print '{} : Raw csv rows to be processed: {}'.format(datetime.datetime.now(), len(csudata))

# Get file names from CSU data
csufiles = get_csufiles(csubinpath)
print '{} : Binary files in input directory: {}'.format(datetime.datetime.now(), len(csufiles))

# Check 'Local ID'
print 'CSU \'Local ID\' appears to have {} parts ({})'.format(str(csudata[0]['Local ID'].count('_')+1),csudata[0]['Local ID'])

#print 'csudata first row: {}'.format(csudata[0])
#print 'csudata first row \'Local ID\': {}'.format(csudata[0]['Local ID'])

#init counters
rownum = 0
processedobject = 0
filescreated = 0
partobject = 0

#process each entity row in csu csv
for csuentity in csudata:
    rownum += 1
    #check that row contains an object record; not just part of compound object
    if csuentity['Project ID'] != '':

        outfile = os.path.join(outputpath, '{}-{}-files-{:%Y%m%d-%H%M}.csv'.format(ddridbase, ddrmodel, datetime.datetime.now()))
        #write header row if first pass
        if not os.path.isfile(outfile):
            odatafile = open(outfile,'w')
            outwriter = csv.writer(odatafile)
            outwriter.writerow(DDR_FILES_FIELDS)
            odatafile.close()
    
        for csufile in csufiles:
            #find matching file in csufiles; then write some data
            id_match, alt_sort = do_id_match(csuentity['Local ID'],csufile['csu_localid'])
            #DEBUG
            #print 'csuentity[\'Local ID\']: {}; csufile[\'csu_localid\']: {}; id_match: {}'.format(csuentity['Local ID'],csufile['csu_localid'],id_match)
            if id_match:
            #set sort val b/c some localids are strange: csufr_jaw_0098-0113
                filesort = csufile['csu_filesort'] if alt_sort == 0 else alt_sort
                #setup row dict
                ddrfilerow = collections.OrderedDict.fromkeys(DDR_FILES_FIELDS)
                #assemble row
                #TODO: less naive DDR ID creation.auto-generate DDR ID
                #ddrfilerow['id'] = get_ddrid(csuentity['Local ID'])
                ddrid = ddridbase + '-{}'.format(processedobject + 1)
                ddrfilerow['id'] = ddrid
                ddrfilerow['external'] = csufile['csu_isext']
                ddrfilerow['role'] = ddrmodel
                ddrfilerow['public'] = '1'
                ddrfilerow['basename_orig'] = csufile['csu_filename']
                ddrfilerow['rights'] = csuentity['DDR Rights']
                ddrfilerow['sort'] = filesort
                #ddrfilerow['label'] = 'Part {}'.format(str(filesort))
                ddrfilerow['label'] = ''
                ddrfilerow['digitize_person'] = ''
                ddrfilerow['tech_notes'] = ''
                if csufile['csu_isext'] == '1':
                    ia_path = ddrid + '/' + ddrid + '-' + ddrmodel + '-'  + csufile['csu_sha1'][:10] + '.' + csufile['csu_filename'][-3:]
                    ddrfilerow['external_urls'] = "label:Internet Archive download|url:https://archive.org/download/{};label:Internet Archive stream|url:https://archive.org/download/{}".format(ia_path,ia_path)
                    ddrfilerow['mimetype'] = csufile['csu_mimetype']
                else:
                    ddrfilerow['external_urls'] = ''
                    ddrfilerow['mimetype'] = csuentity['Digital Format'].split(';')[0].strip()
                ddrfilerow['sha1'] = csufile['csu_sha1']
                ddrfilerow['sha256'] = csufile['csu_sha256']
                ddrfilerow['md5'] = csufile['csu_md5']
                ddrfilerow['size'] = csufile['csu_size']
                ddrfilerow['links'] = ''
                #write row
                odatafile = open(outfile,'a')
                outwriter = csv.writer(odatafile)
                outwriter.writerow(ddrfilerow.values())
                filescreated +=1

        #increment the processed counter and close the output file
        processedobject +=1
        odatafile.close()
    else:
        partobject +=1
        print '{} : Row {} did not have \'Project ID\'. Looks like a compound object part.'.format(datetime.datetime.now(), rownum)

print '{} : Run ended.'.format(datetime.datetime.now())
print '{} : {} rows processed. {} objects found. {} new file rows created. {} partial object rows discarded.'.format(datetime.datetime.now(), rownum, processedobject, filescreated, partobject)

#end
