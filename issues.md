# Troubleshooting and Learning Log: Java GKE CI/CD Setup

यह फ़ाइल उन सभी समस्याओं (Issues), उनके मूल कारणों (Root Causes), और समाधानों (Solutions) का एक व्यापक इतिहास है जो हमने इस इंफ्रास्ट्रक्चर और CI/CD पाइपलाइन को बनाने के दौरान हल किए हैं। इसे आप अपनी भविष्य की सीख (Learning) के लिए रख सकते हैं।

---

## 🛠️ GCP Infrastructure & Terraform Issues

### **Issue #1: GCP Billing Account & Project Creation Permission (HTTP 400)**
*   **समस्या (Problem):** Terraform अप्लाई करने पर `failed to check permissions on billing account` एरर आ रहा था।
*   **मूल कारण (Root Cause):** कोड में `resource "google_project"` ब्लॉक नया प्रोजेक्ट बनाने की कोशिश कर रहा था, जिसके लिए ऑर्गनाइजेशन-लेवल बिलिंग एडमिन (Billing Admin) परमिशन की ज़रूरत होती है (जो फ्री-टियर पर सामान्यतः उपलब्ध नहीं होती)।
*   **समाधान (Solution):** हमने `project.tf` फ़ाइल को खाली कर दिया और कोड को सीधे आपके मौजूदा एक्टिव प्रोजेक्ट (`project-616fef18-15b8-4d6c-8a2`) को टारगेट करने के लिए कॉन्फ़िगर किया।

---

