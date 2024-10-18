import openai 
from sqlalchemy import create_engine, text
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from flask import Flask, request, jsonify
from datetime import datetime, date, time
from flask_cors import CORS


app = Flask(__name__)
CORS(app)


# app = Flask(__name__)
# Configure OpenAI API Key once
openai.api_key = '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'



# Connection parameters
server = 'kritriminsights.database.windows.net'
database = 'Atheanhealth'
username = 'kritrim'
password = 'password*1'
driver = 'ODBC Driver 17 for SQL Server'
connection_string = f'mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver}'
engine = create_engine(connection_string)

# Azure Search details
search_service_name = 'intentsearchindex'
index_name = 'athenahealth'
search_api_key = 'iCVX006auqVmIRz68YmqL3L6f8KinievVyRq4lvHNhAzSeBalXDT'
search_endpoint = f"https://{search_service_name}.search.windows.net"

search_client = SearchClient(
    endpoint=search_endpoint,
    index_name=index_name,
    credential=AzureKeyCredential(search_api_key)
)

# Function to Get Intent from Azure Search Index
def get_intent_from_search(query):
    results = search_client.search(query)
    intents = []
    for result in results:
        if '@search.score' in result and result['@search.score'] > 1:
            intents.append({
                'TableName': result['TableName'],
                'ColumnName': result['ColumnName'],
                'Intent': result['Intent']
            })
    return intents

# Function to Convert Free Text to SQL
def convert_text_to_sql(prompt): 
    response = openai.chat.completions.create(
        model="gpt-4o-mini",  # Use your desired model
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content.strip()

# Function to execute sql query
def execute_sql_query(sql_query):
    with engine.connect() as connection:
        result = connection.execute(text(sql_query))
        rows = result.fetchall()

        print(f"Raw Result: {rows}")  # Log the raw results
        
        results_as_list = []
        for row in rows:
            row_dict = {}
            for column, value in zip(result.keys(), row):
                # Check for datetime types and convert them to string
                if isinstance(value, (datetime, date)):
                    row_dict[column] = value.isoformat()
                elif isinstance(value, time):
                    row_dict[column] = value.strftime('%H:%M:%S')
                else:
                    row_dict[column] = value
            results_as_list.append(row_dict)

        print(f"Formatted Results: {results_as_list}")  # Log the formatted results
        return results_as_list
    
@app.route('/api', methods=['POST'])
def query_api():
    data = request.json
    user_input = data.get('user_input', '')
    prompt=data.get('prompt','')
    if not user_input:
        return jsonify({"error": "user_input is required"}), 400
    intents = get_intent_from_search(user_input)

    prompt = user_input+prompt
    
    sql_query = convert_text_to_sql(prompt)
    if not results_as_list:
        print("No results found for the query.")  # Log if no results found

    return jsonify({"results": results_as_list})


@app.route('/',methods=['GET'])
def test():
    return 'Server is Up!'
if __name__ == '__main__':
    app.run()
