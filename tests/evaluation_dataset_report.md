# Honey-Pot — Evaluation Dataset & Results

> **Project:** Honey-Pot — AI-Powered Scam Detection System
> **Model:** Qwen 3.8-27B (Groq)
> **Date:** 2026-09-02
> **Total Messages:** 86 (49 scam, 37 legitimate)
> **Categories:** 18

---

## Part 1: Evaluation Dataset

### 1.1 Scam Messages (49)

#### Phishing (8)

| ID | Message | Expected |
|---|---|---|
| phishing_01 | URGENT: Your SBI account will be suspended within 2 hours. Verify immediately at sbi-verify.co.in or call 9876543210 | Scam |
| phishing_02 | Dear customer, your HDFC Bank account has been locked due to suspicious login from Lagos, Nigeria. Click here to unlock: hdfc-unlock.in | Scam |
| phishing_03 | Your OTP for transaction of Rs 49,999 is 583921. Share this OTP with our executive for verification. Do it NOW. | Scam |
| phishing_04 | Paytm Alert: Your KYC has expired. Complete KYC within 24 hours or your wallet will be deactivated. Send your Aadhaar number to verify. | Scam |
| phishing_05 | ICICI Bank: Unusual transaction of Rs 15,000 detected on your account. If this was NOT you, call our fraud helpline immediately: 9012345678 | Scam |
| phishing_06 | Google Pay: Your account requires re-verification. Send OTP to 8765432100 to continue using UPI services | Scam |
| phishing_07 | WARNING: Someone tried to access your PhonePe wallet from an unknown device in Karachi. Block immediately by sharing your PIN with our security team. | Scam |
| phishing_08 | Your Aadhaar has been linked to 3 unknown bank accounts. This is a security threat. Share your Aadhaar OTP to de-link immediately. | Scam |

#### Prize / Lottery (6)

| ID | Message | Expected |
|---|---|---|
| prize_01 | Congratulations! You have won Rs 50,00,000 in the IPL Mega Jackpot Draw! To claim your prize, pay a processing fee of Rs 999 to UPI: winner@paytm | Scam |
| prize_02 | Lucky Draw Winner! Your mobile number has been randomly selected for a brand new iPhone 15 Pro. Pay delivery charge of Rs 1,500 to claim. | Scam |
| prize_03 | FINAL NOTICE: Your lottery prize of Rs 10,00,000 from Jio Lottery will expire today at midnight. Send your bank details and Aadhaar to claim NOW. | Scam |
| prize_04 | You have been selected for Amazon Great Indian Festival cashback of Rs 25,000. Send your bank account number to receive the money. | Scam |
| prize_05 | Dear lucky winner, you won a Tata Safari car in an online lucky draw! Pay Rs 2,500 insurance fee to Ramesh Kumar at 9871234567@ybl to claim. | Scam |
| prize_06 | HURRY! You are the 1,00,000th visitor! Claim your prize of Rs 75,000 by sharing your UPI ID within the next 30 minutes. | Scam |

#### Banking / UPI Fraud (6)

| ID | Message | Expected |
|---|---|---|
| banking_01 | UPI Payment of Rs 25,000 initiated to scammer@okhdfcbank. If this was NOT you, call 1800-XXX-XXXX immediately to block. | Scam |
| banking_02 | Bank officer here. Your loan application for Rs 10,00,000 has been approved. Send processing fee of Rs 5,000 to proceed with disbursement. | Scam |
| banking_03 | SBI: Rs 1,50,000 has been credited to your account from unknown source. To receive this money, send your account number and IFSC code. | Scam |
| banking_04 | Your bank account has been frozen due to suspicious activity. Pay Rs 2,500 penalty to this UPI to unfreeze: fine@oksbi | Scam |
| banking_05 | A new UPI mandate of Rs 49,999 has been created on your account by Rajesh Kumar. If you did NOT authorize this, cancel immediately by calling 9876543210. | Scam |
| banking_06 | Tax refund of Rs 50,000 pending from Income Tax Department. Pay Rs 500 processing fee via Google Pay to 9876543210 to receive. | Scam |

#### Tech Support Scam (5)

