import ast
import pandas as pd
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

df = pd.read_csv("Jobs.csv")

@app.route('/')
def home():
    popular_jobs = df.nlargest(3, 'job_score').to_dict(orient='records')
    return render_template('index.html', popular_jobs=popular_jobs)

@app.route('/view/<int:job_id>')
def view_job(job_id):
    job_data = df.loc[df['id'] == job_id].to_dict(orient='records')
    if not job_data:
        return "Job not found", 404
    job = job_data[0]

    if isinstance(job["job_requirements"], str):
        try:
            job["job_requirements"] = ast.literal_eval(job["job_requirements"])
        except (ValueError, SyntaxError):
            job["job_requirements"] = []

    return render_template('view.html', job=job)

@app.route('/search')
def search():
    query = request.args.get('query', '').strip()
    if not query:
        return render_template('search_results.html', query=query, results=[])

    results = df[
        df['title'].str.contains(query, case=False, na=False) |
        df['company'].str.contains(query, case=False, na=False) |
        df['location'].str.contains(query, case=False, na=False)
    ]

    return render_template('search_results.html', query=query, results=results.to_dict(orient='records'))

@app.route('/edit/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):
    global df

    job_data = df[df['id'] == job_id].to_dict(orient='records')
    if not job_data:
        return "Job not found", 404
    job = job_data[0]

    if isinstance(job["job_requirements"], str):
        try:
            job["job_requirements"] = ast.literal_eval(job["job_requirements"])
        except (ValueError, SyntaxError):
            job["job_requirements"] = job["job_requirements"].split("\n")

    if request.method == 'GET':  # Serve the edit page when accessed via GET
        return render_template('edit.html', job=job)

    elif request.method == 'POST':  # Handle AJAX updates
        data = request.get_json()

        required_fields = ["title", "salary", "job_score", "company", "location", "job_requirements", "about_us", "company_video", "company_logo"]
        if any(field not in data or not data[field].strip() for field in required_fields):
            return jsonify({"error": "All fields are required"}), 400

        try:
            job_score = float(data["job_score"])
        except ValueError:
            return jsonify({"error": "Company score must be a valid number."}), 400

        job_requirements_list = [line.strip() for line in data["job_requirements"].split("\n") if line.strip()]

        # Update DataFrame with new values
        df.loc[df['id'] == job_id, required_fields] = [
            data["title"],
            data["salary"],
            job_score,
            data["company"],
            data["location"],
            str(job_requirements_list),
            data["about_us"],
            data["company_video"],
            data["company_logo"]
        ]

        df.to_csv("Jobs.csv", index=False)  # Save changes

        return jsonify({"success": True})  # Send success response

@app.route('/add', methods=['GET', 'POST'])
def add_job():
    global df
    if request.method == 'POST':
        data = request.get_json()

        required_fields = ["title", "salary", "job_score", "company", "location", "job_requirements", "about_us", "company_video", "company_logo"]
        if any(field not in data or not data[field] for field in required_fields):
            return jsonify({"error": "All fields are required"}), 400

        new_id = int(df["id"].max()) + 1 if not df.empty else 1
        new_job = {
            "id": new_id,
            "title": data["title"],
            "salary": data["salary"],
            "job_score": float(data["job_score"]),
            "company": data["company"],
            "location": data["location"],
            "job_requirements": str(data["job_requirements"].split("\n")),
            "about_us": data["about_us"],
            "company_video": data["company_video"],
            "company_logo": data["company_logo"]
        }

        df.loc[len(df)] = new_job
        df.to_csv("Jobs.csv", index=False)

        return jsonify({"success": True, "job_id": new_id})

    return render_template('add.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)

# light grey: e7ecef base: 274c77 accent: 6096ba dark grey: a3cef1