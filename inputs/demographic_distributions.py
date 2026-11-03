# This simple function is for generating synthetic demographic distributions when real census data is not supplied.
# For more realistic distributions we recommend you use census data. See `./census_data/`.

def get_demographic_distributions(min_age=18, max_age=100):
    # Set the desired proportion for each age group
    # https://www.census.gov/quickfacts/losangelescountycalifornia
    under_65_proportion = 1-0.225
    over_65_proportion = 0.225

    n_under_65 = max(65 - min_age, 1)
    n_over_65 = max(max_age - 64, 1)

    return {
        "age": {
            **{age: under_65_proportion / n_under_65 for age in range(min_age, 65)},
            **{age: over_65_proportion / n_over_65 for age in range(65, max_age + 1)},
        },

        "gender": {
            "female": 0.511,
            "male": 0.489,
        },

        # US use "social vulnerability index" instead of IMD, so these are based on that. https://www.atsdr.cdc.gov/place-health/php/svi/index.html
        "deprivation_level": {
            "low": 0.222,
            "medium": 0.300,
            "high": 0.477,
        },

        "ethnicity": {
            "white": 0.629,
            "asian": 0.166,
            "black": 0.089,
            "mixed": 0.058,
            "Native Hawaiian": 0.004,
            "native american": 0.052,
        },
    }


ethnicity_name_mapper = {
    "white": ['en_GB', 'en_IE', 'fr_FR', 'de_DE', 'de_AT', 'de_CH', 'nl_NL', 'nl_BE', 'sv_SE', 'no_NO', 'da_DK', 'fi_FI', 'it_IT', 'es_ES', 'pt_PT', 'el_GR', 'pl_PL', 'ru_RU', 'uk_UA', 'cs_CZ', 'sk_SK', 'hu_HU', 'ro_RO', 'bg_BG', 'hr_HR', 'lt_LT', 'lv_LV'],
    "white british": ['en_GB'],
    "white irish": ['en_IE'],
    "white traveller": ['ro_RO'], # romania
    "white roma": ['ro_RO'], #romania
    "asian": ['tr_TR','zh_CN', 'zh_TW', 'ja_JP', 'ko_KR', 'hi_IN', 'ta_IN', 'bn_BD', 'ne_NP', 'id_ID', 'th_TH', 'vi_VN'],
    "asian bangladeshi": ['bn_BD'],
    "asian chinese": ['zh_CN', 'zh_TW'],
    "asian indian": ['en_IN'],
    "asian pakistani": ['en_PK'],
    "black": ['en_NG', 'yo_NG', 'ig_NG', 'en_KE', 'am_ET', 'zu_ZA'],
    "black african": ['en_NG', 'yo_NG', 'ig_NG', 'en_KE', 'am_ET', 'zu_ZA'],
    "black caribbean": ['en_NG', 'yo_NG', 'ig_NG', 'en_KE', 'am_ET', 'zu_ZA'], # no caribbean locales in faker, so using african locales as a proxy
    "mixed": ['es_MX', 'pt_BR', 'es_CO', 'en_US', 'en_CA', 'en_AU', 'en_NZ'],
    "arab": ['ar_SA'],
    "mixed white and black african": ['es_MX', 'pt_BR', 'es_CO', 'en_US', 'en_CA', 'en_AU', 'en_NZ', 'en_GB', 'en_IE', 'fr_FR', 'de_DE', 'de_AT', 'de_CH', 'nl_NL', 'nl_BE', 'sv_SE', 'no_NO', 'da_DK', 'fi_FI', 'it_IT', 'es_ES', 'pt_PT', 'el_GR', 'pl_PL', 'ru_RU', 'uk_UA', 'cs_CZ', 'sk_SK', 'hu_HU', 'ro_RO', 'bg_BG'],
    "mixed white and asian": ['tr_TR','zh_CN', 'zh_TW', 'ja_JP', 'ko_KR', 'hi_IN', 'ta_IN', 'bn_BD', 'ne_NP', 'id_ID', 'th_TH', 'vi_VN',],
    "mixed white and black caribbean": ['en_GB', 'en_IE', 'fr_FR', 'de_DE', 'de_AT', 'de_CH', 'nl_NL', 'nl_BE', 'sv_SE', 'no_NO', 'da_DK', 'fi_FI', 'it_IT', 'es_ES', 'pt_PT', 'el_GR', 'pl_PL', 'ru_RU', 'uk_UA', 'cs_CZ', 'sk_SK', 'hu_HU', 'ro_RO', 'bg_BG', 'hr_HR', 'lt_LT', 'lv_LV', 'en_NG', 'yo_NG', 'ig_NG', 'en_KE', 'am_ET', 'zu_ZA'],
    "native american": ['en_US'],
    "Native Hawaiian": ['en_US'],
    "other":  ['en_GB', 'en_IE', 'fr_FR', 'de_DE', 'de_AT', 'de_CH', 'nl_NL', 'nl_BE', 'sv_SE', 'no_NO', 'da_DK', 'fi_FI', 'it_IT', 'es_ES', 'pt_PT', 'el_GR', 'pl_PL', 'ru_RU', 'uk_UA', 'cs_CZ', 'sk_SK', 'hu_HU', 'ro_RO', 'bg_BG', 'hr_HR', 'lt_LT', 'lv_LV', 'tr_TR','zh_CN', 'zh_TW', 'ja_JP', 'ko_KR', 'hi_IN', 'ta_IN', 'bn_BD','bn_BD'],
}


class ArabicNameGenerator:
    def __init__(self):
        # Male First Names: (Arabic, Standard Transliteration)
        self.male_names = [
            ("Tariq", "طارق"), ("Zayd", "زيد"), ("Sami", "سامي"),
            ("Kareem", "كريم"), ("Youssef", "يوسف"), ("Hamza", "حمزة"),
            ("Omar", "عمر"), ("Faris", "فارس"), ("Bilal", "بلال")
        ]
        
        # Female First Names
        self.female_names = [
            ("Ghaida", "غيداء"), ("Buthaina", "بثينة"), ("Amira", "أميرة"),
            ("Yara", "يارا"), ("Lina", "لينا"), ("Maryam", "مريم"),
            ("Noor", "نور"), ("Fatima", "فاطمة"), ("Zahra", "زهراء")
        ]
        
        # Family Names / Tribal Names
        self.family_names = [
            ("Al-Qaseer", "القصير"), ("Al-Ghamdi", "الغامدي"),
            ("Al-Mansoor", "المنصور"), ("Al-Otaibi", "العتيبي"),
            ("Al-Sayed", "السيد"), ("Al-Hassan", "الحسن"),
            ("Al-Dabbagh", "الدباغ"), ("Al-Shehri", "الشهري")
        ]

    def generate(self, gender="random", include_father=True, show_arabic=False):
        # Determine gender
        if gender == "random":
            gender = random.choice(["male", "female"])
            
        # Select Given Name
        names_list = self.male_names if gender == "male" else self.female_names
        first_en, first_ar = random.choice(names_list)
        
        # Select Family Name
        fam_en, fam_ar = random.choice(self.family_names)
        
        if include_father:
            # Father's name is picked from male list
            father_en, father_ar = random.choice(self.male_names)
            
            connector_en = "bin" if gender == "male" else "bint"
            connector_ar = "بن" if gender == "male" else "بنت"
            
            latin_name = f"{first_en} {connector_en} {father_en} {fam_en}"
            arabic_name = f"{first_ar} {connector_ar} {father_ar} {fam_ar}"
        else:
            latin_name = f"{first_en} {fam_en}"
            arabic_name = f"{first_ar} {fam_ar}"
            
        if show_arabic:
            return f"{latin_name} ({arabic_name})"
        return latin_name