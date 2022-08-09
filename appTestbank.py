from lib2to3.pgen2.pgen import DFAState
import streamlit as st # web development
import numpy as np # np mean, np random 
import pandas as pd # read csv, df manipulation
import plotly.express as px # interactive charts 
import requests, io, time
from datetime import datetime

# settings
st.set_page_config(
    page_title = 'EVW | Testbank Dashboard',
    page_icon = '✅',
    layout = 'wide'
)

ds_kw = []
ds_tijd = []
ds_hz = []
testCase = None
placeholder = st.empty()

# testbank object

class TestBank(object):  

    def __init__(self, naam, transfo_ratio, nominaal_vermogen, stabieliteits_factor, tijdsinterval, tijdsduur):
        
        try:
            self.injectielink = "http://192.168.218.1/192.168.218.1/PLC_WKK/cgi-bin/OrderValues.exe?TestBank+dummy+1000Code SAIA+PDP,,R406,d+PDP,,R407,d+PDP,,R408,d+PDP,,R409,d+PDP,,R410,d+PDP,,R411,d+PDP,,R413,d+PDP,,R414,d+PDP,,R415,d+PDP,,R412,d+PDP,,R402,d+PDP,,R2377,d+PDP,,R2377,d+PDP,,R2370,d+PDP,,R2371,d+PDP,,R2476,d+PDP,,R2473,d+PDP,,R2474,d+PDP,,R2471,d+PDP,,R2470,d+PDP,,R2470,d+PDP,,R2675,d"
            requests.get(self.injectielink)
            self.url = "http://192.168.218.1/station_name/cgi-bin/ReadFile.exe?TestBank"
            requests.get(self.url)
            
            self.status = "Succes"
            
            self.created = time.perf_counter()
            self.naam = naam
            self.transfo_ratio = transfo_ratio
            self.nominaal_vermogen = nominaal_vermogen
            self.stabiliteits_factor = stabieliteits_factor
            self.tijdsinterval = tijdsinterval
            self.tijdsduur = tijdsduur
            
            print("Succes", "Connectie met testbank gemaakt.")
            
        except:
            self.status = "Error"
            print("Error", "Testbank connectie gefaald.")

    def get_metingen(self):
        
        r = requests.get(self.url)
        
        columns_list = ["1", "2", "register", "value"]
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), names=columns_list)
        
        df.drop(['1','2'], axis=1, inplace=True)

        df['register'] = df['register'].str.replace('R','').astype(int)
        df['value'] = df['value'].str.replace('d=','').astype(int)

        df.sort_values('register', inplace=True)
        
        # df['value'] = df['value'] / self.ds_bewerkingen
        
        df = df.transpose()
        data = df.iloc[1].values.flatten().tolist()

        return data
    
    def start_metingen(self):
        print("Start metingen")
        self.meten = True

    def stop_metingen(self):
        print("Stop/pauze meten")
        self.meten = False
        
    def opslaan_metingen(self):
        print("Opslaan metingen")
        self.meten = False
        self.opslaan = True
        
    def discard_metingen(self):
        print("Meet data verwijderen")
        self.opslaan = False
        self.discard = True
    
    def abandon(self):
        print("Abandon")
        
    def tijd_sinds_created(self):
        return time.perf_counter() - self.created
    
    def tijd_sinds_laatste_meting(self):
        if self.laatste_meting is not None:
            return time.perf_counter() - self.laatste_meting
        return 0

def testbank_create(naam, transfo_ratio, nominaal_vermogen, stabieliteits_factor, tijdsinterval, tijdsduur):

    test_case = TestBank(naam=naam, transfo_ratio=transfo_ratio, nominaal_vermogen=nominaal_vermogen, stabieliteits_factor=stabieliteits_factor, tijdsinterval=tijdsinterval, tijdsduur=tijdsduur)
    
    return test_case

# Streamlit pages

def page_create_testbank():
 
    st.markdown("### EVW testbank instellingen")
        
    naam = st.text_input('Naam van de testcase', type="default", value="Testbank")
    
    transfo_ratio = st.selectbox("Vermogen transfo ratio (A)", ['100/5','300/5','500/5','1000/5','3000/5','5000/5'])
    
    nominaal_vermogen = st.number_input('Nominaal vermogen (kW)', value=1000, step=1, min_value=0, max_value=100000000)
    
    stabieliteits_factor = st.number_input('Stabiliteitsfactor (%)', value=1.00, step=0.01, min_value=0.00, max_value=5.00)  
        
    tijdsinterval = st.slider('Tijdsinterval meting (minuten)', 0, 10, 5)
    tijdsduur = st.slider('Totale test tijd (minuten)', 0, 120, 30)
    
    b_bekijken = st.button('Testobject bekijken')
    b_meten = st.button('Start meten')
    
    if b_bekijken:
        with st.spinner(f"Test object aanmaken..."):
                
            testCase = testbank_create(naam, transfo_ratio, nominaal_vermogen, stabieliteits_factor, tijdsinterval, tijdsduur)
            testCase.meten = False
            
            return testCase
    
    if b_meten:
        with st.spinner(f"Test object aanmaken..."):
                
            testCase = testbank_create(naam, transfo_ratio, nominaal_vermogen, stabieliteits_factor, tijdsinterval, tijdsduur)
            testCase.meten = True
            
            return testCase

def page_dashboard(testCase):
        
    start = time.perf_counter()
        
    with placeholder.container():
                
        dsy = testCase.get_metingen()
        dsx = datetime.now().time().strftime("%H:%M:%S")
                
        ds_kw.append(dsy[8])
        ds_hz.append(float(dsy[0]/100))
        ds_tijd.append(dsx)
        
        if len(ds_kw) > 25:
            ds_kw.pop(0)
            ds_tijd.pop(0)
            ds_hz.pop(0)
            
        df_fig1 = ({"tijd":ds_tijd, "vermogen":ds_kw})
        df_fig1 = pd.DataFrame(df_fig1)
            
        df_fig2 = ({"tijd":ds_tijd, "frequentie":ds_hz})
        df_fig2 = pd.DataFrame(df_fig2)

        st.title("Testbank Dashboard")

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            
        kpi1.metric(label="🕑 Tijd (HH:MM:SS)", value=dsx)
            
        kpi2.metric(label="🔋 Actief vermogen (kW)", value=dsy[8])
            
        kpi3.metric(label="📐 Cos φ", value=f".{dsy[7]}")
            
        kpi4.metric(label="🔁 Frequentie (Hz)", value=float(dsy[0]/100))
            
        tab1, tab2 = st.tabs(["Numerieke waarden", "Trending"])

        with tab1:
            st.markdown("### Elektrische metingen")      
            
            metric1, metric4, metric7 = st.columns(3)
            metric2, metric5, metric8 = st.columns(3)
            metric3, metric6, metric9 = st.columns(3)
            metric10, metric11, metric_ = st.columns(3)
                            
            metric1.metric(label="U12 - Spanning F1", value=f"{dsy[1]} V")
            metric2.metric(label="U23 - Spanning F2", value=f"{dsy[2]} V")
            metric3.metric(label="U32 - Spanning F3", value=f"{dsy[3]} V")
            
            
            metric4.metric(label="I1 - Stroom L1", value=f"{dsy[4]} A")
            metric5.metric(label="I2 - Stroom L2", value=f"{dsy[5]} A")
            metric6.metric(label="I3 - Stroom L3", value=f"{dsy[6]} A")
            
            
            metric7.metric(label="P - Actief vermogen", value=f"{dsy[7]} kW")
            metric8.metric(label="Q - Reactief vermogen", value=f"{dsy[8]} VAR")
            metric9.metric(label="S - Schijnbaar vermogen", value=f"{dsy[9]} VA")
            
            metric10.metric(label="F - Frequentie", value=f"{dsy[0]/100} Hz")
            metric11.metric(label="PF - Cos φ", value=f".{dsy[7]}")
            
            st.markdown("### Mechanische metingen")  
            
            metric12, metric13, metric14, metric15 = st.columns(4)
            metric16, metric17, metric18, metric19 = st.columns(4)
            metric20, metric21, metric22, metric_ = st.columns(4)
            
            metric12.metric(label="Temperatuur olie 1", value=f"{dsy[11]/10} °C")
            metric13.metric(label="Temperatuur olie 2", value=f"{dsy[12]/10} °C")
            metric14.metric(label="Temperatuur water 1", value=f"{dsy[13]/10} °C")
            metric15.metric(label="Temperatuur water 2", value=f"{dsy[14]/10} °C")

            metric16.metric(label="Temperatuur inlaat 1", value=f"{dsy[15]/10} °C")
            metric17.metric(label="Temperatuur inlaat 2", value=f"{dsy[16]/10} °C")
            metric18.metric(label="Temperatuur uitlaat 1", value=f"{dsy[17]/10} °C")
            metric19.metric(label="Temperatuur uitlaat 2", value=f"{dsy[18]/10} °C")
            
            metric20.metric(label="Temperatuur omgeving", value=f"{dsy[19]/10} °C")
            metric21.metric(label="Temperatuur alternator", value=f"{dsy[20]/10} °C")
            metric22.metric(label="Olie druk", value=f"{dsy[21]/10} bar")
            
        with tab2:
            fig_col1, fig_col2 = st.columns(2)
            with fig_col1:
                st.markdown("### 🔋 Actief vermogen (kW)")
                fig = px.line(df_fig1, x="tijd", y="vermogen")
                fig.update_layout(yaxis_range=[0,testCase.nominaal_vermogen])
                st.plotly_chart(fig,use_container_width=True)
            with fig_col2:
                st.markdown("### 🔁 Frequentie (Hz)")
                fig2 = px.line(df_fig2, x="tijd", y="frequentie")
                fig2.update_layout(yaxis_range=[45,55])
                st.plotly_chart(fig2,use_container_width=True)
        
        st.markdown("""---""")
        
    return time.perf_counter() - start

# streamlit app
                
def main():
    print("--------------------------------")
    
    if 'testCase' in st.session_state:
        
        print('try')
        
        testCase = st.session_state['testCase']
        
        print('Try testCase succes: ', testCase)
        
        while testCase.meten is False:

            timer = page_dashboard(testCase)
            sleep_time = 1 - timer
            if sleep_time > 0:
                time.sleep(sleep_time)
            
        while testCase.meten is True:

            timer = page_dashboard(testCase)
            sleep_time = 1 - timer
            if sleep_time > 0:
                time.sleep(sleep_time)
        
    else:
        
        print('except')
        
        testCase = page_create_testbank()
            
        print('Except testCase: ', testCase)
        
        if testCase is not None:
            
            print('testCase is not None')
            
            print(testCase)
            
            st.session_state['testCase'] = testCase
            
            
            print('session state')
            print(st.session_state['testCase'])
            
            main()

if __name__ == "__main__":
    main()