| ID | Message | Expected |
|---|---|---|
| tech_01 | Microsoft Security Alert: Your Windows license has expired. Call +91-9876543210 immediately or your PC will be locked permanently. | Scam |
| tech_02 | URGENT: Your computer has been infected with 5 critical viruses! 12 personal files are at risk. Download our antivirus tool NOW to protect your data. | Scam |
| tech_03 | Apple Support: Your iCloud account has been compromised. Someone in Russia is accessing your photos. Verify your identity by calling our number. | Scam |
| tech_04 | Amazon Prime Alert: Your subscription will auto-renew at Rs 9,999 tomorrow. Cancel by calling 1800-XXX or reply STOP to this message. | Scam |
| tech_05 | WARNING: Someone is accessing your webcam remotely. Your private activities are being recorded. Download SecurityShield Pro immediately to stop this. | Scam |

#### Romance Scam (5)

| ID | Message | Expected |
|---|---|---|
| romance_01 | I love you so much dear but I am stuck in Dubai without money. My family is in danger. Please send Rs 30,000 to my friend's UPI: emergency@paytm | Scam |
| romance_02 | Hi sweetheart, I am a UN peacekeeping doctor in Syria. I found a box with $500,000 but need your help to transfer it. Send Rs 10,000 for clearance fee. | Scam |
| romance_03 | My dear, I want to marry you but first I need money for my passport and visa. Can you send Rs 15,000 to my sister's account? I will repay you. | Scam |
| romance_04 | Baby, my mother is very sick and needs surgery urgently. The hospital is asking Rs 50,000. Can you help me? I will pay you back I promise. | Scam |
| romance_05 | I have been chatting with you for months and I really trust you. But I need Rs 5,000 for a medical emergency right now. Please send to GooglePay. | Scam |

#### Job Scam (5)

| ID | Message | Expected |
|---|---|---|
| job_01 | Congratulations! You are selected for Data Entry job at Rs 35,000/month salary. Send Rs 500 registration fee to confirm your position. | Scam |
| job_02 | Work from home opportunity: Earn Rs 50,000/day! No experience needed. Part-time typing job. Join now by paying Rs 200 for ID card. | Scam |
| job_03 | Government job guaranteed! SSC/UPSC selection guaranteed in 30 days. Our proven method works. Pay Rs 999 now to enroll. | Scam |
| job_04 | Your profile has been shortlisted for Amazon remote job. Salary: Rs 40,000/month. Send resume and Aadhaar photo to proceed. | Scam |
| job_05 | Part-time earning job available. Earn Rs 2,000 daily by doing simple tasks on your phone. Pay Rs 300 security deposit to start today. | Scam |

#### Advance Fee (4)

| ID | Message | Expected |
|---|---|---|
| advance_01 | You have been shortlisted for a personal loan of Rs 10,00,000 from Bajaj Finance. Pay Rs 10,000 processing fee to your assigned officer Mr. Sharma. | Scam |
| advance_02 | International parcel containing Rs 50 lakh from your uncle in London has arrived at Mumbai customs. Pay Rs 15,000 customs duty to release. | Scam |
| advance_03 | CBI investigation requires your cooperation. Your Aadhaar is linked to suspicious transactions. Pay Rs 10,000 investigation fee to prove innocence. | Scam |
| advance_04 | Your passport is ready for collection at Delhi RPO. Pay Rs 3,000 courier charges to 9876543210@paytm for home delivery. | Scam |

#### Authority Impersonation (5)

| ID | Message | Expected |
|---|---|---|
| authority_01 | This is the CBI calling. Your Aadhaar number 1234-5678-9012 has been linked to money laundering worth Rs 2 crore. Share your OTP to verify. | Scam |
| authority_02 | Supreme Court notice: Your SIM will be permanently deactivated within 24 hours due to legal case pending. Verify by calling 9876543210 immediately. | Scam |
| authority_03 | Income Tax Department: Outstanding tax of Rs 75,000 on your PAN card. Pay immediately via UPI or a team will visit your home for arrest. | Scam |
| authority_04 | Police complaint filed against your mobile number for sending abusive messages. Pay Rs 5,000 fine to this account to dismiss the FIR. | Scam |
| authority_05 | TRAI Alert: Your mobile number will be deactivated in 24 hours due to new KYC regulations. Share your Aadhaar OTP to continue service. | Scam |

#### Blackmail (4)

