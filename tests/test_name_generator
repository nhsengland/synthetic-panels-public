from faker import Faker
from faker.config import AVAILABLE_LOCALES
from unidecode import unidecode
from inputs.demographic_distributions import ethnicity_name_mapper, ArabicNameGenerator

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
    "other":  ['en_GB', 'en_IE', 'fr_FR', 'de_DE', 'de_AT', 'de_CH', 'nl_NL', 'nl_BE', 'sv_SE', 'no_NO', 'da_DK', 'fi_FI', 'it_IT', 'es_ES', 'pt_PT', 'el_GR', 'pl_PL', 'ru_RU', 'uk_UA', 'cs_CZ', 'sk_SK', 'hu_HU', 'ro_RO', 'bg_BG', 'hr_HR', 'lt_LT', 'lv_LV', 'tr_TR','zh_CN', 'zh_TW', 'ja_JP', 'ko_KR', 'hi_IN', 'ta_IN', 'bn_BD','bn_BD'],
}

unique_list = list({item for sublist in ethnicity_name_mapper.values() for item in sublist})


# Examples:
print("--- Random Full Names (Latin Alphabet) ---")
for _ in range(5):
    print(generator.generate(include_father=True, gender="female"))

print("\n--- Direct Name Comparison ---")
print(generator.generate(gender="female", show_arabic=True))


def generate_patient_name(self, ethnicity, locale, gender)-> str:
        """
        Given a random ethnicity, generate a name, convert to latin alphabet 
        """
        chosen_locale = locale
        fake = Faker([chosen_locale])

        if gender=='female':
            original_name = fake.name_female()
        else:
            original_name = fake.name_male()
        latin_name = unidecode(original_name)

        if ethnicity=='arab':
            generator = ArabicNameGenerator()
            if gender=='female':
                return generator.generate(include_father=True, gender="female")
            else:
                return generator.generate(include_father=True, gender="male")
        return latin_name


for ethnicity in ethnicity_name_mapper.keys():
     print(ethnicity)
     locales = ethnicity_name_mapper[ethnicity]
     for locale in locales:
         if locale not in AVAILABLE_LOCALES:
             print(f"Locale '{locale}' is not available in Faker. Please check the locale name.")
         if ethnicity == 'arab':
             print(generate_patient_name(None, ethnicity,locale, 'female'), locale)
             print(generate_patient_name(None, ethnicity,locale, 'female'), locale)
             print(generate_patient_name(None, ethnicity,locale, 'female'), locale)
             print(generate_patient_name(None, ethnicity,locale, 'female'), locale)
             print(generate_patient_name(None, ethnicity,locale, 'female'), locale)
