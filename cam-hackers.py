#!/usr/bin/env python3
#-*- coding: utf-8 -*-
#github.com/AngelSecurityTeam/Cam-Hackers
"""
Cam-Hackers: A tool to find public webcams from insecam.org.
Refactored for clarity, robustness, and maintainability.
"""

import requests
import re
import sys
from typing import List, Tuple

import colorama

# --- Constants ---

BASE_URL = "http://www.insecam.org"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux i686; rv:68.0) Gecko/20100101 Firefox/68.0"}

# Data structure: (Country Name, Country Code)
# This is much more robust than two separate lists.
COUNTRIES: List[Tuple[str, str]] = [
    ("United States", "US"), ("Japan", "JP"), ("Italy", "IT"), ("Korea", "KR"),
    ("France", "FR"), ("Germany", "DE"), ("Taiwan", "TW"), ("Russian Federation", "RU"),
    ("United Kingdom", "GB"), ("Netherlands", "NL"), ("Czech Republic", "CZ"),
    ("Turkey", "TR"), ("Austria", "AT"), ("Switzerland", "CH"), ("Spain", "ES"),
    ("Canada", "CA"), ("Sweden", "SE"), ("Israel", "IL"), ("Poland", "PL"),
    ("Iran", "IR"), ("Norway", "NO"), ("Romania", "RO"), ("India", "IN"),
    ("Viet Nam", "VN"), ("Belgium", "BE"), ("Brazil", "BR"), ("Bulgaria", "BG"),
    ("Indonesia", "ID"), ("Denmark", "DK"), ("Argentina", "AR"), ("Mexico", "MX"),
    ("Finland", "FI"), ("China", "CN"), ("Chile", "CL"), ("South Africa", "ZA"),
    ("Slovakia", "SK"), ("Hungary", "HU"), ("Ireland", "IE"), ("Egypt", "EG"),
    ("Thailand", "TH"), ("Ukraine", "UA"), ("Serbia", "RS"), ("Hong Kong", "HK"),
    ("Greece", "GR"), ("Portugal", "PT"), ("Latvia", "LV"), ("Singapore", "SG"),
    ("Iceland", "IS"), ("Malaysia", "MY"), ("Colombia", "CO"), ("Tunisia", "TN"),
    ("Estonia", "EE"), ("Dominican Republic", "DO"), ("Slovenia", "SI"),
    ("Ecuador", "EC"), ("Lithuania", "LT"), ("Palestinian", "PS"),
    ("New Zealand", "NZ"), ("Bangladesh", "BD"), ("Panama", "PA"),
    ("Moldova", "MD"), ("Nicaragua", "NI"), ("Malta", "MT"),
    ("Trinidad And Tobago", "TT"), ("Saudi Arabia", "SA"), ("Croatia", "HR"),
    ("Cyprus", "CY"), ("Pakistan", "PK"), ("United Arab Emirates", "AE"),
    ("Kazakhstan", "KZ"), ("Kuwait", "KW"), ("Venezuela", "VE"), ("Georgia", "GE"),
    ("Montenegro", "ME"), ("El Salvador", "SV"), ("Luxembourg", "LU"),
    ("Curacao", "CW"), ("Puerto Rico", "PR"), ("Costa Rica", "CR"),
    ("Belarus", "BY"), ("Albania", "AL"), ("Liechtenstein", "LI"),
    ("Bosnia And Herzegovina", "BA"), ("Paraguay", "PY"), ("Philippines", "PH"),
    ("Faroe Islands", "FO"), ("Guatemala", "GT"), ("Nepal", "NP"), ("Peru", "PE"),
    ("Uruguay", "UY"), ("Extra", "-"), ("Andorra", "AD"),
    ("Antigua And Barbuda", "AG"), ("Armenia", "AM"), ("Angola", "AO"),
    ("Australia", "AU"), ("Aruba", "AW"), ("Azerbaijan", "AZ"), ("Barbados", "BB"),
    ("Bonaire", "BQ"), ("Bahamas", "BS"), ("Botswana", "BW"), ("Congo", "CG"),
    ("Ivory Coast", "CI"), ("Algeria", "DZ"), ("Fiji", "FJ"), ("Gabon", "GA"),
    ("Guernsey", "GG"), ("Greenland", "GL"), ("Guadeloupe", "GP"), ("Guam", "GU"),
    ("Guyana", "GY"), ("Honduras", "HN"), ("Jersey", "JE"), ("Jamaica", "JM"),
    ("Jordan", "JO"), ("Kenya", "KE"), ("Cambodia", "KH"), ("Saint Kitts", "KN"),
    ("Cayman Islands", "KY"), ("Laos", "LA"), ("Lebanon", "LB"), ("Sri Lanka", "LK"),
    ("Morocco", "MA"), ("Madagascar", "MG"), ("Macedonia", "MK"), ("Mongolia", "MN"),
    ("Macao", "MO"), ("Martinique", "MQ"), ("Mauritius", "MU"), ("Namibia", "NA"),
    ("New Caledonia", "NC"), ("Nigeria", "NG"), ("Qatar", "QA"), ("Reunion", "RE"),
    ("Sudan", "SD"), ("Senegal", "SN"), ("Suriname", "SR"),
    ("Sao Tome And Principe", "ST"), ("Syria", "SY"), ("Tanzania", "TZ"),
    ("Uganda", "UG"), ("Uzbekistan", "UZ"),
    ("Saint Vincent And The Grenadines", "VC"), ("Benin", "BJ")
]


def display_banner_and_menu():
    """Prints the ASCII art banner and the dynamically generated country menu."""
    banner = r"""
    ,     \    /      ,
   / \    )\__/(     / \
  /   \  (_\  /_)   /   \
 /_   \ \()  \ V)  /   _\
 \_   \ \ |  | ) /   _48/
   \    \ (  ) /    /
    \    \ \| /    /
     \    \ |/    /
      \    \ /    /
DRAGONCAMS \ / BY ANONIMAX
"""
    print(f"{colorama.Fore.WHITE}{banner}")

    # Dynamically create the menu in 3 columns
    cols = 3
    countries_per_col = (len(COUNTRIES) + cols - 1) // cols
    for i in range(countries_per_col):
        for j in range(cols):
            index = i + j * countries_per_col
            if index < len(COUNTRIES):
                num = index + 1
                country_name = COUNTRIES[index][0]
                # Pad the country name for alignment
                print(
                    f"{colorama.Fore.RED}{num:3}) "
                    f"{colorama.Fore.WHITE}{country_name:<25}",
                    end=""
                )
        print() # Newline after each row of columns
    print()


def get_country_choice() -> Tuple[str, str]:
    """Prompts the user for a country choice and returns the name and code."""
    while True:
        try:
            choice = int(input(f"{colorama.Fore.WHITE}OPTIONS : "))
            if 1 <= choice <= len(COUNTRIES):
                return COUNTRIES[choice - 1]
            else:
                print(f"{colorama.Fore.RED}Error: Please enter a number between 1 and {len(COUNTRIES)}.")
        except ValueError:
            print(f"{colorama.Fore.RED}Error: Invalid input. Please enter a number.")


def fetch_camera_ips(country_code: str):
    """Fetches and prints all camera IPs for a given country code."""
    print(f"\n{colorama.Fore.YELLOW}[*] Searching for cameras...\n")
    try:
        # First, find the total number of pages
        url = f"{BASE_URL}/en/bycountry/{country_code}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()

        # Safer regex matching
        last_page_match = re.search(r'pagenavigator\("\?page=", (\d+)', res.text)
        if not last_page_match:
            print(f"{colorama.Fore.YELLOW}[!] Could not determine the number of pages. Checking the first page only.")
            last_page = 1
        else:
            last_page = int(last_page_match.group(1))

        print(f"{colorama.Fore.CYAN}[i] Found {last_page} pages of cameras.")

        # Iterate through all pages
        found_count = 0
        for page_num in range(last_page):
            page_url = f"{url}/?page={page_num}"
            print(f"{colorama.Fore.CYAN}[i] Scanning page {page_num + 1}/{last_page}...")
            page_res = requests.get(page_url, headers=HEADERS, timeout=10)
            
            ip_addresses = re.findall(r"http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+", page_res.text)
            
            if not ip_addresses:
                print(f"{colorama.Fore.YELLOW}[!] No IPs found on this page.")
                continue

            for ip in ip_addresses:
                print(f"{colorama.Fore.GREEN}[+] Found: {ip}")
                found_count += 1
        
        print(f"\n{colorama.Fore.YELLOW}[*] Search complete. Found {found_count} total cameras.")

    except requests.exceptions.RequestException as e:
        print(f"{colorama.Fore.RED}[!] Network Error: {e}")
    except Exception as e:
        print(f"{colorama.Fore.RED}[!] An unexpected error occurred: {e}")


def main():
    """Main function to run the script."""
    colorama.init()
    try:
        display_banner_and_menu()
        country_name, country_code = get_country_choice()
        print(f"\n{colorama.Fore.YELLOW}[*] You selected: {country_name} ({country_code})")
        fetch_camera_ips(country_code)
    except KeyboardInterrupt:
        print(f"\n\n{colorama.Fore.RED}[!] User interrupted. Exiting.")
        sys.exit(0)
    finally:
        # Reset terminal color on exit
        print(colorama.Style.RESET_ALL)


if __name__ == "__main__":
    main()
