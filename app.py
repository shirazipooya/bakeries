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
        

@app.route('/api/pivot_table', methods=['GET'])
def pivot_table_data():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM {BAKERISE_TABLE_NAME}')
    rows = cursor.fetchall()
    conn.close()

    # Convert the rows into a list of dictionaries
    columns = [desc[0] for desc in cursor.description]
    bakeries = [dict(zip(columns, row)) for row in rows]
    return jsonify(bakeries)



@app.route("/")
def index():
    return render_template(template_name_or_list="index.html")


@app.route(rule='/database', methods=['GET'])
def database():
    return render_template(template_name_or_list='database.html')


@app.route(rule='/api/bakeries', methods=['GET'])
def get_table_bakeries():
    search = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'ID')
    sort_order = request.args.get('sort_order', 'asc')
    page = int(request.args.get('page', 1))
    per_page = 15
    offset = (page - 1) * per_page
    
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    query = f"""
        SELECT * FROM {BAKERISE_TABLE_NAME} 
        WHERE
            FirstName LIKE ? OR
            LastName LIKE ? OR
            NID LIKE ? OR
            City LIKE ? OR
            Region LIKE ? OR
            District LIKE ? OR
            Lat LIKE ? OR
            Lon LIKE ? OR
            HouseholdRisk LIKE ? OR
            BakersRisk LIKE ? OR
            TypeFlour LIKE ? OR
            TypeBread LIKE ? OR
            BreadRations LIKE ?
        ORDER BY {sort_by} {sort_order}
        LIMIT ? OFFSET ?
    """
    search_term = f'%{search}%'
    bakeries = conn.execute(query, [search_term] * 13 + [per_page, offset]).fetchall()
    
    query = f"""
        SELECT COUNT(*) FROM {BAKERISE_TABLE_NAME}
        WHERE
            FirstName LIKE ? OR
            LastName LIKE ? OR
            NID LIKE ? OR
            City LIKE ? OR
            Region LIKE ? OR
            District LIKE ? OR
            Lat LIKE ? OR
            Lon LIKE ? OR
            HouseholdRisk LIKE ? OR
            BakersRisk LIKE ? OR
            TypeFlour LIKE ? OR
            TypeBread LIKE ? OR
            BreadRations LIKE ?
    """
    total_count = conn.execute(query, [search_term] * 13).fetchone()[0]
    
    conn.close()

    data = [dict(row) for row in bakeries]

    return jsonify(
        {
            'data': data,
            'total_count': total_count,
            'per_page': per_page,
            'page': page
        }
    )
    
    
    
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


@app.route('/api/bakeries/<int:id>', methods=['DELETE'])
def delete_bakery(id):
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute(f'DELETE FROM {BAKERISE_TABLE_NAME} WHERE ID = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Bakery Deleted Successfully'})