### **Issue #2: Duplicate Outputs in Terraform Config**
*   **समस्या (Problem):** `Error: Duplicate output definition` - Terraform इनिशियलाइज़ेशन फ़ेल हो रहा था।
*   **मूल कारण (Root Cause):** आउटपुट वेरिएबल्स (जैसे `gke_cluster_name`, `gke_cluster_location`, और `artifact_registry_url`) को `outputs.tf` फ़ाइल में भी परिभाषित किया गया था और संबंधित `.tf` फ़ाइलों (जैसे `gke.tf`, `artifact_registry.tf`) में भी।
*   **समाधान (Solution):** हमने `gke.tf` और `artifact_registry.tf` से आउटपुट ब्लॉक हटा दिए और सभी आउटपुट को एक ही जगह [`outputs.tf`](file:///C:/Users/AjitP/.gemini/antigravity/scratch/java-gke-cicd/terraform/outputs.tf) में सेंट्रलाइज़ कर दिया।

---

### **Issue #3: TFC GCP Workload Provider ID - Double Prefix (HTTP 400)**
*   **समस्या (Problem):** `oauth2/google: status code 400: {"error":"invalid_request", "error_description":"Invalid value for \"audience\""}`
*   **मूल कारण (Root Cause):** Terraform Cloud में `TFC_GCP_WORKLOAD_PROVIDER_ID` वेरिएबल में हमने पूरा पाथ (`//iam.googleapis.com/projects/...`) सेट कर दिया था। चूँकि TFC खुद यह प्रीफ़िक्स जोड़ता है, इसलिए बैकएंड में डबल प्रीफ़िक्स बन गया।
*   **समाधान (Solution):** हमने TFC में वेरिएबल्स को सुधारा:
    *   `TFC_GCP_WORKLOAD_POOL_ID` में सिर्फ `tfc-pool` (छोटा नाम) रखा।
    *   `TFC_GCP_WORKLOAD_PROVIDER_ID` में सिर्फ `tfc-provider` (छोटा नाम) रखा।

---

### **Issue #4: Missing Service Account & Scope Mismatch**
*   **समस्या (Problem):** `Error creating service account: unable to generate access token...`
*   **मूल कारण (Root Cause):** जिस सर्विस अकाउंट (`tfc-bootstrap-sa`) को Terraform Cloud ऑथेंटिकेट करने के लिए खोज रहा था, वह दूसरे प्रोजेक्ट में बना हुआ था, न कि एक्टिव प्रोजेक्ट (`My First Project`) में।
*   **समाधान (Solution):** हमने `My First Project` में `tfc-bootstrap-sa` नाम का सर्विस अकाउंट कंसोल से मैन्युअली बनाया और उसे प्रोजेक्ट लेवल पर **`Owner`** रोल दिया।

---

### **Issue #5: Allowed Audiences Mismatch (invalid_grant)**
*   **समस्या (Problem):** `oauth2/google: status code 400: {"error":"invalid_grant", "error_description":"The audience in ID Token does not match the expected audience."}`
*   **मूल कारण (Root Cause):** GCP WIF Provider के "Allowed Audiences" में `https://app.terraform.io` डाला गया था, जबकि टोकन एक्सचेंज के दौरान सही प्रोवाइडर पाथ मैच होना ज़रूरी था।
*   **समाधान (Solution):** GCP कंसोल में `tfc-provider` की सेटिंग्स में जाकर **Allowed Audiences** की वैल्यू बदलकर प्रोवाइडर का पूरा रिसोर्स नाम डाल दिया:
    `//iam.googleapis.com/projects/883954050975/locations/global/workloadIdentityPools/tfc-pool/providers/tfc-provider`

---

### **Issue #6: Required GCP APIs Disabled (HTTP 403)**
*   **समस्या (Problem):** `Kubernetes Engine API` / `Artifact Registry API` has not been used or is disabled.
*   **मूल कारण (Root Cause):** नए प्रोजेक्ट में रिसोर्स बनाने से पहले उनकी संबंधित गूगल एपीआई (APIs) इनेबल नहीं थीं।
*   **समाधान (Solution):** हमने GCP कंसोल के सर्च बार से **Kubernetes Engine API** और **Artifact Registry API** दोनों को मैन्युअली इनेबल किया।

---

## 🛠️ GitHub Actions CI/CD Issues

### **Issue #7: GitHub Repository Secrets Missing**
*   **समस्या (Problem):** `Authenticate to Google Cloud (OIDC)` स्टेप पर GitHub एक्शन फ़ेल हुआ।
*   **मूल कारण (Root Cause):** वर्कफ़्लो फ़ाइल में यूज़ होने वाले सीक्रेट्स (`WIF_PROVIDER`, `WIF_SERVICE_ACCOUNT`, `GCP_PROJECT_ID`) GitHub रिपॉजिटरी की सेटिंग्स में नहीं जोड़े गए थे।
*   **समाधान (Solution):** हमने GitHub Repository -> Settings -> Secrets -> Actions में जाकर तीनों वेरिएबल्स को उनके सही मानों के साथ सेव किया।

---

### **Issue #8: OIDC Repository Attribute Condition Rejection (invalid_client)**
*   **समस्या (Problem):** GCP WIF ने `The given credential is rejected by the attribute condition` एरर के साथ ऑथेंटिकेशन रिजेक्ट किया।
*   **मूल कारण (Root Cause):** `wif.tf` में ओइडीसी (OIDC) प्रोवाइडर की कंडीशन लगी थी: `assertion.repository == var.github_repo`। लेकिन कोड में `github_repo` वेरिएबल का डिफ़ॉल्ट मान `"your-username/java-gke-cicd"` रह गया था, जो आपकी असली रिपॉजिटरी से मैच नहीं हुआ।
*   **समाधान (Solution):** हमने [`variables.tf`](file:///C:/Users/AjitP/.gemini/antigravity/scratch/java-gke-cicd/terraform/variables.tf) में `github_repo` का डिफ़ॉल्ट मान बदलकर `"amitpandey1992/java-gke-cicd"` किया और कोड पुश करके Terraform Cloud पर अप्लाई चलाया।

---

### **Issue #9: GKE Kubernetes Pod Image Pull Error (ImagePullBackOff)**
*   **समस्या (Problem):** GKE वर्कलोड स्टेटस पर `Cannot pull image from the registry` (ImagePullBackOff) एरर दिखा रहा था।
*   **मूल कारण (Root Cause):** GKE नोड्स बैकएंड में **Default Compute Engine Service Account** का उपयोग करके इमेज डाउनलोड करते हैं। इसे Artifact Registry से इमेज रीड करने का रोल (`roles/artifactregistry.reader`) नहीं दिया गया था।
*   **समाधान (Solution):** हमने [`wif.tf`](file:///C:/Users/AjitP/.gemini/antigravity/scratch/java-gke-cicd/terraform/wif.tf) में एक नया IAM बाइंडिंग रिसोर्स जोड़ा जो डिफ़ॉल्ट कंप्यूटर सर्विस अकाउंट को `Artifact Registry Reader` रोल प्रदान करता है।

---

## 💡 मुख्य सीख (Key Takeaways)
1. **परियोजना सीमाएँ (Project Boundaries):** WIF और सर्विस अकाउंट्स को हमेशा एक ही GCP प्रोजेक्ट के तहत बनाना चाहिए ताकि प्रोजेक्ट-क्रॉसिंग टोकन एक्सचेंज एरर न हों।
2. **सख्त सुरक्षा (Strict Security):** OIDC का इस्तेमाल करने के लिए नोड्स और प्रोवाइडर्स के बीच सही "Allowed Audiences" और "Attribute Conditions" का होना बेहद ज़रूरी है।
3. **IAM और APIs:** क्लाउड पर डिप्लॉयमेंट से पहले यह पक्का करना ज़रूरी है कि ज़रूरी APIs एक्टिव हों और नोड्स के पास संबंधित रजिस्ट्री को पढ़ने का परमिशन हो।
