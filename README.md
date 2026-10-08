# UPI Transaction Tracker MVP — CSV Import Version

## Requirements
- Python 3.10 or newer
- Internet connection for the Chart.js dashboard charts (CDN)

## Run on Windows
1. Extract the ZIP.
2. Open the `UPI_Transaction_Tracker_MVP` folder.
3. Click the File Explorer address bar, type `cmd`, and press Enter.
4. Run `python -m pip install flask`
5. Run `python app.py`
6. Open `http://127.0.0.1:5000` in your browser.

## Import a CSV
- Click **Download CSV Template** and use the exact column names/order shown in the template.
- Required columns: `transaction_id,date,time,merchant,amount,type,category,purpose,status`
- Date format: `YYYY-MM-DD`; type must be `Debit` or `Credit`; amount must be a non-negative number.
- Choose **Upload CSV**. The app validates the entire file before saving it. A successful upload replaces the currently active dataset and refreshes the dashboard.
- **Restore Demo Data** switches back to the included sample transactions. The imported CSV remains in `uploaded_transactions.csv` until replaced or removed.

## Important limitations
- The included 1,340 transactions are synthetic demo data, not real PhonePe transactions.
- This version imports CSV only; it does not parse PDF/Excel files or connect to PhonePe/bank APIs.
- A bank statement may not contain exact product/service purchased or purpose. Those fields must come from transaction narration, invoices/order data, or authorized additional input.
- Do not upload data unless you are authorized to use it. Never enter UPI PIN, OTP, bank password, or card PIN.
- This is a local development MVP, not a production-secure app. It has no login, multi-user isolation, encryption-at-rest, or audit trail. Do not expose it to the public internet.
