# Veracode list all DAST scans
Lists all DAST scans available to the current user

## Requirements:
- Python 3.12+

## Setup

Clone this repository:

    git clone https://github.com/cadonuno/veracode-list-all-dast-scans

Install dependencies:

    cd veracode-list-all-dast-scans
    pip install -r requirements.txt

(Optional) Save Veracode API credentials in `~/.veracode/credentials`

    [default]
    veracode_api_key_id = <YOUR_API_KEY_ID>
    veracode_api_key_secret = <YOUR_API_KEY_SECRET>


## ISM information
By default, the script will return the endpoint and gateway IDs. However, it supports the inclusion of an endpoints.csv and a gateways.csv files, which will map these values. An example file can be found for each (endpoints_example.csv and gateways_example.csv).

To extrac the IDs, you can follow the instructions included here: https://docs.veracode.com/r/t_dynamic_ISM. The URL depends on your platform instance, but will be one of these:
- https://ui.analysiscenter.veracode.com/mvsa/admin/gateways?depth=1
- https://ui.analysiscenter.veracode.eu/mvsa/admin/gateways?depth=1
- https://ui.analysiscenter.veracode.us/mvsa/admin/gateways?depth=1

## Run
If you have saved credentials as above you can run:

    python list-all-dast-scans.py (arguments)

Otherwise you will need to set environment variables:

    export VERACODE_API_KEY_ID=<YOUR_API_KEY_ID>
    export VERACODE_API_KEY_SECRET=<YOUR_API_KEY_SECRET>
    python list-all-dast-scans.py (arguments)

## Supported Arguments:
- `-o`, `--output_file` - Name of the XLSX file to save (default: 'All_DAST_Scans.xlsx').
- `-s`, `--start_date` - Minimum scheduled start date (YYYY-MM-DDTHH:mm:ssZ).
- `-e`, `--end_date` - Maximum scheduled start date (YYYY-MM-DDTHH:mm:ssZ).