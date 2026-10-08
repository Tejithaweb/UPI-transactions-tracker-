from flask import Flask, render_template, jsonify, request
import csv, io, os
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB CSV limit
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEMO_FILE = os.path.join(BASE_DIR, 'sample_transactions_1340.csv')
UPLOADED_FILE = os.path.join(BASE_DIR, 'uploaded_transactions.csv')
REQUIRED = ['transaction_id', 'date', 'time', 'merchant', 'amount', 'type', 'category', 'purpose', 'status']


def read_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def data():
    # Uploaded data becomes the active dataset after a successful import.
    return read_csv(UPLOADED_FILE if os.path.exists(UPLOADED_FILE) else DEMO_FILE)


@app.get('/')
def home():
    return render_template('index.html')


@app.get('/api/template')
def template():
    content = 'transaction_id,date,time,merchant,amount,type,category,purpose,status\nUPI001,2026-10-01,10:30 AM,Example Store,250,Debit,Shopping,Product Purchase,SUCCESS\n'
    return app.response_class(content, mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=upi_transaction_template.csv'})


@app.post('/api/upload')
def upload():
    f = request.files.get('file')
    if not f or not f.filename:
        return jsonify(error='Please choose a CSV file.'), 400
    if not f.filename.lower().endswith('.csv'):
        return jsonify(error='Only CSV files are supported in this version.'), 400
    try:
        stream = io.TextIOWrapper(f.stream, encoding='utf-8-sig', newline='')
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            return jsonify(error='The CSV file is empty or has no header row.'), 400
        headers = [h.strip().lower() for h in reader.fieldnames]
        missing = [h for h in REQUIRED if h not in headers]
        if missing:
            return jsonify(error='Missing required columns: ' + ', '.join(missing) + '. Download the template and use its column names.'), 400
        # Normalize header case and surrounding whitespace.
        rows, seen_ids = [], set()
        for line_no, raw in enumerate(reader, start=2):
            row = {(k or '').strip().lower(): (v or '').strip() for k, v in raw.items() if k}
            if not any(row.values()):
                continue
            if not row.get('transaction_id'):
                return jsonify(error=f'Row {line_no}: transaction_id is required.'), 400
            tid = row['transaction_id']
            if tid in seen_ids:
                return jsonify(error=f'Row {line_no}: duplicate transaction_id {tid}.'), 400
            seen_ids.add(tid)
            try:
                amount = float(row.get('amount', '').replace(',', '').replace('₹', '').strip())
                if amount < 0:
                    raise ValueError()
            except ValueError:
                return jsonify(error=f'Row {line_no}: amount must be a number greater than or equal to zero.'), 400
            typ = row.get('type', '').title()
            if typ not in ('Debit', 'Credit'):
                return jsonify(error=f'Row {line_no}: type must be Debit or Credit.'), 400
            date_value = row.get('date', '')
            try:
                datetime.strptime(date_value, '%Y-%m-%d')
            except ValueError:
                return jsonify(error=f'Row {line_no}: date must use YYYY-MM-DD format.'), 400
            row['type'] = typ
            row['amount'] = f'{amount:.2f}'
            for col in REQUIRED:
                row.setdefault(col, '')
            rows.append({col: row.get(col, '') for col in REQUIRED})
        if not rows:
            return jsonify(error='No transaction rows found in the CSV.'), 400
        # Save only after every row passes validation, so bad uploads cannot replace active data.
        temp_path = UPLOADED_FILE + '.tmp'
        with open(temp_path, 'w', newline='', encoding='utf-8') as out:
            writer = csv.DictWriter(out, fieldnames=REQUIRED)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temp_path, UPLOADED_FILE)
        return jsonify(message=f'Successfully imported {len(rows)} transactions. Dashboard updated.', count=len(rows))
    except UnicodeDecodeError:
        return jsonify(error='Could not read this CSV encoding. Save it as CSV UTF-8 and try again.'), 400
    except Exception:
        app.logger.exception('CSV import failed')
        return jsonify(error='Import failed. Check the CSV format and try again.'), 500


@app.post('/api/reset-demo')
def reset_demo():
    if os.path.exists(UPLOADED_FILE):
        os.remove(UPLOADED_FILE)
    return jsonify(message='Demo data restored.')


@app.get('/api/summary')
def summary():
    rows = data()
    debit = sum(float(x['amount']) for x in rows if x['type'] == 'Debit')
    credit = sum(float(x['amount']) for x in rows if x['type'] == 'Credit')
    monthly, cats = defaultdict(float), defaultdict(float)
    for x in rows:
        if x['type'] == 'Debit':
            monthly[x['date'][:7]] += float(x['amount'])
            cats[x.get('category') or 'Uncategorized'] += float(x['amount'])
    ratio = round(credit / debit, 4) if debit else None
    return jsonify(count=len(rows), debit=round(debit, 2), credit=round(credit, 2),
                   average=round((debit + credit) / len(rows), 2) if rows else 0,
                   credit_debit_ratio=ratio, monthly=dict(sorted(monthly.items())),
                   categories=dict(sorted(cats.items(), key=lambda z: z[1], reverse=True)),
                   using_uploaded_data=os.path.exists(UPLOADED_FILE))


@app.get('/api/transactions')
def tx():
    q = request.args.get('q', '').lower()
    typ = request.args.get('type', '')
    cat = request.args.get('category', '')
    out = []
    for x in data():
        if q and q not in ' '.join(str(v) for v in x.values()).lower():
            continue
        if typ and x['type'] != typ:
            continue
        if cat and x.get('category') != cat:
            continue
        out.append(x)
    return jsonify(out)


if __name__ == '__main__':
    app.run(debug=False)
