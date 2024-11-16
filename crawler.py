import json
import os
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
import re


def get_country_list() -> list[str]:
    url = "https://whed.net/results_institutions.php"
    response = httpx.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    countries = soup.find("select", {"id": "Chp1"}).find_all("option")
    final_countries = []
    for country in countries:
        country_parent = country.find_parent()
        if country_parent.name == "optgroup":
            if "(all)" not in country.text:
                print(f"Skipping {country.text}")
                continue
        final_countries.append(country)
    return [country["value"] for country in final_countries if country["value"]]

def get_university_domain(whed_code: str):
    u_details_page_url = f"https://www.whed.net/institutions/{whed_code}"
    resp = httpx.get(u_details_page_url)
    u_soup = BeautifulSoup(resp.text, "html.parser")
    u_addr = u_soup.find_all("div", {"class": "dl"})
    for addr in u_addr:
        if "address" in addr.text.lower():
            u_addr = addr
            break
    u_addr = u_addr.find("div", {"class": "dd"})
    try:
        u_website = u_addr.find("a", href=True).text
        print(f"Website: {u_website}")
        u_website = u_website.replace("www.", "")
        base_domain = urlparse(u_website).netloc.split(".")
        print(f"Base Domain: {base_domain}")
        if len(base_domain) > 2:
            base_domain = ".".join(base_domain[-3:])
        else:
            base_domain = ".".join(base_domain)
        print(f"Domain: {base_domain}")
        return base_domain
    except AttributeError:
        print("No website found")
        return ""


def capture_country_university_list(country_name: str):
    current_offset_value = 0
    final_offset_value = 0
    output_list = []
    while True:
        url = "https://whed.net/results_institutions.php"
        form_data = {
            "Chp1": country_name,
            "sort": "IAUMember DESC,Country,InstNameEnglish,iBranchName",
            "nbr_ref_pge": 100,
            "debut": current_offset_value
        }
        response = httpx.post(url, data=form_data)
        soup = BeautifulSoup(response.text, "html.parser")
        form_page = soup.find("form", {"name": "SELECT"})
        if final_offset_value == 0:
            try:
                final_value = form_page.find("a", {"title": "Last page"}).get("onclick")
                match = re.search(r'document\.grille\.debut\.value=(\d+);', final_value)
                if match:
                    final_offset_value = match.group(1)  # Extract the captured group
                    print("Extracted value:", final_offset_value)
            except AttributeError:
                print("No final offset value found")
                final_offset_value = -1

        full_result = form_page.find("ul", {"id": "results"})
        for u in full_result.find_all("span", {"class": "gui"}):
            whed_code = u.text.lstrip().rstrip()
            print(f"WHED Code: {whed_code} (https://www.whed.net/institutions/{whed_code})")
            u_info = u.find_next_sibling("li").find("h3")
            u_name = u_info.find("a").text.lstrip().rstrip()
            print(f"University Name: {u_name}")
            output_list.append({
                "Univeristy": u_name,
                "WHED": whed_code,
                "Domain": get_university_domain(whed_code)
            })
            print(f"{'='*50}")
        print(f"Finished on offset value: {current_offset_value}")
        current_offset_value += 100
        if current_offset_value >= int(final_offset_value):
            print(f"End of the crawl task for {country_name}")
            break
        print(f"Changing Current Offset Value: {current_offset_value}")
    os.makedirs("output", exist_ok=True)
    with open(f"output/{country_name}.json", "w+") as f:
        json.dump(output_list, f, indent=4)
