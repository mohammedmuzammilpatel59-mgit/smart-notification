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
