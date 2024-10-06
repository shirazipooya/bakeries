import sqlite3
import pandas as pd
from flask import Flask
from flask import render_template, jsonify, request


# Global Variable
DATABASE_NAME = 'database.db'
BAKERISE_TABLE_NAME = 'BAKERIES'
HEADER_NAME = {
    'ID': 'ردیف',
    'FirstName': 'نام',
    'LastName': 'نام خانوادگی',
    'NID': 'کدملی',
    'City': 'شهر',
    'Region': 'منطقه',
    'District': 'ناحیه',
    'Lat': 'عرض جغرافیایی',
    'Lon': 'طول جغرافیایی',
    'HouseholdRisk': 'ریسک خانوار',
    'BakersRisk': 'ریسک نانوا',
    'TypeFlour': 'نوع آرد',
    'TypeBread': 'نوع پخت',
    'BreadRations': 'سهمیه',
}


app = Flask(
    import_name=__name__,
    template_folder="templates",
    static_folder="assets"
)


# SQLite Database Function
def query_db(query, args=(), database=DATABASE_NAME):
    conn = sqlite3.connect(database, timeout=10)
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
    data = query_db(query=query, args=(), database=DATABASE_NAME)
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


@app.route(rule="/sunburst_data/<option>", methods=["GET"])
def sunburst_data(option):
    selected_column = option    
    query = f'SELECT City, Region, District, {selected_column} FROM {BAKERISE_TABLE_NAME}'
    data = pd.DataFrame(query_db(query=query, args=(), database=DATABASE_NAME))
    def build_hierarchy(data, keys):
        if not keys:
            return {'size': len(data)}
        result = []
        for key, group in data.groupby(keys[0]):
            
            if key in list(data[selected_column].unique()):
                result.append({
                    'name': key,
                    'size': len(group[selected_column])
                })
            else:
                result.append({
                    'name': key,
                    'children': build_hierarchy(group, keys[1:]) if len(keys) > 1 else len(group[selected_column])
                })                
        return result

    hierarchy = build_hierarchy(data, ['City', 'Region', 'District', selected_column])

    hierarchical_json = {'name': 'Root', 'children': hierarchy}
    
    return jsonify(hierarchical_json)


@app.route(rule='/region/<region>', methods=['GET'])
def region_info(region):
    print(region)
    query = f'SELECT * FROM {BAKERISE_TABLE_NAME} WHERE Region=?'
    region_data = pd.DataFrame(query_db(query=query, args=(region,), database=DATABASE_NAME))
    print(region_data.groupby(by=['District'])['TypeBread'].value_counts())
    if not region_data.empty:
        return jsonify({
            'n': len(region_data),
            # 'district': region_data.groupby(['District'].count()),
            # 'population': region_data[2],
            # 'area': region_data[3]
        })
    return jsonify({'error': 'Region not found'}), 404
        




@app.route("/")
def index():
    return render_template(template_name_or_list="index.html")


@app.route(rule="/database", methods=['GET'])
def database():

    query = f'SELECT * FROM {BAKERISE_TABLE_NAME}'
    data = query_db(query=query, args=(), database=DATABASE_NAME)
    se = request.args.get('query', '')
    if se != '':
        query = f'SELECT * FROM {BAKERISE_TABLE_NAME} WHERE ? IN (ID, FirstName, LastName, NID, City, Region, District, Lat, Lon, HouseholdRisk, BakersRisk, TypeFlour, TypeBread, BreadRations)'
        data = query_db(query=query, args=(f'%{se}%',), database=DATABASE_NAME)
        
    # query = f'SELECT * FROM {BAKERISE_TABLE_NAME}'
    # data = query_db(query=query, args=(), database=DATABASE_NAME)
    page = request.args.get('page', 1, type=int)
    per_page = 15
    start = (page - 1) * per_page
    end = start + per_page
    total_pages = (len(data) + per_page - 1) // per_page
    items_on_page = data[start:end]
    
    
    return render_template(
        template_name_or_list="database.html",
        data=items_on_page,
        columns=[HEADER_NAME.get(x) for x in list(data[0].keys())],
        total_pages = total_pages,
        page=page
        )
    

# @app.route(rule='/search', methods=['GET'])
# def search():
#     se = request.args.get('query', '')
#     if se == '':
#         query = f'SELECT * FROM {BAKERISE_TABLE_NAME}'
#         data = query_db(query=query, args=(), database=DATABASE_NAME)
#     else:
#         query = f'SELECT * FROM {BAKERISE_TABLE_NAME} WHERE ? IN (ID, FirstName, LastName, NID, City, Region, District, Lat, Lon, HouseholdRisk, BakersRisk, TypeFlour, TypeBread, BreadRations)'
#         data = query_db(query=query, args=(f'%{se}%',), database=DATABASE_NAME)
        
#         page = request.args.get('page', 1, type=int)
#         per_page = 15
#         start = (page - 1) * per_page
#         end = start + per_page
#         total_pages = (len(data) + per_page - 1) // per_page
#         items_on_page = data[start:end]
        
        
#         return render_template(
#             template_name_or_list="database.html",
#             data=items_on_page,
#             columns=[HEADER_NAME.get(x) for x in list(data[0].keys())],
#             total_pages = total_pages,
#             page=page
#             )



# Route to add a new record
@app.route('/add_record', methods=['POST'])
def add_record():
    
    data = request.json
    
    FirstName = data.get('FirstName')
    LastName = data.get('LastName')
    NID = data.get('NID')
    City = data.get('City')
    Region = data.get('Region')
    District = data.get('District')
    Lat = data.get('Lat')
    Lon = data.get('Lon')
    HouseholdRisk = data.get('HouseholdRisk')
    BakersRisk = data.get('BakersRisk')
    TypeFlour = data.get('TypeFlour')
    TypeBread = data.get('TypeBread')
    BreadRations = data.get('BreadRations')
    
    if not FirstName or not LastName or not NID or not City or not Region or not District or not Lat or not Lon or not HouseholdRisk or not BakersRisk or not TypeFlour or not TypeBread or not BreadRations:
        return jsonify({'status': 'error', 'message': 'Missing Fields'}), 400
    
    
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        f'INSERT INTO {BAKERISE_TABLE_NAME} (FirstName, LastName, NID, City, Region, District, Lat, Lon, HouseholdRisk, BakersRisk, TypeFlour, TypeBread, BreadRations) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (FirstName, LastName, NID, City, Region, District, Lat, Lon, HouseholdRisk, BakersRisk, TypeFlour, TypeBread, BreadRations)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'message': 'Record Added Successfully!'})



# Route to delete a record
@app.route('/delete_record/<int:id>', methods=['POST'])
def delete_record(id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        f'DELETE FROM {BAKERISE_TABLE_NAME} WHERE ID=?',
        (id,)
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Record deleted successfully!'})




if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )