question = """
  It is a Saturday morning. You receive the following text message from the NHS. Based on the message you received, how likely would you be to click on the link provided?
  """

scale = """
  1. Extremely unlikely
  2. Somewhat unlikely
  3. Neither likely nor unlikely
  4. Somewhat likely
  5. Extremely likely
  """

texts = {
  "control": "Dear Patient. Sleepio is a free, NHS recommended treatment for poor sleep and insomnia. Start today at www.sleepio.com/nhs. Kind regards Your GP",
  "expectations": "Dear Patient. Sleep is important to your health. To improve yours, the NHS now provides six 10-min weekly sessions of sleep therapy: www.sleepio.com/nhs",
  "norms": "Dear Patient, people are increasingly prioritising their sleep. 76% of people improved theirs using the NHS-recommended treatment Sleepio: www.sleepio.com/nhs",
  "educational": "Dear Patient, to help you sleep better, the NHS recommends using cognitive behavioural therapy. Start six online sessions of Sleepio today: www.sleepio.com/nhs",
  "lifestyle": "Dear Patient, good sleep makes you feel refreshed and more connected to the people around you. Sleep better with NHS-recommended Sleepio: www.sleepio.com/nhs",
  "social": "Dear Patient, if you or someone you know has trouble sleeping, you can now access an NHS sleep therapy. Sign-up and share the support: www.sleepio.com/nhs",
  "urgency": "Dear Patient, prioritise your sleep this month. Start the NHS-recommended therapy Sleepio today: www.sleepio.com/nhs",
}