| ID | Message | Expected |
|---|---|---|
| blackmail_01 | We have recorded your private activities from your phone camera. Pay Rs 5,000 to this UPI within 24 hours or we share everything with your contacts. | Scam |
| blackmail_02 | I have hacked your WhatsApp and have all your private chats and photos. Send Rs 10,000 or I will forward them to everyone in your contact list. | Scam |
| blackmail_03 | Your daughter's phone location has been tracked. We know where she is. Pay Rs 50,000 if you want her to be safe. No police. | Scam |
| blackmail_04 | We have proof that you visited certain websites. Pay Rs 3,000 to this number or we will send the browsing history to your family. | Scam |

---

### 1.2 Legitimate Messages (37)

#### OTP Notifications (5)

| ID | Message | Expected |
|---|---|---|
| otp_01 | Your OTP for login is 123456. Do NOT share this with anyone. Valid for 5 minutes. | Legit |
| otp_02 | Axis Bank OTP: 567890 for Rs 2,500 debit. Do not share. If not requested, call 1800-XXX. | Legit |
| otp_03 | Amazon OTP for order delivery: 432100. Share only with delivery person. Never share via phone or email. | Legit |
| otp_04 | Google verification code: 987654. Do not share this code with anyone, including Google employees. | Legit |
| otp_05 | PhonePe: Your OTP is 112233 for UPI registration. Valid for 3 minutes. Never share this OTP. | Legit |

#### Bank Alerts (5)

| ID | Message | Expected |
|---|---|---|
| bankalert_01 | Axis Bank: Rs 2,500 debited from A/c XX4521 for Amazon Pay. Avl Bal: Rs 15,842.00. Not you? Call 1800-XXX. | Legit |
| bankalert_02 | SBI: Rs 50,000 credited to your A/c XX7890. Bal: Rs 2,34,500. Ref: TXN987654. Ignore if not expecting. | Legit |
| bankalert_03 | HDFC Bank Credit Card: Rs 4,999 charged at Amazon.in on 01-Sep. Total due: Rs 12,450. Pay by 15th Sep. | Legit |
| bankalert_04 | Kotak Mahindra Bank: Auto-debit of Rs 18,500 for home loan EMI processed on 01-Sep. A/c XX3456. | Legit |
| bankalert_05 | ICICI Bank: UPI credit of Rs 500 from Priya Sharma (REF: UPI123456). Avl Bal: Rs 8,920. | Legit |

#### Personal Messages (5)

| ID | Message | Expected |
|---|---|---|
| personal_01 | Hey, are you coming to the party tonight? We're meeting at 8 PM at the usual place. | Legit |
| personal_02 | Mom said dinner is ready. Come home soon, she made your favourite paneer butter masala! | Legit |
| personal_03 | Happy Birthday! Wishing you a wonderful year ahead. Let's catch up over coffee this weekend. | Legit |
| personal_04 | Can you pick up milk on your way home? We also need vegetables if you have time. | Legit |
| personal_05 | Your parcel has been delivered. I kept it at the security desk. Please collect when you get home. | Legit |

#### Professional / Work (4)

| ID | Message | Expected |
|---|---|---|
| professional_01 | Meeting reminder: Project review meeting tomorrow at 10 AM in Conference Room B. Please bring your progress report. | Legit |
| professional_02 | Hi, the client presentation has been moved to Thursday. Please update the slide deck accordingly. | Legit |
| professional_03 | Your leave request for Sep 5-7 has been approved by your manager. Please plan your tasks accordingly. | Legit |
| professional_04 | Team lunch tomorrow at 1 PM at Taj Restaurant. Please confirm your attendance by today. | Legit |

#### Service Notifications (4)

| ID | Message | Expected |
|---|---|---|
| service_01 | Your Flipkart order #OD12345 has been shipped. Expected delivery: Sep 4. Track: flipkart.com/track | Legit |
| service_02 | Uber ride completed. Fare: Rs 245 paid via UPI. Rate your driver and share feedback on the app. | Legit |
| service_03 | Zomato: Your order has been confirmed! Estimated delivery: 35 minutes. Track live on the app. | Legit |
| service_04 | Swiggy: Your food is being prepared. Rider will pick up in 10 minutes. Enjoy your meal! | Legit |

#### Promotional (4)

