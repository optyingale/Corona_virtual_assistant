import requests 
import numpy as np
from bs4 import BeautifulSoup 
import pandas as pd
import re
import json
import speech_recognition as sr
import pyttsx3
import warnings

warnings.filterwarnings("ignore")

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    return text


def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        said = ''
        
        try:
            said = r.recognize_google(audio)
        except Exception as e:
            print(str(e))
    return said.lower()

speak('Scraping table')
print('Scraping table')
def scrape_table(url):
    # Creating soup for each source
    soup = BeautifulSoup(requests.get(url).content, 'lxml')

    # Getting rows for each table from soup
    table_rows = soup.find_all('tr')
    
    # Getting column names given as the 'th' tag; strip=True means that the tags are removed from the string
    column_names = []
    for cell in table_rows[0].find_all('th'):
        column_names.append(cell.get_text(strip=True))

    # Getting cell data in list to later create a DataFrame
    each_row = []
    for row in table_rows[1:]:
        each_row.append([cell.get_text(strip=True) for cell in row.find_all('td')])

    # Creating DataFrame from extracted data
    df = pd.DataFrame(each_row, columns=column_names)
    
    return df

speak('cleaning the data')
print('cleaning the data')
def clean_data(df):
    
    # Checking for which dataframe is recieved 
    if 'Name of State / UT' in df:
        df = india_df.iloc[:33, :]
        df.drop('S. No.', axis=1, inplace=True)
        df.set_index('Name of State / UT', inplace=True)
        for col in df.columns:
            df[col] = df[col].str.extract('(\d+)').astype(int)
        df.sort_values(df.columns[0], ascending=False, inplace=True)
        
        # Creating recovery_rate to understand more about the closed cases
        df['recovery_rate (in percentage)'] = ((df[df.columns[1]]/(df[df.columns[1]]+df[df.columns[2]]))*100).round(2)
        
        # No idea why this isnt working
#        df.rename(columns={df.columns[1]:'Total Cases',
#                        df.columns[3]:'Deaths', 
#                        df.columns[2]:'Total Recovered'}, 
#                  inplace=True)
#        response = requests.get("https://api.covid19india.org/state_test_data.json")
#        data = json.loads(response.text)
#        data1 = data.get('states_tested_data')
#        df['ICU Beds'] = 0
#        df['Isolation Beds'] = 0
#        df['Total Tests'] = 0
#        df['Test positive rate'] = 0
#        for x in data1:
#            if x.get('state') in df[df.columns[0]].values:
#                if x.get('testpositivityrate') != '':
#                    df.loc[temp_df[df.columns[0]]==x.get('state'), 'Test positive rate'] = float(x.get('testpositivityrate')[:-1])
#                if x.get('totaltested') != '':
#                    df.loc[temp_df[df.columns[0]]==x.get('state'), 'Total Tests'] = float(x.get('totaltested'))
#                if x.get('numicubeds') != '':
#                    df.loc[temp_df[df.columns[0]]==x.get('state'), 'ICU Beds'] = int(x.get('numicubeds'))
#                if x.get('numisolationbeds') != '':
#                    df.loc[temp_df[df.columns[0]]==x.get('state'), 'Isolation Beds'] = int(x.get('numisolationbeds'))
    
    elif 'TotalDeaths' in df:
        # The reason for not hard coding here below is that
        # The website might add on later new countires whose data might not be available now
        upper_index = world_df[world_df['Country,Other']=='World'].index[0]
        lower_index = world_df[world_df['Country,Other']=='Total:'].index[0]
        
        # 15 May, website updated their table and added a number column
        world_df.drop('#', axis=1, inplace=True)
        
        # Dropping columns after active cases, this can be changed depending on need for analysis later on
        df = world_df.iloc[upper_index:lower_index, :-7]
        df['Total Tests'] = world_df.loc[:, 'TotalTests'].iloc[upper_index:lower_index]
        df.set_index('Country,Other', inplace=True)
        
        # Converting alphanumeric data to pure numeric and later to integer type
        # this works for all values
        for col in df.columns:
            df[col] = [''.join(re.findall(r'\d+', df[col].values[i])) for i in range(len(df[col]))]
            df[col] = df[col].replace('', 0)
            df[col] = df[col].apply(int)
            
        df.sort_values('TotalCases', ascending=False, inplace=True)
        df['recovery_rate (in percentage)'] = ((df[df.columns[4]]/(df[df.columns[4]]+df[df.columns[2]]))*100).round(2)
        df['Positive Rate'] = ((df['TotalCases']/df['Total Tests'])*100).round(2)
        df['Positive Rate'].replace(np.inf, 0, inplace=True)
    
    return df

india_url = 'https://www.mohfw.gov.in/'
india_df = scrape_table(india_url)
world_url = 'https://www.worldometers.info/coronavirus/'
world_df = scrape_table(world_url)

india_df_clean = clean_data(india_df)
world_df_clean = clean_data(world_df)


###################################################################################################################

temp_df = india_df_clean.reset_index()
temp_df1 =world_df_clean.reset_index()

#Adding Positive Rate 
#temp_df1['Positive Rate'] = ((temp_df1['TotalCases']/temp_df1['Total Tests'])*100).round(2)
#temp_df1.replace(np.inf, 0, inplace=True)


temp_df.rename(columns={temp_df.columns[1]:'Total Cases',
                        temp_df.columns[3]:'Deaths', 
                        temp_df.columns[2]:'Total Recovered'}, 
               inplace=True)
response = requests.get("https://api.covid19india.org/state_test_data.json")
data = json.loads(response.text)
data1 = data.get('states_tested_data')
temp_df['ICU Beds'] = 0
temp_df['Isolation Beds'] = 0
temp_df['Total Tests'] = 0
temp_df['Test positive rate'] = 0
for x in data1:
    if x.get('state') in temp_df[temp_df.columns[0]].values:
        if x.get('testpositivityrate') != '':
            temp_df.loc[temp_df[temp_df.columns[0]]==x.get('state'), 'Test positive rate'] = float(x.get('testpositivityrate')[:-1])
        if x.get('totaltested') != '':
            temp_df.loc[temp_df[temp_df.columns[0]]==x.get('state'), 'Total Tests'] = float(x.get('totaltested'))
        if x.get('numicubeds') != '':
            temp_df.loc[temp_df[temp_df.columns[0]]==x.get('state'), 'ICU Beds'] = int(x.get('numicubeds'))
        if x.get('numisolationbeds') != '':
            temp_df.loc[temp_df[temp_df.columns[0]]==x.get('state'), 'Isolation Beds'] = int(x.get('numisolationbeds'))


def query_df(text):
    query_country_or_state = []
    text = text.replace('and', '')
    text = text.replace('in ', '')
    text = text.replace('tamilnadu', 'tamil nadu')
    df = temp_df
    for state in df[df.columns[0]].values:
        for t in text.split():
            if t == state.lower():
                query_country_or_state.append(state)
    if any(query_country_or_state) == False :
        df = temp_df1
        for country in df[df.columns[0]].values:
            for t in text.split():
                if t == country.lower():
                    query_country_or_state.append(country)
    return df.set_index(df.columns[0]).loc[query_country_or_state].reset_index().drop_duplicates()

def query_col(text):
    india_column_patterns = {re.compile("[\w\s]+ cases [\w\s]+") : temp_df.columns[1],
                             re.compile("[\w\s]+ recovered [\w\s]+") : temp_df.columns[2],
                             re.compile("[\w\s]+ death|deaths [\w\s]+") : temp_df.columns[3],
                             re.compile("[\w\s]+ recovery rate [\w\s]+") : temp_df.columns[4],
                             re.compile("[\w\s]+ test|tests|testing [\w\s]+") : temp_df.columns[7],
                             re.compile("[\w\s]+ positive rate [\w\s]+") : temp_df.columns[8],}
    world_column_patterns = {re.compile("[\w\s]+ cases [\w\s]+") : temp_df1.columns[1],
                             re.compile("[\w\s]+ recovered [\w\s]+") : temp_df1.columns[5],
                             re.compile("[\w\s]+ death|deaths [\w\s]+") : temp_df1.columns[3],
                             re.compile("[\w\s]+ recovery rate [\w\s]+") : temp_df1.columns[8],
                             re.compile("[\w\s]+ test|tests|testing [\w\s]+") : temp_df1.columns[7],
                             re.compile("[\w\s]+ positive rate [\w\s]+") : temp_df1.columns[9],}
    india_state = temp_df[temp_df.columns[0]].str.lower().values
    col = []
    p = india_column_patterns
    for t in text.split():
        if t in india_state:
            p = india_column_patterns
            print(t)
            pass
        else:
            p = world_column_patterns
    for pattern , column in p.items():
        if pattern.match(text):
            col.append(column)
    return col

speak('ask me any stat about coronavirus for either country or state')
speak('to terminate this app you must say stop')
print('You may now speak')

end_phrase = 'stop'

while True:
    print('Listning')
    text = get_audio()
    print(text)
    if text:
        try:
            if text.find(end_phrase) != -1:  # stop loop
                print("Exit")
                speak('The pleasure was mine')
                break
            #print(query_df(text))
            query_result = query_df(text)[query_col(text)].values
            speak(query_result)
            print(query_result)
            print(query_df(text))
        except Exception as e:
            speak(str(e))
            print(str(e))
