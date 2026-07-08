import os
from flask import Flask, jsonify, request
import requests
from dotenv import load_dotenv
from flask_cors import CORS

# Загрузка ключа из файла .env
load_dotenv()

app = Flask(__name__)
CORS(app)
app.json.ensure_ascii = False

EIA_API_KEY = os.environ.get("EIA_API_KEY")

# Тип топлива - код серии в EIA API
FUEL_SERIES_MAP = {
    "total": "TETCE",      # Всего выбросов CO2
    "coal": "CLTCE",       # Выбросы от угля
    "gas": "NNTCE",        # Выбросы от природного газа
    "petroleum": "PMTCE"   # Выбросы от бензина
}

@app.route('/api/co2-data', methods=['GET'])
def get_co2_data():

    fuel_type = request.args.get('fuel', 'total').lower()

    # Проверяем, есть ли такой тип
    if fuel_type not in FUEL_SERIES_MAP:
        return jsonify({"error": f"Неверный тип под-категории. Допустимые: {list(FUEL_SERIES_MAP.keys())}"}), 400

    # Вытаскиваем нужный код серии (MSN)
    target_series = FUEL_SERIES_MAP[fuel_type]

    query_string = (
        f"api_key={EIA_API_KEY}"
        "&frequency=annual"
        "&data[0]=value"
        f"&facets[seriesId][]={target_series}"
        "&facets[stateId][]=US"
        "&sort[0][column]=period"
        "&sort[0][direction]=asc"
        "&length=100"
    )
    
    url = f"https://api.eia.gov/v2/seds/data/?{query_string}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        raw_data = response.json()
        
        records = raw_data.get("response", {}).get("data", [])
        
        years = []
        emissions = []
        
        for record in records:
            val = record.get("value")
            per = record.get("period")
            
            if val is not None and per is not None:
                try:
                    years.append(int(per))
                    emissions.append(float(val))
                except ValueError:
                    continue
            
        return jsonify({
            "fuel_type": fuel_type,
            "series_code": target_series,
            "years": years,
            "emissions": emissions
        })
        
    except Exception as e:
        return jsonify({"error": f"Ошибка: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)