| ID | Message | Expected |
|---|---|---|
| promo_01 | Jio: Your data pack is expiring tomorrow. Recharge with 2GB/day plan at Rs 239. Visit jio.com to recharge. | Legit |
| promo_02 | Big Sale is LIVE on Myntra! Up to 70% off on fashion. Shop now at myntra.com. T&C apply. | Legit |
| promo_03 | Airtel: Special offer! Get 3 months free on annual broadband plan. Call 1800-XXX or visit airtel.in. | Legit |
| promo_04 | Dominos: Order 1 pizza, get 1 free today only! Use code BOGO at checkout. Offer valid till midnight. | Legit |

#### Informational (3)

| ID | Message | Expected |
|---|---|---|
| info_01 | Your electricity bill for August is Rs 1,245. Due date: Sep 30. Pay via any UPI app or visit the BESCOM office. | Legit |
| info_02 | Your PAN card has been linked to your Aadhaar successfully. Reference: PAN-AADHAR-123456. | Legit |
| info_03 | Water supply will be suspended on Sep 5 from 10 AM to 6 PM for maintenance. Please store water accordingly. | Legit |

#### Greetings (3)

| ID | Message | Expected |
|---|---|---|
| greeting_01 | Good morning! Happy Diwali to you and your family. May this festival bring joy and prosperity. | Legit |
| greeting_02 | Eid Mubarak! Wishing you and your loved ones a blessed and peaceful Eid. | Legit |
| greeting_03 | Merry Christmas! Hope you have a wonderful holiday season with your family. | Legit |

#### Edge Cases (5)

| ID | Message | Expected |
|---|---|---|
| edge_01 | Hey, can you send me Rs 200 on GPay? I'm stuck without cash at the petrol pump. Will pay you back tomorrow. | Legit |
| edge_02 | Boss, can I get my salary in advance this month? My daughter's school fees is due. I will adjust next month. | Legit |
| edge_03 | I need to borrow Rs 5000 from you. I will return it next week when my salary comes. Please help. | Legit |
| edge_04 | Hi, I am your son. I lost my phone and using friend's phone. Please send Rs 5000 urgently to this number for an emergency. | Scam |
| edge_05 | Mom, I reached home safely. Don't worry. Will call you in the evening. | Legit |

---

## Part 2: Evaluation Results

> Ran against Groq LLM (Qwen 3.8-27B). 86 API calls, ~3.5 min runtime.

### 2.1 Global Metrics

| Metric | Value |
|---|---|
| Accuracy | **87.21%** |
| Precision | **81.67%** |
| Recall | **100.00%** |
| F1 Score | **89.91%** |
| False Positive Rate | **29.73%** |
| False Negative Rate | **0.00%** |
| Avg Response Time | 2.337s |

### 2.2 Confusion Matrix

```
                    Predicted
                 Scam  | Legit
Actual Scam  :    49   |   0    (TP=49  FN=0)
Actual Legit :    11   |  26    (FP=11  TN=26)
```

### 2.3 Per-Category Breakdown

| Category | Count | Accuracy | Precision | Recall | F1 | FP | FN |
|---|---|---|---|---|---|---|---|
| advance_fee | 4 | 100% | 100% | 100% | 100% | 0 | 0 |
| authority_impersonation | 5 | 100% | 100% | 100% | 100% | 0 | 0 |
| bank_alert | 5 | 60% | 0% | 0% | 0% | 2 | 0 |
| banking_upi | 6 | 100% | 100% | 100% | 100% | 0 | 0 |
| blackmail | 4 | 100% | 100% | 100% | 100% | 0 | 0 |
| edge_case | 5 | 40% | 25% | 100% | 40% | 3 | 0 |
| greeting | 3 | 100% | 0% | 0% | 0% | 0 | 0 |
| informational | 3 | 67% | 0% | 0% | 0% | 1 | 0 |
| job | 5 | 100% | 100% | 100% | 100% | 0 | 0 |
| otp_notification | 5 | 60% | 0% | 0% | 0% | 2 | 0 |
| personal_message | 5 | 80% | 0% | 0% | 0% | 1 | 0 |
| phishing | 8 | 100% | 100% | 100% | 100% | 0 | 0 |
| prize_lottery | 6 | 100% | 100% | 100% | 100% | 0 | 0 |
| professional_work | 4 | 100% | 0% | 0% | 0% | 0 | 0 |
| promotional | 4 | 75% | 0% | 0% | 0% | 1 | 0 |
| romance | 5 | 100% | 100% | 100% | 100% | 0 | 0 |
| service_notification | 4 | 75% | 0% | 0% | 0% | 1 | 0 |
| tech_support | 5 | 100% | 100% | 100% | 100% | 0 | 0 |