@app.route('/api/bakeries/<int:id>', methods=['POST'])
def update_bakery(id):
    data = request.json
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    query = f'''
        UPDATE {BAKERISE_TABLE_NAME} SET
            FirstName = ?,
            LastName = ?,
            NID = ?,
            City = ?,
            Region = ?,
            District = ?,
            Lat = ?,
            Lon = ?,
            HouseholdRisk = ?,
            BakersRisk = ?,
            TypeFlour = ?,
            TypeBread = ?,
            BreadRations = ?
        WHERE ID = ?
    '''
    conn.execute(
        query, 
        (
            data['FirstName'],
            data['LastName'],
            data['NID'],
            data['City'],
            data['Region'],
            data['District'],
            data['Lat'],
            data['Lon'],
            data['HouseholdRisk'],
            data['BakersRisk'],
            data['TypeFlour'],
            data['TypeBread'],
            data['BreadRations'],
            id
        )
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Bakery Updated Successfully'})



@app.route(rule='/api/cities', methods=['GET'])
def get_cities():
    conn = sqlite3.connect(DATABASE_NAME)
    cur = conn.cursor()
    query = f'SELECT DISTINCT City FROM {BAKERISE_TABLE_NAME}'
    args = ()
    cur.execute(query, args)
    data = cur.fetchall()
    data.sort()
    conn.close()
    return jsonify([city[0] for city in data])


@app.route(rule='/api/regions/<city>', methods=['GET'])
def get_regions(city):
    conn = sqlite3.connect(DATABASE_NAME)
    cur = conn.cursor()
    query = f'SELECT DISTINCT REGION FROM {BAKERISE_TABLE_NAME} WHERE CITY = ?'
    args = (city,)
    cur.execute(query, args)
    data = cur.fetchall()
    data.sort()
    conn.close()
    return jsonify([region[0] for region in data])


@app.route(rule='/api/districts/<region>/<city>', methods=['GET'])
def get_districts(city, region):
    conn = sqlite3.connect(DATABASE_NAME)
    cur = conn.cursor()
    query = f'SELECT DISTINCT DISTRICT FROM {BAKERISE_TABLE_NAME} WHERE CITY = ? AND REGION = ?'
    args = (city, region)
    cur.execute(query, args)
    data = cur.fetchall()
    data.sort()
    conn.close()
    return jsonify([district[0] for district in data])



@app.route(rule='/api/filtered/<city>/<region>/<district>/<typebread>', methods=['GET'])
def get_filtered_data(city, region, district, typebread):
    if typebread == "999":
        if city == "999" and region == "999" and district == "999":
            query = f'SELECT * FROM {BAKERISE_TABLE_NAME}'
            data = query_db(query=query, args=(), database=DATABASE_NAME)
        elif region == "999" and district == "999":
            query = f'SELECT * FROM {BAKERISE_TABLE_NAME} WHERE CITY = ?'
            data = query_db(query=query, args=(city, ), database=DATABASE_NAME)
        elif district == "999":
            query = f'SELECT * FROM {BAKERISE_TABLE_NAME} WHERE CITY = ? AND REGION = ?'
            data = query_db(query=query, args=(city, region), database=DATABASE_NAME)
        else:        
            query = f'SELECT * FROM {BAKERISE_TABLE_NAME} WHERE CITY = ? AND REGION = ? AND DISTRICT = ?'
            data = query_db(query=query, args=(city, region, district), database=DATABASE_NAME)
    else:
        if city == "999" and region == "999" and district == "999":
            query = f'SELECT * FROM {BAKERISE_TABLE_NAME} WHERE TypeBread = ?'
            data = query_db(query=query, args=(typebread,), database=DATABASE_NAME)
        elif region == "999" and district == "999":
            query = f'SELECT * FROM {BAKERISE_TABLE_NAME} WHERE CITY = ? AND TypeBread = ?'
            data = query_db(query=query, args=(city, typebread), database=DATABASE_NAME)
        elif district == "999":
            query = f'SELECT * FROM {BAKERISE_TABLE_NAME} WHERE CITY = ? AND REGION = ? AND TypeBread = ?'
            data = query_db(query=query, args=(city, region, typebread), database=DATABASE_NAME)
        else:        
            query = f'SELECT * FROM {BAKERISE_TABLE_NAME} WHERE CITY = ? AND REGION = ? AND DISTRICT = ? AND TypeBread = ?'
            data = query_db(query=query, args=(city, region, district, typebread), database=DATABASE_NAME)
        
    
    response = {
        'data': data,
    }
    
    return jsonify(response)



@app.route(rule='/api/typeBread', methods=['GET'])
def get_typeBread():
    conn = sqlite3.connect(DATABASE_NAME)
    cur = conn.cursor()
    query = f'SELECT DISTINCT TypeBread FROM {BAKERISE_TABLE_NAME}'
    args = ()
    cur.execute(query, args)
    data = cur.fetchall()
    data.sort()
    conn.close()
    return jsonify([typeBread[0] for typeBread in data])




@app.route(rule='/map-search', methods=['GET'])
def map_search():
    se = request.args.get('query', '')
    if se == '':
        data = query_db(
            query=f'SELECT * FROM {BAKERISE_TABLE_NAME}',
            args=[]
        )
    else:
        data = query_db(
            query=f"""
                SELECT COUNT(*) FROM {BAKERISE_TABLE_NAME}
                WHERE
                    FirstName LIKE ? OR
                    LastName LIKE ? OR
                    NID LIKE ? OR
                    City LIKE ? OR
                    Region LIKE ? OR
                    District LIKE ? OR
                    Lat LIKE ? OR
                    Lon LIKE ? OR
                    HouseholdRisk LIKE ? OR
                    BakersRisk LIKE ? OR
                    TypeFlour LIKE ? OR
                    TypeBread LIKE ? OR
                    BreadRations LIKE ?
            """,
            args=[f'%{se}%'] * 13
        )
        
    response = {
        "data": data,
    }
    
    return jsonify(response)




if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )