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
    """TestBank object
    Dit is een class/object die elke keer aangemaakt wordt zodat er object georienteerd kan geprogrammeerd worden.
    De Testbank wordt aangemaakt met verschillende waarden, waarmee we deze objecten kunnen configureren adhv welke waarden onze testcase heeft.
    In de __init__ functie proberen we alles te configureren en verbinding te maken. We werken met het pricinipe EAFP.
    """
    def __init__(self, naam, transfo_ratio, nominaal_vermogen, stabieliteits_factor, tijdsinterval, tijdsduur, meet_stand, nominaal_spanning):
        
        try:
            # Ip van de plc.
            self.ip = "192.168.218.1"
            
            # De injectielink voor de Ordervalues.
            self.injectielink = f"{self.ip}/PLC_TESTBANK/cgi-bin/OrderValues.exe?TestBankMetingen+dummy+1000Code SAIA+PDP,,R413,d+PDP,,R414,d+PDP,,R415,d+PDP,,R416,d+PDP,,R417,d+PDP,,R418,d+PDP,,R420,d+PDP,,R421,d+PDP,,R422,d+PDP,,R419,d+PDP,,R409,d+PDP,,R500,d+PDP,,R501,d+PDP,,R502,d+PDP,,R503,d+PDP,,R504,d+PDP,,R505,d+PDP,,R506,d+PDP,,R507,d+PDP,,R508,d+PDP,,R509,d+PDP,,R510,d+PDP,,R511,d+PDP,,R512,d+PDP,,R513,d+PDP,,R514,d"
            
            # De url om de ordervalues file "testbank" uit te lezen.
            self.url = f"http://{self.ip}/PLC_TESTBANK/cgi-bin/ReadFile.exe?TestBankMetingen"
            
            # Write & read val links
            self.url_readval = f"http://{self.ip}/PLC_TESTBANK/cgi-bin/readVal.exe?"
            self.url_writeval = f"http://{self.ip}/PLC_TESTBANK/cgi-bin/writeVal.exe?"

            # Hier injecteren we de ordervalues & lezen we ze eens uit (in de background), als dit faalt stopt de try loop en is de connectie mislukt.
            requests.get(self.injectielink)
            requests.get(self.url)
            
            # Standaard waarden die we nodig hebben en moeten zetten zodat ze bestaan enkel als de request een succes was.
            self.metingen_dataset = []
            self.metingen_klaar = False
            self.run = True
            self.step_counter = 0 
            self.status = "Verbonden"

            # Deze waarden worden doorgegeven door de create functie. 
            self.meet_stand = meet_stand
            self.naam = naam
            self.transfo_ratio = transfo_ratio
            self.nominaal_vermogen = nominaal_vermogen
            self.nominaal_spanning = nominaal_spanning
            self.stabiliteits_factor = stabieliteits_factor
            self.tijdsinterval = tijdsinterval
            self.tijdsduur = tijdsduur

            self.created = time.perf_counter() # Een object waarde die we aanmaken, mocht deze waarde nodig zijn.
            self.laatste_meting = 0 # Laatste meting.
            self.sinds_laatste_meting = time.perf_counter() * time.perf_counter() # De tijd sinds de laatste meting, zeer groot zodat we zeker meten eerste keer. Deze waarde kunnen we manipuleren met de abandon knop.

            # De titels van de register, in juiste volgorde (na sorting registers van klein naar groot) voor het excel bestand voor An.
            self.register_lijst = [
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
                'Olie druk 1',
                'Olie druk 2'
                'Temperatuur water in',
                'Temperatuur water uit',
                'Temperatuur alternator',
                'Temperatuur inlaat',
                'Temperatuur afblaas',
                'Temperatuur uitlaat 1',
                'Temperatuur uitlaat 2',
                'Temperatuur wikkeling 1',
                'Temperatuur wikkeling 2',
                'Temperatuur wikkeling 3',
                'Temperatuur olie 1',
                'Temperatuur olie 2',
                'Temperatuur omkasting',

            ]
            # De delingen voor de register waardes, in juiste volgorde (na sorting registers van klein naar groot).
            self.register_bewerkingen = [
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
                10,
                10,
                10,
                10,
                10,
            ]
            
            print("Succes", "Connectie met testbank gemaakt.")
            
        except:
            # De except zal runnen als de try loop ergens faalt. Dit is zodat het programma niet crasht maar gewoon in de console een error print zal geven.
            # In 99.9% van de gevallen zal dit enkel gebeuren omdat de connectie tussen de plc & pc niet lukt. 
            self.status = "Error"
            print("Error", "Testbank connectie gefaald.")
    
    # Hieronder staan functies die bij het object horen die we aanmaken. 
    
    def get_metingen(self):
        # Hier halen we data op via de webserver, we zetten ze om naar een lijst.
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
    
    def waardes_cachen(self):
        # We gebruiken deze funtie om de metingen te verwerken en om deze in een dataset te zetten en bijhouden.
        dsy = self.get_metingen()
        ds = [datetime.now().time().strftime("%H:%M:%S")] + dsy
        
        self.laatste_meting = time.perf_counter()
        
        for e, _ in enumerate(ds):
            ds[e] = ds[e]/self.register_bewerkingen[e]
        
        self.metingen_dataset.append(ds)
   
    def tijd_sinds_created(self):
        # Een functie die de als antwoord geeft hoeveel seconden er gepasseerd zijn sinds de connnectie is gemaakt.
        return time.perf_counter() - self.created
    
   
    def tijd_sinds_laatste_meting(self):
        # Een functie die onze laatste meting waarde instelt.
        self.sinds_laatste_meting = time.perf_counter() - self.laatste_meting
    
    
    def metingen_naar_excel(self):
        # Een functie die onze opgeslagen metingen in de data set in excel steekt.
        df = pd.DataFrame(self.metingen_dataset, columns=['Tijd']+self.register_lijst)
                    
        self.metingen_dataset = []
                    
        writer = pd.ExcelWriter("metingen.xlsx")
        df.to_excel(writer, sheet_name='metingen', index=False, na_rep='NaN')
                    
        for column in df:
            column_length = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            writer.sheets['metingen'].set_column(col_idx, col_idx, column_length)

        print('writer save')
        writer.save()
    
    def abandon(self):
        # De abandon functie, deze functie wordt opgeroepen door de abonden knop. Hier kunnen we de functionaliteit inzetten.
        self.sinds_laatste_meting = self.tijdsinterval - 5
        print("Abandon")
    
    def write_register(self, value, register):
        # Deze functie zal gebruikt worden om een waarde in een register/vlag te schrijven op de plc.
        r = requests.get(f"{self.url_writeval}PDP,,{register},d+{value}")
        print(r)
       
    def read_register(self, register):
        # Deze functie zal gebruikt worden om een waarde in een register/vlag te lezen van de plc.
        value = requests.get(f"{self.url_readval}PDP,,{register},d")
        return int(value)
    
    def step_counter_plus(self):
        # Deze functie zal als alles goed verlopen is in de cyclys stap, de plc laten weten dat de pc klaar is voor de volgende stap.
        # bv if R1000 = R1100 => volgende stap
        # De plc zet de waarde R1000 op welke stap de pc moet uitvoeren, als de pc klaar is zet hij R1100 op hetzelfde nummer.    
        self.step_counter += 1
        self.write_register(self.step_counter, 'R1100')
        self.write_register(0, 'F1004')

    def in_error(self):
        # Error schrijven naar error vlag (voor pc) op de plc.   
        self.send_value_register(1, 'F1103')
    
    def mag_meten(self):
        # F1004 is de waar de plc laat weten dat er een meting mag volgen. Als F1004 = 1 is, mag de pc meten. Anders wacht de pc en gaan we niet de volgende stap uitvoeren. Als de stap is uitgevoerd zal de pc de vlag terug op 0 zeten.
        # bv: If self.step_counter == R1100 - 1 && F1004 = 1: mag de pc naar de volgende stap.
        return self.read_register('F1004')

    def get_plc_counter(self):
        # Deze functie return het register R1100, de stap counter op de plc.
        return self.read_register('R1100')


# Algemene functies

def testbank_create(naam, transfo_ratio, nominaal_vermogen, stabieliteits_factor, tijdsinterval, tijdsduur, meet_stand, nominaal_spanning):
    # Het aanmaken van het testbank object. 
    test_case = TestBank(naam=naam, transfo_ratio=transfo_ratio, nominaal_vermogen=nominaal_vermogen, stabieliteits_factor=stabieliteits_factor, tijdsinterval=tijdsinterval, tijdsduur=tijdsduur, meet_stand=meet_stand, nominaal_spanning=nominaal_spanning)
    
    return test_case


# Streamlit paginas

def page_create_testbank():
    # De pagina waar we de testbank aanmaken.
    st.title("EVW testbank instellingen")
    st.markdown("Als je deze opnieuw wilt instellen, klik dan op 'ctrl'+'f5' of herlaad de pagina.")

    # Dit zijn de inputs die we vragen en adhv deze waardes het object aanmaken.   
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
        #Als de knop 'Connectie met testbank maken' ingeduwt is maken we het object aan. Deze knop laat ons ook herlopen door de cycle maar nu zal het object in onze cache gestoken worden.
        with st.spinner(f"Test object aanmaken..."):  
            
            testCase = testbank_create(naam, transfo_ratio, nominaal_vermogen, stabieliteits_factor, tijdsinterval, tijdsduur, meet_stand, nominaal_spanning)
            testCase.meten = False
    
            return testCase


def page_dashboard(testCase):
    # Algemeen dashboard pagina
    
    
    with placeholder.container():
        # De placeholder.container gebruiken we om de content vanboven te plaatsen en continue te vervangen.

        # Dsy & dsx zijn onze data lijsten. De ene zal onze metingen bevatten en de andere de tijd.
        dsy = testCase.get_metingen()
        dsx = datetime.now().time().strftime("%H:%M:%S")
        
        # Deze 4 zijn data lijsten die we gaan tonen
        ds_kw.append(dsy[8])
        ds_hz.append(dsy[0]/testCase.register_bewerkingen[0])
        ds_spanning.append(dsy[1])
        ds_tijd.append(dsx)
        
        if len(ds_kw) > 50:
            # Als onze lengte van onze datalijst groter is dan 50, smijten we da eerste waardes uit onze 4 datalijsten.
            ds_kw.pop(0)
            ds_tijd.pop(0)
            ds_hz.pop(0)
            ds_spanning.pop(0)

        # Hier maken we onze dataframe aan voor onze grafieken.
        df_fig1 = ({"tijd":ds_tijd, "vermogen":ds_kw})
        df_fig1 = pd.DataFrame(df_fig1)
            
        df_fig2 = ({"tijd":ds_tijd[-30:], "frequentie":ds_hz[-30:]})
        df_fig2 = pd.DataFrame(df_fig2)
        
        df_fig4 = ({"tijd":ds_tijd[-30:], "spanning":ds_spanning[-30:]})
        df_fig4 = pd.DataFrame(df_fig4)

        # Titel van de metingen pagina & aanmaken van onze 2 tabs.
        st.title(f"{testCase.naam}")
            
        tab1, tab2 = st.tabs(["Numerieke waarden", "Trending"])

        with tab1:
            # Op tab 1:
            st.markdown("### Mechanische metingen")  
            
            # Onze kolom plaatsen op de pagina reserveren voor deze waardes.
            metric12, metric13, metric14, metric15 = st.columns(4)
            metric16, metric17, metric18, metric19 = st.columns(4)
            metric20, metric21, metric22, metric23 = st.columns(4)
            metric24, metric25, metric26, metric_ = st.columns(4)
            
            # Onze waardes defineren. 
            metric12.metric(label="Olie druk 1", value=f"{dsy[11]/testCase.register_bewerkingen[11]} bar")
            metric13.metric(label="Olie druk 2", value=f"{dsy[12]/testCase.register_bewerkingen[12]} bar")
            metric14.metric(label="Temperatuur olie 1", value=f"{dsy[23]/testCase.register_bewerkingen[23]} °C")
            metric15.metric(label="Temperatuur olie 2", value=f"{dsy[24]/testCase.register_bewerkingen[24]} °C")

            metric16.metric(label="Temperatuur alternator", value=f"{dsy[15]/testCase.register_bewerkingen[15]} °C")
            metric17.metric(label="Temperatuur inlaat", value=f"{dsy[16]/testCase.register_bewerkingen[16]} °C")
            metric18.metric(label="Temperatuur omkasting", value=f"{dsy[25]/testCase.register_bewerkingen[25]} °C")
            metric19.metric(label="Temperatuur afblaas", value=f"{dsy[17]/testCase.register_bewerkingen[17]} °C")

            metric20.metric(label="Temperatuur water in", value=f"{dsy[13]/testCase.register_bewerkingen[13]} °C")
            metric21.metric(label="Temperatuur water uit", value=f"{dsy[14]/testCase.register_bewerkingen[14]} °C")
            metric22.metric(label="Temperatuur uitlaat 1", value=f"{dsy[18]/testCase.register_bewerkingen[18]} °C")
            metric23.metric(label="Temperatuur uitlaat 2", value=f"{dsy[19]/testCase.register_bewerkingen[19]} °C")

            metric24.metric(label="Temperatuur wikkeling 1", value=f"{dsy[20]/testCase.register_bewerkingen[20]} °C")
            metric25.metric(label="Temperatuur wikkeling 2", value=f"{dsy[21]/testCase.register_bewerkingen[21]} °C")
            metric26.metric(label="Temperatuur wikkeling 3", value=f"{dsy[22]/testCase.register_bewerkingen[22]} °C")

            st.markdown("### Elektrische metingen")
            
            # Onze kolom plaatsen op de pagina reserveren voor deze waardes.
            metric1, metric4, metric7, metric10 = st.columns(4)
            metric2, metric5, metric8, metric11 = st.columns(4)
            metric3, metric6, metric9, metric__ = st.columns(4)

            # Onze waardes defineren.               
            metric1.metric(label="U12 - Spanning F1", value=f"{dsy[1]} V")
            metric2.metric(label="U23 - Spanning F2", value=f"{dsy[2]} V")
            metric3.metric(label="U32 - Spanning F3", value=f"{dsy[3]} V")
            metric10.metric(label="F - Frequentie", value=f"{dsy[0]/testCase.register_bewerkingen[0]} Hz")
            
            metric4.metric(label="I1 - Stroom L1", value=f"{dsy[4]} A")
            metric5.metric(label="I2 - Stroom L2", value=f"{dsy[5]} A")
            metric6.metric(label="I3 - Stroom L3", value=f"{dsy[6]} A")
            metric11.metric(label="PF - Cos φ", value=f"{dsy[7]/testCase.register_bewerkingen[7]}")
            
            metric7.metric(label="P - Actief vermogen", value=f"{dsy[8]} kW")
            metric8.metric(label="Q - Reactief vermogen", value=f"{dsy[9]} VAR")
            metric9.metric(label="S - Schijnbaar vermogen", value=f"{dsy[10]} VA")
            
        with tab2:
            # Op tab 2:

            # Onze grote grafiek aanmaken voor vermogen.
            st.markdown("### ⚡ Actief vermogen (kW)")
            fig = px.line(df_fig1, x="tijd", y="vermogen")
            fig.update_layout(yaxis_range=[0,testCase.nominaal_vermogen*1.25])
            st.plotly_chart(fig,use_container_width=True)
            
            # Onze 2 kleine grafieken een plaats geven in kolommen.
            fig_col1, fig_col2 = st.columns(2)
            
            with fig_col1:
                # Figuur 1 defineren
                st.markdown("### 🔋 Spanning (V)")
                fig4 = px.line(df_fig4, x="tijd", y="spanning")
                fig4.update_layout(yaxis_range=[0,testCase.nominaal_spanning*1.25])
                st.plotly_chart(fig4,use_container_width=True)
                
            with fig_col2:
                # Figuur 2 defineren
                st.markdown("### 🔁 Frequentie (Hz)")
                fig2 = px.line(df_fig2, x="tijd", y="frequentie")
                fig2.update_layout(yaxis_range=[45,55])
                st.plotly_chart(fig2,use_container_width=True)
        
        st.markdown("""---""")


                
def main():
    # streamlit main app cycle

    if 'testCase' in st.session_state:
        # als testcase al bestaat en in onze caching zit:
        testCase = st.session_state['testCase']
        
        
        if testCase.meet_stand == 'Overzicht':
            # Overzicht stand
            while testCase.meet_stand == 'Overzicht':
                # De while loop / cycle die we zullen doorlopen om de metingen elke keer te tonen.
                
                # Start is ons moment wanneer de loop starte, deze gebruiken we om een totale seconde zo dicht mogelijk te benaderen.
                start = time.perf_counter()
            
                # Ons dashboard scherm die de waarden weergeeft.S
                page_dashboard(testCase)

                # End is onze tijd wanneer de loop zo goed als klaar is
                end = time.perf_counter()

                # Onze time delta is hoelang de loop erover gedaan heeft
                timedelta = end - start

                # Sleep time is hoeveel seconden de cycle moet pauzeren, hiervan trekken we onze timedelta aangezien we deze tijd al 'gepauzeerd' hebben.
                sleep_time = 1 - timedelta

                # Hier checken we als onze sleeptime groter is dan 0, soms doordat een cycle eens langer duurt dan 1seconde (traag internet bv) kan het zijn dat onze sleeptime negatief zal uitkomen. We kunnen natuurlijk niet negatief aantal tijd wachten. 
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
        
        elif testCase.meet_stand == 'Automatisch':
            # Automatische stand    
            with st.sidebar:
                
                if st.button("pause / continue"):
                    # De run status van ons object omdraaien. not zal de bool/vlag inverteren.
                    testCase.run = not testCase.run

                if st.button('Meting vroegtijdig naar excel'):
                    # Mocht door 1 of andere reden alle metingen al in excel moeten zitten.
                    testCase.metingen_naar_excel()
                    
                if st.button('Abandon'):
                    # De abandon knop, hier kunnen we de tijd sinds laatste metingen zetten op een andere waarde
                    testCase.abandon()
                
                st.markdown("""---""")        
            
            while testCase.meet_stand == 'Automatisch':
                # Automatische cycle met zelfde werking als overzicht, behalve de metingen.
                start = time.perf_counter()
                
                # We checken als de plc zegt dat we mogen meten
                if testCase.mag_meten():
                    
                    # We kijken in welke stap de plc momenteel zit, en gaan onze logica uitvoeren.
                    plc_step = testCase.get_plc_counter()
                    
                    # We gebruiken match om een bepaalde stap te matchen aan de plc en deze uit te voeren. We kunnen zoveel cases/stappen toe voegen dat we maar willen. Functionaliteit zetten we achter onze 'case n:' en op het einde gaan we 1 stap omhoog.
                    match plc_step:
                    
                        case 1:
                            # Als stap 1 gedaan is, zetten wij onze eigen counter 1tje hoger zodat de plc weet dat we klaar zijn.
                            # We zetten ook ons register die zegt dat we mogen meten terug op 0 in deze functie.
                            testCase.step_counter_plus()

                        case 2:
                            testCase.step_counter_plus()
                        
                        case 3:
                            testCase.step_counter_plus()

                        case 4:
                            testCase.step_counter_plus()

                        case 5:
                            testCase.step_counter_plus()
                        
                        case 6:
                            testCase.step_counter_plus()

                        case 7:
                            testCase.step_counter_plus()
                            
                        case 8:
                            testCase.step_counter_plus()
                            
                page_dashboard(testCase)
                
                end = time.perf_counter()
                timedelta = end - start
                sleep_time = 1 - timedelta
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
        elif testCase.meet_stand == 'Handmatig':
            # Handmatige stand
            with st.sidebar:
                
                if st.button('Meting opslaan'):
                    # Hier slaan we de metingen op in onze cache.
                    testCase.waardes_cachen()
                
                if st.button('Metingen naar excel'):
                    # Hier zetten we onze metingen van onze cache in een excel bestand.
                    testCase.metingen_naar_excel()
                
                st.markdown("""---""")     
            
            while testCase.meet_stand == 'Handmatig':
                # Handmatige cycle
                start = time.perf_counter()
            
                page_dashboard(testCase)
                    
                end = time.perf_counter()
                timedelta = end - start
                sleep_time = 1 - timedelta
            
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
    else:
        # Als ons object nog niet bestaat/in onze cache zit
        testCase = page_create_testbank()

        if testCase is not None:
            # Als ons object al bestaad, maar nog niet in onze cache zit.
            st.session_state['testCase'] = testCase

            # We herlopen door main, aangezien ons object nu in onze cache zit zullen we iets anders uitvoeren (recursive function).
            main()

if __name__ == "__main__":
    main()