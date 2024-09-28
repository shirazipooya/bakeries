import sqlite3
import pandas as pd
from flask import Flask
from flask import render_template, jsonify


# Global Variable
BAKERISE_TABLE_NAME = 'BAKERIES'


app = Flask(
    import_name=__name__,
    template_folder="templates",
    static_folder="assets"
)


# SQLite Database Function
def query_db(query, args=(), database='database.db'):
    conn = sqlite3.connect(database)
    cur = conn.cursor()
    cur.execute(query, args)
    column_names = [description[0] for description in cur.description]
    rows = cur.fetchall()
    data = [dict(zip(column_names, row)) for row in rows]
    conn.close()
    return data

# Cols: 'HouseholdRisk', 'BakersRisk', 'TypeFlour', 'TypeBread', 'BreadRations'
# API to Get All Data
@app.route(rule='/get_all_data', methods=['GET'])
def get_all_data():
    query = f'SELECT * FROM {BAKERISE_TABLE_NAME}'
    data = query_db(query=query, args=(), database='database.db')
    df = pd.DataFrame(data)
    
    type_bread_cat = df.groupby("TypeBread")["TypeBread"].count().to_dict()
    type_bread_cat = {k: int(v) for k, v in type_bread_cat.items()}
    
    type_flour_cat = df.groupby("TypeFlour")["TypeFlour"].count().to_dict()
    type_flour_cat = {k: int(v) for k, v in type_flour_cat.items()}
    
    bread_rations_cat = df.groupby("BreadRations")["BreadRations"].count().to_dict()
    bread_rations_cat = {k: int(v) for k, v in bread_rations_cat.items()}
    
    bakers_risk_cat = df.groupby("BakersRisk")["BakersRisk"].count().to_dict()
    bakers_risk_cat = {k: int(v) for k, v in bakers_risk_cat.items()}
        
    household_risk_cat = df.groupby("HouseholdRisk")["HouseholdRisk"].count().to_dict()
    household_risk_cat = {k: int(v) for k, v in household_risk_cat.items()}
    
    response = {
        'data': data,
        'number_of_row': len(data),
        'type_bread_cat': type_bread_cat,
        'type_flour_cat': type_flour_cat,
        'bread_rations_cat': bread_rations_cat,                
        'bakers_risk_cat': bakers_risk_cat,
        'household_risk_cat': household_risk_cat,
    }
    
    return jsonify(response)


@app.route("/")
def index():
    return render_template(template_name_or_list="index.html")


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )