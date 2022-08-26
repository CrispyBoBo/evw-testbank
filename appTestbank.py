import random # wordt gebruikt voor een willekeurig nummer te generen voor als het programma getest wordt
import streamlit as st # het webapp framework
import numpy as np # wiskunde pakket
import pandas as pd # pandas is gemaakt op numpy, deze gebruiken we voor onze dataframes en excel communicatie
import plotly.express as px # plotly gebruiken we voor onze grafieken
import requests, io, time # requests is het pakket voor de http requests, io is het pakket voor de file input/output, time is het pakket voor de tijd handelingen
from datetime import datetime # datetime is het pakket voor de tijd handelingen met datum

# settings van de webapp
st.set_page_config(
    page_title = 'EVW | Testbank Dashboard',
    page_icon = '✅',
    layout = 'wide'
)

# """
# ds = data serie/set, een lijst van informatie
# df = data frame, een 2D tabel met informatie met index & kolommen
# [] is een lege lijst, verzameling van informatie. Deze wordt aangemaakt zodat we aan deze lijst kunnen toevoegen.
# """

ds_kw = [] 
ds_tijd = []
ds_hz = []
ds_spanning = []
testCase = None
placeholder = st.empty()

# testbank object

class TestBank(object):  
    """TestBank opbject
    Dit is een class/object die elke keer aangemaakt wordt zodat er object georienteerd kan geprogrammeerd worden.
    De Testbank wordt aangemaakt met verschillende waarden, waarmee we deze objecten kunnen configureren adhv welke waarden onze testcase heeft.
    In de __init__ functie proberen we alles te configureren en verbinding te maken. We werken met het pricinipe EAFP.
    """
    def __init__(self, naam, transfo_ratio, nominaal_vermogen, stabieliteits_factor, tijdsinterval, tijdsduur, meet_stand, nominaal_spanning):
        
        try:
            self.injectielink = "http://192.168.218.1/192.168.218.1/PLC_WKK/cgi-bin/OrderValues.exe?TestBank+dummy+1000Code SAIA+PDP,,R406,d+PDP,,R407,d+PDP,,R408,d+PDP,,R409,d+PDP,,R410,d+PDP,,R411,d+PDP,,R413,d+PDP,,R414,d+PDP,,R415,d+PDP,,R412,d+PDP,,R402,d+PDP,,R2377,d+PDP,,R2377,d+PDP,,R2370,d+PDP,,R2371,d+PDP,,R2476,d+PDP,,R2473,d+PDP,,R2474,d+PDP,,R2471,d+PDP,,R2470,d+PDP,,R2470,d+PDP,,R2675,d"
            requests.get(self.injectielink)
            self.url = "http://192.168.218.1/station_name/cgi-bin/ReadFile.exe?TestBank"
            requests.get(self.url)
            
            self.status = "Verbonden"
            self.meet_stand = meet_stand
            self.created = time.perf_counter()
            self.naam = naam
            self.transfo_ratio = transfo_ratio
            self.nominaal_vermogen = nominaal_vermogen
            self.nominaal_spanning = nominaal_spanning
            self.stabiliteits_factor = stabieliteits_factor
            self.tijdsinterval = tijdsinterval
            self.tijdsduur = tijdsduur
            self.laatste_meting = time.perf_counter() * time.perf_counter()
            self.register_lijst = [
                'Timer',
                'F - Frequentie',
                'U12 - Spanning F1',
                'U23 - Spanning F2',
                'U32 - Spanning F3',
                'I1 - Stroom L1',
                'I2 - Stroom L2',
                'I3 - Stroom L3',
                'PF - Cos φ',
                'P - Actief vermogen',
                'Q - Reactief vermogen',
                'S - Schijnbaar vermogen',
                'Temperatuur olie 1',
                'Temperatuur olie 2',
                'Temperatuur water 1',
                'Temperatuur water 2',
                'Temperatuur inlaat 1',
                'Temperatuur inlaat 2',
                'Temperatuur uitlaat 1',
                'Temperatuur uitlaat 2',
                'Temperatuur omgeving',
                'Temperatuur alternator',
                'Olie druk',
            ]
            self.register_bewerkingen = [
                1,
                100,
                1,
                1,
                1,
                1,
                1,
                1,
                100,
                1,
                1,
                1,
                10,
                10,
                10,
                10,
                10,
                10,
                10,
                10,
                10,
                10,
                10
            ]
            self.metingen_dataset = []
            self.metingen_klaar = False
            self.run = True
            self.step_counter = 0 
            
            print("Succes", "Connectie met testbank gemaakt.")
            
        except:
            self.status = "Error"
            print("Error", "Testbank connectie gefaald.")
    
    # Hier halen we data op via de webserver, we zetten ze om naar een lijst.
    def get_metingen(self):
        
        r = requests.get(self.url)
        
        columns_list = ["1", "2", "register", "value"]
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), names=columns_list)
        
        df.drop(['1','2'], axis=1, inplace=True)

        df['register'] = df['register'].str.replace('R','').astype(int)
        df['value'] = df['value'].str.replace('d=','').astype(int)

        df.sort_values('register', inplace=True)
        
        df = df.transpose()
        data = df.iloc[1].values.flatten().tolist()

        return data
    
    # We gebruiken deze funtie om de metingen te verwerken en om deze in een dataset te zetten en bijhouden.
    def waardes_meten(self):
        
        dsy = self.get_metingen()
        ds = [int(time.perf_counter())] + dsy
        
        self.laatste_meting = time.perf_counter()
        
        for e, _ in enumerate(ds):
            ds[e] = ds[e]/self.register_bewerkingen[e]
        
        self.metingen_dataset.append(ds)
    
    # Een functie die de als antwoord geeft hoeveel seconden er gepasseerd zijn sinds de connnectie is gemaakt.
    def tijd_sinds_created(self):
        return time.perf_counter() - self.created
    
    # Een functie die weergeeft hoeveel tijd er is gepasseerd sinds de laatste meting (in seconden).
    def tijd_sinds_laatste_meting(self):
        return time.perf_counter() - self.laatste_meting
    
    # Een functie die onze opgeslagen metingen in de data set in excel steekt.
    def metingen_naar_excel(self):
        
        df = pd.DataFrame(self.metingen_dataset, columns=self.register_lijst)
                    
        self.metingen_dataset = []
                    
        writer = pd.ExcelWriter("metingen.xlsx")
        df.to_excel(writer, sheet_name='metingen', index=False, na_rep='NaN')
                    
        for column in df:
            column_length = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            writer.sheets['metingen'].set_column(col_idx, col_idx, column_length)

        print('writer save')
        writer.save()
    
    # De abandon functie, deze functie zal de tijd doorspoelen tot juist voor de meting. Momenteel print deze enkel dat hij is ingeduwt. De automatische cyclus is nog niet af. 
    def abandon(self):
        print("Abandoned", "Magische knop ingeduwt.")
    
    # Deze functie zal gebruikt worden om een waarde in een register/vlag te schrijven op de plc
    def write_value_register(self, value, register):
        return print(f' {value} - {register}')
       
    # Deze functie zal gebruikt worden om een waarde in een register/vlag te lezen van de plc 
    def read_register(self, register):
        value = random.randint(0, 100)
        return value
    
    # Deze functie zal als alles goed verlopen is in de cyclys stap, de plc laten weten dat de pc klaar is voor de volgende stap.
    # if R1000 = R1100 => volgende stap
    # De plc zet de waarde R1000 op welke stap de pc moet uitvoeren, als de pc klaar is zet hij R1100 op hetzelfde nummer.    
    def step_counter_plus(self):
        self.step_counter += 1
        self.write_value_register(self.step_counter, 'R1100')
    
    # Error schrijven naar error vlag (voor pc) op de plc    
    def in_error(self):
        self.send_value_register(1, 'F1103')
    
    # F1004 is de waar de plc laat weten dat er een meting mag volgen. Als F1004 = 1 is, mag de pc meten. Anders wacht de pc en gaan we niet de volgende stap uitvoeren. Als de stap is uitgevoerd zal de pc de vlag terug op 0 zeten.
    # If self.step_counter == R1100 - 1 && F1004 = 1: mag de pc naar de volgende stap.
    def can_continue(self):
        return self.read_register('F1004')

    def get_plc_counter(self):
        return self.read_register('R1100')

# Het aanmaken van het testbank object.        
def testbank_create(naam, transfo_ratio, nominaal_vermogen, stabieliteits_factor, tijdsinterval, tijdsduur, meet_stand, nominaal_spanning):

    test_case = TestBank(naam=naam, transfo_ratio=transfo_ratio, nominaal_vermogen=nominaal_vermogen, stabieliteits_factor=stabieliteits_factor, tijdsinterval=tijdsinterval, tijdsduur=tijdsduur, meet_stand=meet_stand, nominaal_spanning=nominaal_spanning)
    
    return test_case

# Streamlit paginas

# De pagina waar we de testbank aanmaken
def page_create_testbank():
 
    st.title("EVW testbank instellingen")
    st.markdown("Als je deze opnieuw wilt instellen, klik dan op 'ctrl'+'f5' of herlaad de pagina.")
        
    naam = st.text_input('Naam van de testcase', type="default", value="Testbank")
    
    transfo_ratio = st.selectbox("Vermogen transfo ratio (A)", ['100/5','300/5','500/5','1000/5','3000/5','5000/5'])
    
    nominaal_vermogen = st.number_input('Nominaal vermogen (kW)', value=1000, step=1, min_value=0, max_value=100000000)
    
    nominaal_spanning = st.number_input('Nominale spanning (V)', value=400, step=1, min_value=0, max_value=1000)
    
    stabieliteits_factor = st.number_input('Stabiliteitsfactor (%)', value=1.00, step=0.01, min_value=0.00, max_value=5.00)  
        
    tijdsinterval = st.slider('Tijdsinterval meting (minuten)', 0, 10, 5)
    tijdsduur = st.slider('Totale test tijd (minuten)', 0, 120, 30)
    
    meet_stand = st.radio(
     "Automatisch of handmatig metingen opslaan:",
     ( 'Handmatig', 'Automatisch', 'Overzicht')
     )
    
    b_bekijken = st.button('Connectie met testbank maken')
    
    st.markdown("""---""")
    
    if b_bekijken:
        with st.spinner(f"Test object aanmaken..."):  
            
            testCase = testbank_create(naam, transfo_ratio, nominaal_vermogen, stabieliteits_factor, tijdsinterval, tijdsduur, meet_stand, nominaal_spanning)
            testCase.meten = False
    
            return testCase

# Algemeen dashboard pagina
def page_dashboard(testCase):
        
    with placeholder.container():
                
        dsy = testCase.get_metingen()
        dsx = datetime.now().time().strftime("%H:%M:%S")
        
        ds_kw.append(dsy[8])
        ds_hz.append(dsy[0]/testCase.register_bewerkingen[1])
        ds_spanning.append(dsy[1])
        ds_tijd.append(dsx)
        
        if len(ds_kw) > 50:
            ds_kw.pop(0)
            ds_tijd.pop(0)
            ds_hz.pop(0)
            ds_spanning.pop(0)
            
        df_fig1 = ({"tijd":ds_tijd, "vermogen":ds_kw})
        df_fig1 = pd.DataFrame(df_fig1)
            
        df_fig2 = ({"tijd":ds_tijd[-30:], "frequentie":ds_hz[-30:]})
        df_fig2 = pd.DataFrame(df_fig2)
        
        df_fig4 = ({"tijd":ds_tijd[-30:], "spanning":ds_spanning[-30:]})
        df_fig4 = pd.DataFrame(df_fig4)

        st.title(f"{testCase.naam}")
        st.markdown(f"Laatste meting: {testCase.tijd_sinds_laatste_meting()}s geleden | status: {testCase.status} | run: {testCase.run}")
            
        tab1, tab2 = st.tabs(["Numerieke waarden", "Trending"])

        with tab1:
            
            st.markdown("### Mechanische metingen")  
            
            metric12, metric13, metric14, metric15 = st.columns(4)
            metric16, metric17, metric18, metric19 = st.columns(4)
            metric20, metric21, metric22, metric_ = st.columns(4)
            
            metric12.metric(label="Temperatuur olie 1", value=f"{dsy[11]/testCase.register_bewerkingen[12]} °C")
            metric13.metric(label="Temperatuur olie 2", value=f"{dsy[12]/testCase.register_bewerkingen[13]} °C")
            metric14.metric(label="Temperatuur water 1", value=f"{dsy[13]/testCase.register_bewerkingen[14]} °C")
            metric15.metric(label="Temperatuur water 2", value=f"{dsy[14]/testCase.register_bewerkingen[15]} °C")

            metric16.metric(label="Temperatuur inlaat 1", value=f"{dsy[15]/testCase.register_bewerkingen[16]} °C")
            metric17.metric(label="Temperatuur inlaat 2", value=f"{dsy[16]/testCase.register_bewerkingen[17]} °C")
            metric18.metric(label="Temperatuur uitlaat 1", value=f"{dsy[17]/testCase.register_bewerkingen[18]} °C")
            metric19.metric(label="Temperatuur uitlaat 2", value=f"{dsy[18]/testCase.register_bewerkingen[19]} °C")
            
            metric20.metric(label="Temperatuur omgeving", value=f"{dsy[19]/testCase.register_bewerkingen[20]} °C")
            metric21.metric(label="Temperatuur alternator", value=f"{dsy[20]/testCase.register_bewerkingen[21]} °C")
            metric22.metric(label="Olie druk", value=f"{dsy[21]/testCase.register_bewerkingen[22]} bar")
            
            st.markdown("### Elektrische metingen")      
            
            metric1, metric4, metric7, metric10 = st.columns(4)
            metric2, metric5, metric8, metric11 = st.columns(4)
            metric3, metric6, metric9, metric_ = st.columns(4)
                          
            metric1.metric(label="U12 - Spanning F1", value=f"{dsy[1]} V")
            metric2.metric(label="U23 - Spanning F2", value=f"{dsy[2]} V")
            metric3.metric(label="U32 - Spanning F3", value=f"{dsy[3]} V")
            metric10.metric(label="F - Frequentie", value=f"{dsy[0]/testCase.register_bewerkingen[1]} Hz")
            
            metric4.metric(label="I1 - Stroom L1", value=f"{dsy[4]} A")
            metric5.metric(label="I2 - Stroom L2", value=f"{dsy[5]} A")
            metric6.metric(label="I3 - Stroom L3", value=f"{dsy[6]} A")
            metric11.metric(label="PF - Cos φ", value=f"{dsy[7]/testCase.register_bewerkingen[8]}")
            
            metric7.metric(label="P - Actief vermogen", value=f"{dsy[8]} kW")
            metric8.metric(label="Q - Reactief vermogen", value=f"{dsy[9]} VAR")
            metric9.metric(label="S - Schijnbaar vermogen", value=f"{dsy[10]} VA")
            
        with tab2:
            
            st.markdown("### ⚡ Actief vermogen (kW)")
            fig = px.line(df_fig1, x="tijd", y="vermogen")
            fig.update_layout(yaxis_range=[0,testCase.nominaal_vermogen*1.2])
            st.plotly_chart(fig,use_container_width=True)
            
            fig_col1, fig_col2 = st.columns(2)
            
            with fig_col1:
                st.markdown("### 🔋 Spanning (V)")
                fig4 = px.line(df_fig4, x="tijd", y="spanning")
                fig4.update_layout(yaxis_range=[0,testCase.nominaal_spanning*1.25])
                st.plotly_chart(fig4,use_container_width=True)
                
            with fig_col2:
                st.markdown("### 🔁 Frequentie (Hz)")
                fig2 = px.line(df_fig2, x="tijd", y="frequentie")
                fig2.update_layout(yaxis_range=[45,55])
                st.plotly_chart(fig2,use_container_width=True)
        
        st.markdown("""---""")

# streamlit main app script
                
def main():
    
    if 'testCase' in st.session_state:
        
        testCase = st.session_state['testCase']
        
        # Overzicht
        while testCase.meet_stand == 'Overzicht':
            
            start = time.perf_counter()
            
            page_dashboard(testCase)
            
            end = time.perf_counter()
            timedelta = end - start
            sleep_time = 1 - timedelta
            
            if sleep_time > 0:
                time.sleep(sleep_time)
                
        # Automatisch
        if testCase.meet_stand == 'Automatisch':
            
            with st.sidebar:
                
                if st.button("pause / continue"):
                    testCase.run = not testCase.run

                if st.button('Meting vroegtijdig naar excel'):
                    testCase.metingen_naar_excel()
                    
                if st.button('Abandon'):
                    testCase.abandon()
                
                st.markdown("""---""")        
            
        while testCase.meet_stand == 'Automatisch':
            
            start = time.perf_counter()
            
            if testCase.can_continue():
                plc_step = testCase.get_plc_counter()
                
                match plc_step:
                
                    case 1:
                        # ....
                        testCase.step_counter_plus()

                    case 2:
                        # ....
                        testCase.step_counter_plus()
                    
                    case 3:
                        # ....
                        testCase.step_counter_plus()

                    case 4:
                        # ....
                        testCase.step_counter_plus()

                    case 5:
                        # ....
                        testCase.step_counter_plus()
                    
                    case 6:
                        # ....
                        testCase.step_counter_plus()

                    case 7:
                        # ....
                        testCase.step_counter_plus()
                        
                    case 8:
                        # ....
                        testCase.step_counter_plus()
                        
            page_dashboard(testCase)
            
            end = time.perf_counter()
            timedelta = end - start
            sleep_time = 1 - timedelta
            
            if sleep_time > 0:
                time.sleep(sleep_time)
                
        # Handmatig
        if testCase.meet_stand == 'Handmatig':

            with st.sidebar:
                
                if st.button('Meting opslaan'):
                    testCase.waardes_meten()
                
                if st.button('Metingen naar excel'):
                   testCase.metingen_naar_excel()
                
                st.markdown("""---""")     
            
        while testCase.meet_stand == 'Handmatig':
            
            start = time.perf_counter()
            
            page_dashboard(testCase)
                    
            end = time.perf_counter()
            timedelta = end - start
            sleep_time = 1 - timedelta
            
            if sleep_time > 0:
                time.sleep(sleep_time)
            
    else:
        
        testCase = page_create_testbank()

        if testCase is not None:
            
            st.session_state['testCase'] = testCase

            main()

if __name__ == "__main__":
    main()