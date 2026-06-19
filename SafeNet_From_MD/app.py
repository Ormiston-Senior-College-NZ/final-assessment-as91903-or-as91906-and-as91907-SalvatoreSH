from flask import Flask, render_template, request, redirect
import json, os
app=Flask(__name__)
DB='reports.json'

def load_reports():
    if not os.path.exists(DB): return []
    return json.load(open(DB))

def save_reports(d):
    json.dump(d, open(DB,'w'), indent=2)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/scanner', methods=['GET','POST'])
def scanner():
    result=None
    if request.method=='POST':
        url=request.form['url']
        warnings=[]
        if 'http://' in url: warnings.append('Not HTTPS')
        if 'bit.ly' in url: warnings.append('Shortened URL')
        if '@' in url: warnings.append('Contains @ symbol')
        result=('Safe','No obvious warning signs') if not warnings else ('Warning', ', '.join(warnings))
    return render_template('scanner.html', result=result)

@app.route('/report', methods=['GET','POST'])
def report():
    if request.method=='POST':
        r=load_reports()
        r.append({'title':request.form['title'],'description':request.form['description']})
        save_reports(r)
        return redirect('/reports')
    return render_template('report.html')

@app.route('/reports')
def reports():
    return render_template('reports.html', reports=load_reports())

@app.route('/education')
def education():
    return render_template('education.html')

app.run(debug=True)
