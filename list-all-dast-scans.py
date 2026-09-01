import argparse
import csv
import os
import pandas as pd
from veracode_api_py import Analyses, BusinessUnits, Occurrences, Scans
from veracode_api_py.apihelper import APIHelper

ANALYSIS_CACHE = dict()
URLS_ISMS_CACHE = dict()
ENDPOINT_CACHE = dict()
SCAN_TYPES= {
    "WEB_SCAN": "Web Application",
    "API_SCAN": "API",
}

gateway_id_to_gateway_name = dict()
endpoint_id_to_endpoint_name = dict()

def get_actual_start_date(occurrence):
    return occurrence["actual_start_date"] if "actual_start_date" in occurrence else "NONE"

def get_scheduled_start_date(occurrence):
    return occurrence["start_date"] if "start_date" in occurrence else "NONE"

def get_create_date(base_analysis):
    return base_analysis["created_on"] if "created_on" in base_analysis else "NONE"

def get_actual_end_date(occurrence):
    return occurrence["actual_end_date"] if "actual_end_date" in occurrence else "NONE"

def get_scheduled_end_date(occurrence):
    return occurrence["end_date"] if "end_date" in occurrence else "NONE"

def get_status(occurrence):
    if "status" in occurrence and "status_type" in occurrence["status"]:
        return occurrence["status"]["status_type"]
    return 'No status found'

def parse_ism_info(ism_info):
    global gateway_id_to_gateway_name
    global endpoint_id_to_endpoint_name
    
    gateway_id = ism_info["gateway_id"]
    endpoint_id = ism_info["endpoint_id"]
    if endpoint_id in ENDPOINT_CACHE:
        return ENDPOINT_CACHE.get(endpoint_id)

    gateways = APIHelper()._rest_request('dae/api/tcs-api/api/v1/ism_gateways','GET')

    for gateway in gateways:
        if gateway["refId"] == gateway_id:
            for endpoint in gateway["endpoints"]:
                if endpoint["token"] == endpoint_id:
                    endpoint_info = f"ISM Gateway: {gateway['name']}, Endpoint: {endpoint['name']}"
                    ENDPOINT_CACHE.update({endpoint_id: endpoint_info})
                    return endpoint_info
            break

    endpoint_info = f"ISM Gateway: {gateway_id_to_gateway_name.get(gateway_id, f' ID {gateway_id}')}, Endpoint: {endpoint_id_to_endpoint_name.get(endpoint_id, f' ID {endpoint_id}')}"
    ENDPOINT_CACHE.update({endpoint_id: endpoint_info})

    return endpoint_info

def get_analysis_for_id(analysis_id):
    if analysis_id in ANALYSIS_CACHE:
        return ANALYSIS_CACHE.get(analysis_id)
    analyses = Analyses().get(analysis_id)
    ANALYSIS_CACHE.update({analysis_id: analyses})
    return analyses

def parse_endpoints_and_gateways_map():
    global gateway_id_to_gateway_name
    global endpoint_id_to_endpoint_name

    gateway_csv = 'gateways.csv'
    endpoint_csv = 'endpoints.csv'

    try:
        if os.path.exists(gateway_csv):
            with open(gateway_csv, 'r') as gateways_file:
                reader = csv.DictReader(gateways_file)
                for row in reader:
                    gateway_id_to_gateway_name[row["gateway_id"]] = row["gateway_name"]
        else:
            print(f"Warning: {gateway_csv} not found. Gateway names will not be available.")

        if os.path.exists(endpoint_csv):
            with open(endpoint_csv, 'r') as endpoints_file:
                reader = csv.DictReader(endpoints_file)
                for row in reader:
                    endpoint_id_to_endpoint_name[row["endpoint_id"]] = row["endpoint_name"]
        else:
            print(f"Warning: {endpoint_csv} not found. Endpoint names will not be available.")
    except Exception as e:
        print(f"Error reading CSV files: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Lists all DAST scans available to the current user."
    )

    parser.add_argument(
        "-o",
        "--output_file",
        help="Name of the CSV file to save (default: 'All_DAST_Scans.csv').",
        required=False
    )

    parser.add_argument(
        "-s",
        "--start_date",
        help="Minimum scheduled start date (YYYY-MM-DDTHH:mm:ssZ).",
        required=False
    )

    parser.add_argument(
        "-e",
        "--end_date",
        help="Maximum scheduled start date (YYYY-MM-DDTHH:mm:ssZ).",
        required=False
    )

    args =  parser.parse_args()
    output_file = args.output_file

    if not output_file:
        output_file = "All_DAST_Scans.xlsx"

    parse_endpoints_and_gateways_map()

    print("Fetching list of DAST scans")
    if args.start_date or args.end_date:
        scan_filters = {}
        if args.start_date:
            scan_filters["start_date_after"] = args.start_date
        if args.end_date:
            scan_filters["start_date_before"] = args.end_date
        all_occurrences = APIHelper()._rest_paged_request('was/configservice/v1/analysis_occurrences','GET','analysis_occurrences', scan_filters)
    else:
        all_occurrences = Occurrences().get_all()

    business_unit_map = dict()
    for bu in BusinessUnits().get_all():
        business_unit_map.update({str(bu["bu_legacy_id"]): bu["bu_name"]})

    all_dast_scans = []
    raw_data = []
    for occurrence in all_occurrences:
        base_analysis = get_analysis_for_id(occurrence["analysis_id"])
        
        is_api_scan = base_analysis["scan_type"] == "API_SCAN"
        bu_id = base_analysis["org_info"]["business_unit_id"] if ("org_info" in base_analysis and "business_unit_id" in base_analysis["org_info"]) else None
        business_unit = business_unit_map[bu_id] if str(bu_id) in business_unit_map else "N/A"

        urls_for_ocurrence = Occurrences().get_scan_occurrences(occurrence["analysis_occurrence_id"])
        all_dast_scans.append({ "Analysis Name": base_analysis["name"], "Scan Type": SCAN_TYPES.get(base_analysis["scan_type"], "NONE"), "Number of Items": len(urls_for_ocurrence), "Status": get_status(occurrence), "Frequency": base_analysis.get("schedule_frequency", "NONE"), "StartDate": get_scheduled_start_date(occurrence), "Business Unit": business_unit })
        
        for url_scan_ocurrence in urls_for_ocurrence:
            very_high_flaws = url_scan_ocurrence.get("count_of_very_high_sev_flaws", 0)
            high_flaws = url_scan_ocurrence.get("count_of_high_sev_flaws", 0)
            medium_flaws = url_scan_ocurrence.get("count_of_medium_sev_flaws", 0)
            low_flaws = url_scan_ocurrence.get("count_of_low_sev_flaws", 0)
            total_flaws = very_high_flaws + high_flaws + medium_flaws + low_flaws
            raw_data.append({
                                "Analysis Name": base_analysis["name"], 
                                "URL/Api SPEC": url_scan_ocurrence["api_scan_setting"]["spec_name"] if is_api_scan else url_scan_ocurrence["target_url"], 
                                "Application Name": url_scan_ocurrence.get("linked_platform_app_name", "N/A"), 
                                "Status": url_scan_ocurrence.get("analysis_occurrence_status", "N/A"), 
                                "Very High": very_high_flaws, 
                                "High": high_flaws, 
                                "Medium": medium_flaws, 
                                "Low": low_flaws, 
                                "Total Count": total_flaws, 
                                "Start Date": url_scan_ocurrence.get("start_date", "N/A"), 
                                "Duration": url_scan_ocurrence.get("duration", "N/A"), 
                                "Internal Scanning": parse_ism_info(url_scan_ocurrence["internal_scan_configuration"]) if url_scan_ocurrence["internal_scan_configuration"]["enabled"] else "N/A"
                            })

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df = pd.DataFrame(all_dast_scans)
        df.to_excel(writer, sheet_name='All Analysis Completed', index=False)
        df_raw = pd.DataFrame(raw_data)
        df_raw.to_excel(writer, sheet_name='Raw Data', index=False)
if __name__ == '__main__':
    main()