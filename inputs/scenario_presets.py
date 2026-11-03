scenario_presets = {
    "sleepio": {
        "label": "Sleepio (Sleep Therapy)",
        "question": "It is a Saturday morning. You receive the following text message from the NHS. Based on the message you received, how likely would you be to click on the link provided?",
        "scale": "1. Extremely unlikely\n2. Somewhat unlikely\n3. Neither likely nor unlikely\n4. Somewhat likely\n5. Extremely likely",
        "texts": {
            "control": "Dear patient. Sleepio is a free, NHS recommended treatment for poor sleep and insomnia. Start today at www.sleepio.com/nhs. Kind regards Your GP",
            "expectations": "Dear patient. Sleep is important to your health. To improve yours, the NHS now provides six 10-min weekly sessions of sleep therapy: www.sleepio.com/nhs",
            "norms": "Dear patient, people are increasingly prioritising their sleep. 76% of people improved theirs using the NHS-recommended treatment Sleepio: www.sleepio.com/nhs",
            "educational": "Dear patient, to help you sleep better, the NHS recommends using cognitive behavioural therapy. Start six online sessions of Sleepio today: www.sleepio.com/nhs",
            "lifestyle": "Dear patient, good sleep makes you feel refreshed and more connected to the people around you. Sleep better with NHS-recommended Sleepio: www.sleepio.com/nhs",
            "social": "Dear patient, if you or someone you know has trouble sleeping, you can now access an NHS sleep therapy. Sign-up and share the support: www.sleepio.com/nhs",
            "urgency": "Dear patient, prioritise your sleep this month. Start the NHS-recommended therapy Sleepio today: www.sleepio.com/nhs",
        },
    },
   
    "Wayfinder": {
         "label": "Wayfinder 1",
         "question": "It is a Saturday morning. You receive the following text message from the NHS. Based on the message you received, how likely would you be to click on the link provided?",
         "scale": "1. Extremely unlikely\n2. Somewhat unlikely\n3. Neither likely nor unlikely\n4. Somewhat likely\n5. Extremely likely",
         "texts": {
             "neutral": "Dear patient. We have received your referral and you are on the waiting list for an appointment with CHFT. Please visit your patient portal at [link] to let us know if you still need your place on the waiting list.", 
             "state_the_cost": "Dear patient. We have received your referral and you are on the waiting list for an appointment with CHFT. Each missed appointment costs the NHS £177. Please visit your patient portal at [link] to let us know if you still need your place on the waiting list. Thank you.",
             "prosocial" : "Dear patient. We have received your referral and you are on the waiting list for an appointment with CHFT. If you no longer need your appointment, please visit your patient portal at [link] to let us know so we can offer it out to someone else in need. Thank you.",
             },
         "real_results":{
             "neutral": 0.6003,
             "state_the_cost": 0.5711,
             "prosocial": 0.3289,
         }
    },

    "111_dental": {
         "label": "111 dental",
         "question": "You have rung 111 and as you are triaged to an operator you receive the following message. Based on the message you received, how likely are you to visit 111 online instead and end your call early?",
         "scale": "1. Extremely unlikely\n2. Somewhat unlikely\n3. Neither likely nor unlikely\n4. Somewhat likely\n5. Extremely likely",
         "texts": {
             "control": "The fastest way to get help for a dental problem is to use 111 online. Would you like a text with a link to 111 online?",
             "social": "You can reduce the strain on the NHS by using 111 online to get dental help. Can we send you a text with a link to 111 online?",
             "easy": "The fastest way to get dental help is to use 111 online. This usually takes less than 90 seconds. Can we send you a text with a link to 111 online?"},
        "real_results": {
                     "control": 0.23,
                     "social": 0.19,
                     "easy": 0.3,
                },
    },

    "111_emergency_medication": {
         "label": "111 emergency medication",
         "question": "You have rung 111 and as you are triaged to an operator you receive the following message. Based on the message you received, how likely are you to visit 111 online instead and end your call early?",
         "scale": "1. Extremely unlikely\n2. Somewhat unlikely\n3. Neither likely nor unlikely\n4. Somewhat likely\n5. Extremely likely",
         "texts": {
             "control": "The fastest way to get Emergency Medication is by using 111 online. Would you like a link to 111 online?",
             "social": "You can reduce the strain on the NHS by using 111 online to get urgent prescriptions. Can we send you a text with a link to 111 online?",
             "easy": "The fastest way to get urgent prescriptions is by using 111 online. This usually takes less than 90 seconds. Can we send you a text with a link to 111 online?"},
    "real_results": {
                 "control": 0.16,
                 "social": 0.21,
                 "easy": 0.24,
             },
    },

    "111_repeat_prescription": {
         "label": "111 repeat prescription",
         "question": "You have rung 111 and as you are triaged to an operator you receive the following message. Based on the message you received, how likely are you to visit 111 online instead and end your call early?",
         "scale": "1. Extremely unlikely\n2. Somewhat unlikely\n3. Neither likely nor unlikely\n4. Somewhat likely\n5. Extremely likely",
         "texts": {
             "control": "The fastest way to get repeat prescriptions is by using 111 online. Would you like a link to 111 online?",
             "social": "You can reduce the strain on the NHS by using 111 online to get repeat prescriptions. Can we send you a text with a link to 111 online?",
             "easy": "The fastest way to get repeat prescriptions is by using 111 online. This usually takes less than 90 seconds. Can we send you a text with a link to 111 online?"},
         "real_results": {
             "control": 0.17,
             "social": 0.18,
             "easy": 0.29,
         },
    },

    "melanoma": {
        "label": "Melanoma",
        "question": "It is a Saturday morning. You receive the following letter from the NHS. Based on the message you received, how likely would you be to take part in the research described?",
        "scale": "1. Extremely unlikely\n2. Somewhat unlikely\n3. Neither likely nor unlikely\n4. Somewhat likely\n5. Extremely likely",
        "texts": {
            "control": "This is an invitation to participate in a research study called MyMelanoma, which is being led by the University of Oxford.\n The study is open to anyone who has ever been diagnosed with a melanoma of the skin, of the mucosal surfaces (e.g., nose, mouth, genitals), melanoma of the eye, or under the nails. MyMelanoma is an online study, so you will not have to travel to any in-person appointments in order to participate. The study will recruit and maintain contact with a large group of melanoma patients to build the biggest melanoma data resource ever collected in the UK. This resource will help improve the quality of melanoma care in as fast a time as possible, by enabling researchers to answer key unanswered questions about melanoma. For example, how does a melanoma diagnosis and treatment affect mental health and quality of life?", 
            "individualistic_and_norms": "This is an invitation to participate in a research study called MyMelanoma, which is being led by the University of Oxford.\n As someone who has melanoma, you are uniquely placed to help with this study. Your help has the potential to transform the lives of people like you, who live with melanoma.\n The study is open to anyone who has ever been diagnosed with a melanoma of the skin, of the mucosal surfaces (e.g., nose, mouth, genitals), melanoma of the eye, or under the nails. MyMelanoma is an online study, so you will not have to travel to any in-person appointments in order to participate. The study will recruit and maintain contact with a large group of melanoma patients to build the biggest melanoma data resource ever collected in the UK. This resource will help improve the quality of melanoma care in as fast a time as possible, by enabling researchers to answer key unanswered questions about melanoma. For example, how does a melanoma diagnosis and treatment affect mental health and quality of life?",
            "softened_individualistic_and_norms": "This is an invitation to participate in a research study called MyMelanoma, which is being led by the University of Oxford.\n If you are someone with melanoma, you are uniquely placed to help with this study. Your help has the potential to transform the lives of people like you, who live with melanoma.\n The study is open to anyone who has ever been diagnosed with a melanoma of the skin, of the mucosal surfaces (e.g., nose, mouth, genitals), melanoma of the eye, or under the nails. MyMelanoma is an online study, so you will not have to travel to any in-person appointments in order to participate. The study will recruit and maintain contact with a large group of melanoma patients to build the biggest melanoma data resource ever collected in the UK. This resource will help improve the quality of melanoma care in as fast a time as possible, by enabling researchers to answer key unanswered questions about melanoma. For example, how does a melanoma diagnosis and treatment affect mental health and quality of life?"
            },
    },

    "milkman_vaccine_study": {
        "label": "Walmart vaccine intervention",
        "question": "You received a flu vaccine from walmart last year and consented to receive texts from them. Given you receive the following text message, how likely are you to book a flu vaccine?",
        "scale": "1. Extremely unlikely\n2. Somewhat unlikely\n3. Neither likely nor unlikely\n4. Somewhat likely\n5. Extremely likely",
        "texts": {
             "come_back_and_get_your_flu_shot": "Hi  ${NAME}! Congrats on getting your flu shot last year at Walmart. Please come back & get your 2020 flu shot, available now at any Walmart. INFO = info, STOP = opt out.",
             "receive_a_joke_about_the_flu": "Hi  ${NAME}! Congrats on getting your flu shot last year at Walmart. Please come back & get your 2020 flu shot, available now at any Walmart. To help you remember to ask for your flu shot, here's a joke about the flu: Did you hear the joke about the flu? Never mind, we don't want to spread it around. INFO = info, STOP = opt out.",
             "share_a_joke_about_the_flu": "Hi  ${NAME}! Congrats on getting your flu shot last year at Walmart. Please come back & get your 2020 flu shot, available now at any Walmart. To help you remember to ask for your flu shot, here's a joke about the flu: Did you hear the joke about the flu? Never mind, we don't want to spread it around. But what good is a joke you keep to yourself? Share that joke w/ a friend, or even better, the Walmart pharmacist when you go to get your flu shot! INFO = info, STOP = opt out.",
             "people_who_get_flu_shots_are_less_likely_to_get_the_flu": " Hi  ${NAME}! It's flu season. A National Institutes of Health study reveals that Americans who get flu shots are less likely to get the flu. You can get your flu shot at Walmart. Will you get your flu shot and be part of this group? Text Y for Yes or N for No. INFO = info, STOP = opt out.",
             "get_flu_shot_to_avoid_getting_sick": "Hi  ${NAME}! It's flu season and you can get a flu shot at Walmart. Getting a flu shot helps you avoid getting sick. Get a flu shot at Walmart. INFO = info, STOP = opt out.",
             "get_flu_shot_to_avoid_getting_sick_prev_sickness": "Hi  ${NAME}! It's flu season and you can get a flu shot at Walmart. Remember the last time you got sick? It probably interrupted your plans and wasn't much fun. Do you wish you could have avoided getting sick by getting a simple shot? Text Y for yes or N for no. INFO =info, STOP = opt out.",
             "risk_of_catching_flu": " Hi  ${NAME}! It's flu season and you can get a flu shot at Walmart. Please take a minute to think about the risk of catching the flu. Please respond C to let us know you have received this message. Thank you. INFO= info, STOP = opt out",
             "flu_people_healthy_wealthy_educated": "Hi  ${NAME}! It's flu season. A National Institutes of Health study reveals that Americans who get flu shots are healthier, wealthier, and more educated. You can get your flu shot at Walmart. Will you get your flu shot and be part of this group? Text Y for Yes or N for No. INFO = info, STOP = opt out.",
             "risk_of_catching_flu_specific_location": "Hi  ${NAME}! It's flu season & you can get a flu shot at Walmart. Please take a minute to think about the risk of catching the flu. Where do you think you're *most* likely to catch the flu? Please reply 1 for 'At work' 2 for 'At home' 3 for 'At the grocery store' 4 for 'At a bar or restaurant' 5 for 'Any other places you regularly visit' INFO = info, STOP = opt out"
             },
        "real_results": { # looking at beta (increase in uptake) baseline is 23.6%
            "come_back_and_get_your_flu_shot": 0.025,
            "receive_a_joke_about_the_flu": 0.021,
            "share_a_joke_about_the_flu": 0.019,
            "people_who_get_flu_shots_are_less_likely_to_get_the_flu": 0.016,
            "get_flu_shot_to_avoid_getting_sick": 0.015,
            "get_flu_shot_to_avoid_getting_sick_prev_sickness":0.015,
            "risk_of_catching_flu":0.014,
            "flu_people_healthy_wealthy_educated":0.011,
            "risk_of_catching_flu_specific_location": 0.009,
        }
    },

    "milkman_vaccine_study_multiple_messages": {
        "label": "Walmart vaccine intervention",
        "question": "You received a flu vaccine from walmart last year and consented to receive texts from them. Given you receive the following text messages, how likely are you to book a flu vaccine?",
        "scale": "1. Extremely unlikely\n2. Somewhat unlikely\n3. Neither likely nor unlikely\n4. Somewhat likely\n5. Extremely likely",
        "texts": {
            # On the first day you receive:\n  \nThree days later you receive:\n
            "flu_shot_waiting_for_you" : "On the first day you receive:\nWalmartRx - Hi ${NAME}! It's flu season & you can get a flu shot at Walmart. To help you remember, you'll receive another text in a few days. Flu vaccines prevent getting or spreading the flu. INFO = info, STOP = opt out. \nThree days later you receive:\nWalmartRx - Remember a flu shot is waiting for you at Walmart.",
            "Reminder_to_get_a_flu_shot" : "On the first day you receive:\nWalmartRx - Hi ${NAME}! It's flu season & you can get a flu shot at Walmart. To help you remember, you'll receive another text in a few days. INFO = info, STOP = opt out. \nThree days later you receive:\nWalmartRx - This is a reminder to get your flu shot at Walmart.",
            "More_Americans_are_getting_flu_shot_than_in_the_past": "On the first day you receive:\nWalmartRx - Hi ${NAME}! More Americans are getting the flu shot than ever in the last decade. It's flu season & you can get a flu shot at Walmart. To help you remember, you'll receive another text in a few days. INFO = info, STOP = opt out. \nThree days later you receive:\nWalmartRx - This is a reminder to get your flu shot at Walmart. More Americans are getting the flu shot than ever in the last decade.",
            "45_percent_of_Americans_get_the_flu_shot_more_than_in_the_past":  "On the first day you receive:\nWalmartRx - Hi ${NAME}! More Americans are getting the flu shot than ever in the last decade. Last year, 45% of American adults got one. It's flu season & you can get a flu shot at Walmart. To help you remember, you'll receive another text in a few days. INFO = info, STOP = opt out. \nThree days later you receive:\nWalmartRx - This is a reminder to get your flu shot at Walmart. More Americans are getting the flu shot than ever in the last decade. Last year, 45% of American adults got one.",
        },
        "real_results": { # looking at beta (increase in uptake) baseline is 23.6%
            "flu_shot_waiting_for_you" : 0.032,
            "Reminder_to_get_a_flu_shot" : 0.026,
            "More_Americans_are_getting_flu_shot_than_in_the_past": 0.025,
            "45_percent_of_Americans_get_the_flu_shot_more_than_in_the_past": 0.021,
        }

    },
    
    "covid_vaccine_RCT_1": {
        "label": "Covid 19 Booster RCT1",
        "question": "You have previously completed the primary COVID-19 vaccine series. Given this text based reminder, would you click the link and book a booster?",
        "scale": "1. Not at all likely \n2. Quite unlikely \n3. Somewhat unlikely \n4. Neither likely nor unlikely \n5. Somewhat likely \n6. Quite likely \n7. Very likely",
        "texts": {"Ownership w/ Narrow Link": "UCLA Health: ${NAME}, your medical records indicate that you are now eligible for the new bivalent COVID-19 booster. UCLA Health has limited booster appointments available on MyChart.To enhance your protection against COVID-19, claim your dose today by booking an appointment at CVS Pharmacy more availability [specific link to CVS pharmacy website]",
                 "Ownership w/ Broad Link": "UCLA Health: ${NAME}, your medical records indicate that you are now eligible for the new bivalent COVID-19 booster. UCLA Health has limited booster appointments available on MyChart. To enhance your protection against COVID-19, claim your dose today by booking an appointment at a Pharmacy nearby (more availability) [link to www.vaccines.org]",
                  "RCT1 Doctor Recommendation Only": "UCLA Health: ${NAME}, your medical records indicate that you are now eligible for the new bivalent COVID-19 booster. Doctors at UCLA Health strongly recommend that you get this updated booster, as it is designed to extend your protection against COVID-19 by targeting the most contagious, dominant variants of the virus.",
                  "Doctor Recommendation & Ownership w/ Narrow Link": "UCLA Health: ${NAME}, your medical records indicate that you are now eligible for the new bivalent COVID-19 booster. Doctors at UCLA Health strongly recommend that you get this updated booster, as it is designed to extend your protection against COVID-19 by targeting the most contagious, dominant variants of the virus. UCLA Health has limited booster appointments available on MyChart. Claim your dose today by booking an appointment at CVS Pharmacy (more availability) [specific link to CVS pharmacy website]",
                  "Doctor Recommendation & Ownership w/ Broad Link": "UCLA Health: ${NAME}, your medical records indicate that you are now eligible for the new bivalent COVID-19 booster. Doctors at UCLA Health strongly recommend that you get this updated booster, as it is designed to extend your protection against COVID-19 by targeting the most contagious, dominant variants of the virus. UCLA Health has limited booster appointments available on MyChart. Claim your dose today by booking an appointment at CVS Pharmacy (more availability) [link to www.vaccines.org]",
                 },
        "real_results": {
            "Ownership w/ Narrow Link": 0.1432,
            "Ownership w/ Broad Link": 0.1369,
            "RCT1 Doctor Recommendation Only": 0.1371,
            "Doctor Recommendation & Ownership w/ Narrow Link": 0.1429,
            "Doctor Recommendation & Ownership w/ Broad Link": 0.1389,
        },
        },
    
    "covid_vaccine_RCT_2": {
        "label": "Covid 19 Booster RCT2",
        "question": "You have previously completed the primary COVID-19 vaccine series. Given this text based reminder, would you click the link and get a booster?",
        "scale": "1. Not at all likely \n2. Quite unlikely \n3. Somewhat unlikely \n4. Neither likely nor unlikely \n5. Somewhat likely \n6. Quite likely \n7. Very likely",
        "texts": {"Simple-No Info": "UCLA Health: ${NAME}, you can now get the new bivalent COVID-19 booster. UCLA Health has limited booster appointments available on MyChart. Book your appointment at a Pharmacy nearby (more availability) [https://www.vaccines.gov/search/?medicationGuids=018b22d2-054b-4d42-8279-d4efb511aec6%2C25e72c3c-8f6c-4738-9638-08911a400e70&appointments=true&medicationKeys=pfizer_covid_19_vaccine_bivalent_booster%2Cmoderna_covid_19_vaccine_bivalent_booster]",
                "Info-Uniqueness":"UCLA Health: ${NAME}, you can now get the new bivalent COVID-19 booster, which is different from the COVID-19 vaccines you already got. The updated booster can extend your protection by targeting the most contagious, dominant variants of the virus, while strengthening your protection from earlier variants. UCLA Health has limited booster appointments available on MyChart. Book your appointment at a Pharmacy nearby (more availability) [https://www.vaccines.gov/search/?medicationGuids=018b22d2-054b-4d42-8279-d4efb511aec6%2C25e72c3c-8f6c-4738-9638-08911a400e70&appointments=true&medicationKeys=pfizer_covid_19_vaccine_bivalent_booster%2Cmoderna_covid_19_vaccine_bivalent_booster]",
                "Info-Eligibility Clarification" : "UCLA Health: ${NAME} , you can now get the new bivalent COVID-19 booster. Regardless of whether you are at high risk, received the original boosters, or previously got COVID-19, you are eligible based on your  medical records, and this updated booster will strengthen your protection. UCLA Health has limited booster appointments available on MyChart. Book your appointment at a Pharmacy nearby (more availability) [https://www.vaccines.gov/search/?medicationGuids=018b22d2-054b-4d42-8279-d4efb511aec6%2C25e72c3c-8f6c-4738-9638-08911a400e70&appointments=true&medicationKeys=pfizer_covid_19_vaccine_bivalent_booster%2Cmoderna_covid_19_vaccine_bivalent_booster]",
                "Info-Severity": "UCLA Health: ${NAME}, the chances that a healthy adult will develop severe or long-lasting COVID-19 symptoms are higher than many people realize. You can now get the new bivalent COVID-19 booster, which can effectively reduce your chance of developing severe illness and long-lasting COVID-19 symptoms. UCLA Health has limited booster appointments available on MyChart. Book your appointment at a Pharmacy nearby (more availability) [https://www.vaccines.gov/search/?medicationGuids=018b22d2-054b-4d42-8279-d4efb511aec6%2C25e72c3c-8f6c-4738-9638-08911a400e70&appointments=true&medicationKeys=pfizer_covid_19_vaccine_bivalent_booster%2Cmoderna_covid_19_vaccine_bivalent_booster]",
                "Consistency": "UCLA Health: ${NAME}, based on your medical records, you have completed a COVID-19 vaccine primary series. Great job protecting your health. Now, you can get the new bivalent COVID-19 booster. UCLA Health has limited booster appointments available on MyChart. Book your appointment at a Pharmacy nearby (more availability) [https://www.vaccines.gov/search/?medicationGuids=018b22d2-054b-4d42-8279-d4efb511aec6%2C25e72c3c-8f6c-4738-9638-08911a400e70&appointments=true&medicationKeys=pfizer_covid_19_vaccine_bivalent_booster%2Cmoderna_covid_19_vaccine_bivalent_booster]",
                "Consistency & Info-Uniqueness" : "UCLA Health: ${NAME}, based on your medical records, you have completed a COVID-19 vaccine primary series. Great job  protecting your health. Now, you can get the new bivalent COVID-19 booster, which is different from the COVID-19 vaccines you already got. The updated booster can extend your protection by targeting the most contagious, dominant variants of the virus, while strengthening your  protection from earlier variants. UCLA Health has limited booster appointments available on MyChart. Book your appointment at a Pharmacy nearby (more availability) [https://www.vaccines.gov/search/?medicationGuids=018b22d2-054b-4d42-8279-d4efb511aec6%2C25e72c3c-8f6c-4738-9638-08911a400e70&appointments=true&medicationKeys=pfizer_covid_19_vaccine_bivalent_booster%2Cmoderna_covid_19_vaccine_bivalent_booster]"
                    },
        "real_results" : {
            "Info-Uniqueness" : 0.1389,
            "Info-Eligibility Clarification" : 0.1349,
            "Consistency & Info-Uniqueness"	: 0.1339,
            "Simple No-Info":0.1329,
            "Info-Severity":0.1329,
            "Consistency" : 0.1319,
        },
        },
    "covid_vaccine_RCT_3": {
            "label": "Covid 19 Booster RCT3",
            "question": "You have previously completed the primary COVID-19 vaccine series. Given this text based reminder, would you click the link and get a booster?",
            "scale": "1. Not at all likely \n2. Quite unlikely \n3. Somewhat unlikely \n4. Neither likely nor unlikely \n5. Somewhat likely \n6. Quite likely \n7. Very likely",
            "texts": {"Simple–Enhance Protection": "UCLA Health: ${NAME}, this fall, enhance your protection against COVID-19! You can now get the bivalent COVID-19 booster. UCLA Health has limited booster appointments available on MyChart. Book your appointment at CVS Pharmacy (more availability) [https://www.cvs.com/vaccine/intake/store/schedule-options]", 
                      "Bundle–Tagging Flu Shot" : "UCLA Health: ${NAME}, this fall, enhance your protection against COVID-19!You can now get the bivalent COVID-19 booster.UCLA Health has limited booster appointments available on MyChart. Book your appointment at CVS Pharmacy (more availability) [https://www.cvs.com/vaccine/intake/store/schedule-options]; you can also protect yourself against the flu by adding the flu vaccine to your COVID-19 booster appointment.",
                      "Bundle–Booster & Flu Shot" : "UCLA Health: ${NAME}, this fall, enhance your protection against COVID-19 and the flu! You can now save time by bundling two vaccines (the bivalent COVID-19 booster and flu vaccine) at once. UCLA Health has limited booster appointments available on MyChart. At CVS Pharmacy (more availability), you can book one appointment to get both vaccines [https://www.cvs.com/vaccine/intake/store/schedule-options]"

            },
        },
}
    # Add more presets here following the same structure:
    # "preset_key": {
    #     "label": "Display Name",
    #     "question": "...",
    #     "scale": "...",
    #     "texts": {"variant_name": "message content", ...},
    # },
#}}

# milkman ranking: the same order as the texts are listed, arguably the 'risk_of_catching_flu_specific_location' has diff instructions so could remove?