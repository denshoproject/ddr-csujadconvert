# ddr-csujadconvert

Python scripts used to convert CSUJAD ContentDM-generated csv object export metadata to DDR-compatible `entity` and `file` csvs for import.

## Usage

The repo contains two scripts: 

```
ddr-csujadconvert-entities DDR_COLLECTION_ID CSUJAD_CSV_INPUT_FILE DDR_CSV_OUTPUT_BASE_PATH
```

`DDR_COLLECTION_ID`: pre-assigned id of the target DDR collection (e.g., `ddr-testing-243`)   
`CSUJAD_CSV_INPUT_FILE`: file path of raw csv object file from CSUJAD (e.g., `./csudh_ind_objects`)  
`DDR_CSV_OUTPUT_BASE_PATH`: base path for output csv file (e.g., `./converted_data`)  

```
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

### Notes on `Local ID` and binary filenames

`ddr-csujadconvert-files.py` works by comparing the value of the `Local ID` in each row of the input csv against the list of filenames in the binary directory. In the case of mezzanine files, the filenames of the binaries -- minus the extension -- should *always* match the `Local ID`. However, for master files (called `preservation` by CSUJAD), include extra info in the filename to indicate the ordinality of the file in the case of multi-part aggregated entities (e.g., the individual page images of a scrapbook). Unfortunately, the naming convention for this aggregate info is not consistent across all of the materials so the script is hard-wired to handle only those patterns that we have been able to identify in the current data set. The script can process four types of name patterns:

*    'Part + Digit' - `nis_01_066_Part3.pdf` where `Local ID` == `nis_01_066`
*    'Single Alpha Char' - `ike_05_23_012b.jpg` where `Local ID` == `ike_05_23_012`
*    'Numeric Leading Zero' - `csufr_jaw_01_066_0031` where `Local ID` == `csufr_jaw_01_066`
*    'Numeric Leading Zero Subpart Range' - `nis_01_0069` where `Local ID` == `nis_01_0053-0072`

In addition, the script must know something about the structure of the local IDs, specifically, how many `_` separated parts are in the ID strings. The script has a global `CSU_LOCALID_PARTS` to configure this value.
