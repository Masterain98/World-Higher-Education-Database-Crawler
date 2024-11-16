from crawler import capture_country_university_list, get_country_list

if __name__ == "__main__":
    countries = get_country_list()
    for country in countries:
        capture_country_university_list(country)