### 2.4 False Positives (legitimate messages flagged as scam)

| ID | Category | Message | Why it was flagged |
|---|---|---|---|
| otp_03 | otp_notification | Amazon OTP for order delivery: 432100. Share only with delivery person. Never share via phone or email. | Contains "share" and "OTP" — matches scam patterns |
| otp_05 | otp_notification | PhonePe: Your OTP is 112233 for UPI registration. Valid for 3 minutes. Never share this OTP. | "UPI registration" + "OTP" triggers detection |
| bankalert_02 | bank_alert | SBI: Rs 50,000 credited to your A/c XX7890. Bal: Rs 2,34,500. Ref: TXN987654. Ignore if not expecting. | Large credit amount + "Ignore if not expecting" |
| bankalert_03 | bank_alert | HDFC Bank Credit Card: Rs 4,999 charged at Amazon.in on 01-Sep. Total due: Rs 12,450. Pay by 15th Sep. | "Pay by" + credit card charge pattern |
| personal_05 | personal_message | Your parcel has been delivered. I kept it at the security desk. Please collect when you get home. | "parcel" + "delivered" triggers shipping scam patterns |
| service_01 | service_notification | Your Flipkart order #OD12345 has been shipped. Expected delivery: Sep 4. Track: flipkart.com/track | Order tracking — similar to phishing delivery scams |
| promo_01 | promotional | Jio: Your data pack is expiring tomorrow. Recharge with 2GB/day plan at Rs 239. Visit jio.com to recharge. | "expiring" + "recharge" matches urgency scam pattern |
| info_02 | informational | Your PAN card has been linked to your Aadhaar successfully. Reference: PAN-AADHAR-123456. | PAN/Aadhaar — common in identity scam messages |
| edge_01 | edge_case | Hey, can you send me Rs 200 on GPay? I'm stuck without cash at the petrol pump. Will pay you back tomorrow. | Money request via UPI — matches scam payment pattern |
| edge_02 | edge_case | Boss, can I get my salary in advance this month? My daughter's school fees is due. I will adjust next month. | Financial urgency + "advance" triggers advance fee pattern |
| edge_03 | edge_case | I need to borrow Rs 5000 from you. I will return it next week when my salary comes. Please help. | Borrowing request + money amount triggers scam detection |

### 2.5 False Negatives

None. **All 49 scam messages were correctly detected.**

---

## Part 3: Analysis

### Key Findings

1. **100% Recall** — the system never misses a real scam. This is the most critical metric for a scam detection tool.
2. **Perfect detection across all scam types** — phishing, prize/lottery, banking fraud, tech support, romance, job, advance fee, authority impersonation, and blackmail all scored 100% recall.
3. **False positives are edge cases** — all 11 FPs involve messages that share surface-level patterns with scams (UPI mentions, urgency words, financial requests, OTP references).
4. **The model is aggressively biased toward catching scams** — this is intentional. A false positive is annoying; a false negative costs someone their savings.

### False Positive Patterns

The 11 false positives fall into 3 patterns:

| Pattern | Count | Examples |
|---|---|---|
| OTP/UPI keyword overlap | 4 | OTP sharing, UPI registration, bank credits, PAN/Aadhaar |
| Financial urgency language | 4 | Borrowing requests, advance salary, "expiring" messages |
| Shipping/delivery scams | 3 | Parcel delivery, order tracking, Flipkart shipping |

### Recommendations

1. **Add sender whitelist** — bank alert shortcodes, known services (Amazon, Flipkart, Zomato) should be whitelisted to reduce FPs in OTP/bank/service categories.
2. **Lower confidence threshold for legitimate patterns** — messages from known contacts with casual tone should score lower on scam probability.
3. **Add context awareness** — a message saying "pay by 15th Sep" is different from "pay NOW or your account is blocked."

---

*Generated by `tests/test_comprehensive.py` on 2026-09-02*
