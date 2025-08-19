Smart Notification Agent for email processing.
Task:
Input: Paste raw email text.
Use LLM (GPT-4o, Claude 3.5, or Mistral 8x7b depending on Bolt model access).
Process email and extract:
Summary: 5-line summary.
Category: Academic, HR, Finance, IT, General.
Urgency: Critical, High, Normal.
Action Required: Yes/No.
Format the output as:
makefile
Summary: <summary> Category: <category> Urgency: <urgency> Action: <yes/no> 
Integration (Optional Next Stage):
After processing, store the output to Google Sheets using Bolt's built-in Google Sheets integration.

---

Setup:
1. Create and activate a Python 3.10+ environment.
2. Install dependencies:
   pip install -r requirements.txt
3. Copy .env.example to .env and set keys as needed.

Usage:
- Direct email text:
   python agent.py --email "<paste raw email text>"
- From a file:
   python agent.py --email-file /absolute/path/email.txt
- Choose provider explicitly:
   python agent.py --provider openai --email "<text>"
   python agent.py --provider anthropic --email "<text>"
   python agent.py --provider mistral --email "<text>"
- Pipe input:
   cat email.txt | python agent.py

Output format (single line):
makefile
Summary: <summary> Category: <category> Urgency: <urgency> Action: <yes/no>

Optional: Append to Google Sheets:
   python agent.py --email "<text>" --sheet-id <SPREADSHEET_ID> --sheet-tab "Notifications" --service-account /abs/path/service-account.json

Notes:
- If no provider keys are available, a heuristic fallback is used.
- Ensure GOOGLE_APPLICATION_CREDENTIALS points to a valid service account JSON for Sheets.
