# Personalized `medicalTracker`

a `personalized medicalTracker` is more than an AI Agent with discipline in medicine.   

Considering the full life of an individual, the main mission of the `personalized medicalTracker` is to a) Know the Individual Person at a very deep level and b) advocate and consule the individual thru the medical events/conditions till end of life. 

A `personalized medicalTracker` is one and the same with "the individual".  It is the individual - because it has incorporated all knowledge and insight about every aspect of the individual's health.  As the individual changes and adjust to life challanges, so does the personalized medicalTracker. 

- Medical History Data normally resides in the following places:
    - within the heads of doctors seen over a lifetime
    - a 'health folder' accumulating a hog-poog of medical data
    - MyChart health portal - while it has tests, medicines, appointments, doctors - it 

# medicalExpertise

## expert endocrinologist

- An expert endocrinologist's mission is to diagnose, treat, and long-term manage complex hormonal imbalances and metabolic disorders.
- By fine-tuning the body’s chemical messengers (hormones),
- their goal is to restore internal balance,
- improve overall quality of life, and
- prevent future complications linked to conditions like diabetes and thyroid disease.

## expert geriatric doctor

- The mission of an expert geriatric doctor is to optimize the health, independence, and overall quality of life for older adults. 
- They focus on holistic care by managing complex medical conditions, preventing functional decline, and prioritizing treatments
- that honor a patient's personal goals and values.
- Geriatricians are board-certified in family or internal medicine
- with additional fellowship training in the unique physiology and health challenges of aging.
- Their care is typically guided by the 5 M's of Geriatric Care, which ensure a comprehensive approach to an older adult's needs:
-
### 5M's
- Mind: Diagnosing and managing cognitive issues, such as dementia or delirium, as well as mental health concerns like depression.
- Mobility: Evaluating balance, fall risks, and physical limitations to maintain strength and functional independence.
- Medications: Reviewing complex medication lists to prevent adverse drug reactions, simplify dosing, and minimize negative side effects.
- Multi-complexity: Coordinating care for patients who are navigating multiple overlapping health issues (e.g., heart disease, arthritis, and diabetes simultaneously).
- Matters Most: Listening to what a patient values most (like staying in their own home or enjoying time with family) and aligning the care plan with those specific lifestyle and comfort goals

# medicalHistory

## Medical Person History Ingest

- Build a "medicalPersonProfile" : complete set of info that most doctors ask about
- Per Person
    - Injest Medication History
    - Injest Surgery/Procedure History - updated over time

## Medical Test Result History Injestion

- one time import of historical medical data
- contineous import of new medical test result data
- Normalizing all test results from different sources (labs) into best medical industry standard


### Accessing MyChart Data

1. No, MyChart does not provide a native button to directly export all test results into a custom JSON file on a recurring schedule. [1, 2] 
However, under the 21st Century Cures Act, patient portals are legally mandated to allow machine-readable exports. You can accomplish this natively via a bulk XML/JSON export, or automate it on a regular basis using a localized FHIR API script or browser automation tools. [3, 4, 5] 
#### Option 1: The Native Bulk Request (Semi-Automated)
Most Epic MyChart portals allow you to request a full Electronic Health Information (EHI) or Lucy Summary export. This contains your history in standardized, machine-readable XML or Firebased JSON formats. [5, 6, 7] 

   1. Go to your Menu and search for Sharing Hub or Document Center.
   2. Look for Request Copy of Health Record or Download Health Record.
   3. Choose the machine-readable data format option (if available) instead of a human-readable PDF.
   4. Downside: This process usually requires manual clicks and can take a few hours to days for the clinic to generate the bundle file. [5, 6, 7, 8, 9, 10] 

#### Option 2: Fetch via FHIR API (Best for Real JSON)
Because the Austin Regional Clinic MyChart Portal runs on the Epic Systems platform, you can bypass the website UI entirely using the Fast Healthcare Interoperability Resources (FHIR) API. [4, 7] 

* Tools like [Fetch My Epic Token](https://fetch-my-epic-token.org/) guide you through logging into your provider to generate a temporary patient access token.
* You can pair this token with an open-source script (such as getEHR_async on GitHub) to pull raw FHIR JSON components (Observations/Lab Results).
* Downside: Due to security restrictions and strict two-factor authentication (2FA) enforcement, you generally cannot schedule this token refresh completely headless. You will need to manually authenticate each time you execute the pull. [4, 11] 

#### Option 3: Browser Automation Scripting (Scheduled Scraping)
If you want a true regular schedule, you can create a local headless browser script (using Playwright, Puppeteer, or Selenium) that logs into your account, handles the 2FA prompt, navigates the DOM, and extracts the text into a custom JSON structure. [3] 
Platforms like [Anchor Browser Hub](https://anchorbrowser.io/hub/epic-mychart-api-alternative) provide boilerplate logic for automating Epic MyChart data scraping: [3] 

// Example Playwright concept for lab scrapingconst collectMyChartTestResults = async (page) => {
  // Script navigates to: /MyChart/app/test-results
  await page.goto('https://mychart.austinregionalclinic.com/MyChart/app/test-results');
  
  // Logic to iterate through the 177 test classes, expanding rows if necessary
  const results = await page.evaluate(() => {
    // Extract test names, dates, values, and reference ranges from the DOM
    let data = []; 
    // DOM selectors go here...
    return data;
  });
  return results;
};


* Downside: Epic frequently updates its DOM element IDs and security checks. A custom web scraper will require ongoing maintenance whenever the portal layout changes. [2, 11] 


#### Reference: MyChart Access 

- [1] [https://yalehealth.yale.edu](https://yalehealth.yale.edu/sites/default/files/2026-01/how%20to%20download%20records%20from%20mychart%20%28july%202025%29.pdf)
- [2] [https://www.youtube.com](https://www.youtube.com/watch?v=ZPw3bu9bO7w)
- [3] [https://anchorbrowser.io](https://anchorbrowser.io/hub/epic-mychart-api-alternative)
- [4] https://fetch-my-epic-token.org
- [5] [https://www.texashealth.org](https://www.texashealth.org/About-Texas-Health/Request-Medical-Records)
- [6] [https://www.austinregionalclinic.com](https://www.austinregionalclinic.com/patient-guide/mychart-tips/download-visit-and-health-summaries)
- [7] [https://www.youtube.com](https://www.youtube.com/watch?v=RWhktdVwk9M)
- [8] [https://www.hopkinsmedicine.org](https://www.hopkinsmedicine.org/-/media/patient-care/documents/mychart/download-health-records-tip-sheet.pdf)
- [9] [https://www.hopkinsmedicine.org](https://www.hopkinsmedicine.org/-/media/patient-care/documents/mychart/download-health-records-tip-sheet.pdf)
- [10] [https://www.youtube.com](https://www.youtube.com/watch?v=ftW_8b9Bmh4)
- [11] [https://www.youtube.com](https://www.youtube.com/watch?v=2VKGD3FVJ-g)
