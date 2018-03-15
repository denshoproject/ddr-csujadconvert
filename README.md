# ddr-csujadconvert

Python scripts used to convert CSUJAD ContentDM-generated csv object export metadata to DDR-compatible `entity` and `file` csvs for import.

## Requirements

Compatible with Python 2.7 only.

## Usage

The repo contains two scripts: 

```
ddr-csujadconvert-entities DDR_COLLECTION_ID CSUJAD_CSV_INPUT_FILE DDR_CSV_OUTPUT_BASE_PATH
```

`DDR_COLLECTION_ID`: pre-assigned id of the target DDR collection (e.g., `ddr-testing-243`)
`CSUJAD_CSV_INPUT_FILE`: file path of raw csv object file from CSUJAD (e.g., `./csudh_ind_objects`)
`DDR_CSV_OUTPUT_BASE_PATH`: base path for output csv file (e.g., `./converted_data`) 

ddr-csujadconvert-files DDR_COLLECTION_ID DDR_FILE_ROLE CSUJAD_CSV_INPUT_FILE CSUJAD_BINARY_DIRECTORY DDR_CSV_OUTPUT_BASE_PATH
```

`DDR_COLLECTION_ID`: pre-assigned id of the target DDR collection (e.g., `ddr-testing-243`)
`DDR_FILE_ROLE`: DDR role for the files; must be selected from ddr models (e.g., `mezzanine`)
`CSUJAD_CSV_INPUT_FILE`: file path of raw csv object file from CSUJAD (e.g., `./csudh_ind_objects.csv`)
`CSUJAD_BINARY_DIRECTORY`: path to directory containing the CSUJAD binary files (e.g., `./csudh_ind_access`)
`DDR_CSV_OUTPUT_BASE_PATH`: base path for output csv file (e.g., `./converted_data`) 

### Workflow

1. Create DDR-compatible `entities` import csv from raw CSUJAD object csv, `csudh_test_objects.csv`:

```
densho$ python ddr-csujadconvert-entities.py ddr-test-3 /Users/densho/csujad-in/csudh_test_objects.csv /Users/densho/csujad-out/
```

The output will be the new csv file, `/Users/densho/csujad-out/ddr-test-3-entities-20180315-1412.csv`, ready for import into the DDR.

2. Create DDR-compatible `files` import csv:

```
densho$ python ddr-csujadconvert-files.py ddr-test-3 master /Users/densho/csujad-in/csudh_test_objects.csv /Users/densho/csujad-in/csudh_test_preservation /Users/densho/csujad-out/
```

The output will be the new csv file, `/Users/densho/csujad-out/ddr-test-3-files-20180315-1412.csv`, ready for import into the DDR.
