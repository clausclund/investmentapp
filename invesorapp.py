# -*- coding: utf-8 -*-

import dash
from dash import dcc
from dash import html
from dash import Dash, dcc, html, Input, Output, State, ALL, Patch
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
# Declare server for Heroku deployment. Needed for Procfile.
server = app.server

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Investering med dansk skat"), style={'textAlign': 'center'})
    ]),
    dbc.Row([
        dbc.Col(dcc.Markdown('''
            Denne beregner tager udgagspunkt i et investeringsscenarie under danske skatteforhold.
            Modellen tager udgangspunkt i et selvvalgt forventet gennemsnitligt årligt afkast og inflation.
            Se forklaringerne nederst på siden for detaljerne omkring modellen
            
            '''))
    ]),
    dbc.Row([
        dbc.Col([
            #html.Label("Current year: "),
            #dcc.Input(id="current-year", type="number", value=2023, className="form-control mb-3"),
            html.Label("Nuværende alder:"),
            dcc.Input(id="current-age", type="number", value=30, className="form-control mb-3"),
            html.Label("Forventet levealder:"),
            dcc.Input(id="final-age", type="number", value=95, className="form-control mb-3"),
            html.Label("Nuværende værdi af investeringer:"),
            dcc.Input(id="current-investments", type="number", value=100000, className="form-control mb-3"),
            html.Label("Forventet årligt afkast af investeringer (før inflation) i %:"),
            dcc.Input(id="expected-yield", type="number", value=9, className="form-control mb-3"),
            html.Label("Forventet årlig inflation i %:"),
            dcc.Input(id="expected-inflation", type="number", value=2, className="form-control mb-3"),
        ], className="col-md-6"),
        dbc.Col([
            html.H5("Årlige udgifter"),
            html.Div(id = 'expenses_container', children=[]),
            html.Button("Tilføj udgift", id="add-expense", n_clicks=0,className="btn btn-primary mb-3", style = {'width': '200px'}),
            html.Button("Fjern sidste udgift", id="remove-expense", n_clicks=0, className="btn btn-danger mb-3",style = {'width': '200px'}),
            html.H5("Lønindtægter "),
            html.Div(id='income-container', children=[]),
            html.Button("Tilføj lønindtægt", id="add-income", n_clicks=0, className="btn btn-primary mb-3",style = {'width': '200px'}),
            html.Button("Fjern sidste lønindtægt", id="remove-income", className="btn btn-danger mb-3",style = {'width': '200px'}),
            #html.Button("Kør beregningen", id="calculate-button", n_clicks=0, className="btn btn-success mb-3"),
            html.Div(id="results"),
        ], className="col-md-6")
    ]),
  
    dbc.Row([
        html.Button("Kør beregningen", id="calculate-button", n_clicks=0, className="btn btn-success mb-3")
    ]),
    dbc.Row([
        dbc.Col(dcc.Markdown('''
           
             __Grafer__
            
            Hold musen over grafen for at se data for grafen. Du kan også zoome ind på et segment af grafen ved at markere en del med musen.
            dobbeltklik på plottet for at zoome ud igen. Dobbeltklik på grafforklaringen til højre for at filtrere.
            '''))
    ]),
    
    dbc.Row([
        dbc.Col(
            dcc.Graph(id='investment-chart'),
            className="mt-3"
        )
    ]),
    dbc.Row([
        dbc.Col(
            dcc.Graph(id='balance-chart'),
            className="mt-3"
        )
    ]),
    dbc.Row([
        dbc.Col(dcc.Markdown('''
             ##### Nuværende alder
             
             Den giver vist sig selv...
             
             ##### Forventet levealder
             
             Den alder hvor du forventer at skulle i graven.Dine investeringer skal ikke nå at gå i minus før du dør.
             Er du rigtig dygtig, ender du omkring 0kr ;)
                
             ##### Nuværende værdi af investeringer
             
             Din nuværende beholdning af aktiver. Beregneren antager at det hele står på et normalt aktiedepot.
             
             ##### Forventet årligt afkast før inflation
             
             Hvor meget forventer du i gennemsnitligt årligt afkast på dine investeringer? Det afhænger af din porteføljesammensætning.
             Mange regner med omkring 10% som gennemsnitligt markedsafkast for en bredt investeret globalportefølje.
             
             ##### Forventet årlig inflation
             
             Hvilken gennemsnitlig årlig inflation forventer du? Historisk set har der været 2-3%.
             
             ##### Årlige udgifter
            
            Du har mulighed for at indtaste årlige udgifter (efter skat), i selvvalgte intervaller af levetiden.
            Har man eksempelvis en forventning om at bruge 180.000kr årligt resten af livet kan man indtaste dette.
            Man kan også tilføje flere udgifter hvis man regner med at have variable udgifter i sin levetid.
            Det kunne eksempelvis være at man regner med at have en ekstra udgift på 60.000 kr årligt til barn
            fra man er 30 år til man er 48 år. Man kan således godt specificere overlappende udgifter.
            Der er mulighed for at navngive de forskellige udgifter så man ikke mister overblikket.
            
            ##### Årlige Lønindtægter
            
            På samme måde som for udgifter, kan man specificere sin årlige lønindtægt i løbet af sin levetid.
            Bemærk at lønindtægter skal angives før skat, da modellen tager højde for beskatning.
            De første 48.000kr årligt beskattes således ikke men fratrækkes kun 8% i AM-bidrag. 
            Alt fra 48.000kr til topskattegrænsen på 568.900 fratrækkes først 8% AM-bidrag og beskattes efterfølgende med 38%.
            Alt over topskattegrænsen fratrækkes først 8% AM-bidrag, dernæst 15% topskat, og slutteligt 38% skat.
            Man kan godt specificere overlappende indtægter.
            Modellen har på nuværende tidspunkt ikke mulighed for at specificere andre typer indtægter.
            Der er mulighed for at navngive de forskellige indtægter så man ikke mister overblikket.
            
            ##### Investeringer
            
            Modellen ser på de udgifter og indtægter som du har specificeret. Hvis dine lønindtægter efter
            skat er højere end dine udgifter, så lægges hele overskuddet til dine investeringer.
            Ønsker du at lægge noget til side til en opsparing, kan dette angives som en udgift.
            Hvis dine lønindtægter ikke kan dække dine udgifter det pågældende år, 
            fratrækked det nødvendige udtræk fra dine investeringer, for at kunne dække udgifterne efter skat.
            Beregneren antager at dine aktiver står på et almindeligt aktiedepot og at du gør brug af
            værdipapirer som er realisationsbeskattede. Modellen tager højde for en progressionsgrænse for realiseret afkast.
            Alt afkast under progressionsgrænsen på 58.900kr beskattes med 27%. Alt afkast derover beskattes med 42%.
            
            '''))
    ])
])


@app.callback(
    Output("expenses_container", "children"), 
    [Input("add-expense", "n_clicks"), Input("remove-expense", "n_clicks")],
    [State('expenses_container', 'children')]
)
def modify_expenses_container(add_clicks, remove_clicks, div_children):

    triggered_id = dash.callback_context.triggered[0]['prop_id']
    if triggered_id == "add-expense.n_clicks":
        # Add a new expense input field
        new_child = html.Div(children=[
            html.Label(f"Udgift {len(div_children) + 1}: "),
            dcc.Input(id=f"expense-name-{len(div_children)}", type="text", className="form-control mb-3", value="Beskrivende tekst (valgfri)"),
            html.Label("Beløb årligt (Efter skat): "),
            dcc.Input(id=f"expense-{len(div_children)}", type="number", className="form-control mb-3"),
            html.Label("Alder hvor udgift starter: "),
            dcc.Input(id=f"age-expense-start-{len(div_children)}", type="number", className="form-control mb-3"),
            html.Label("Alder hvor udgift ophører: "),
            dcc.Input(id=f"age-expense-end-{len(div_children)}", type="number", className="form-control mb-3")
        ])
        div_children.append(new_child)
    elif triggered_id == "remove-expense.n_clicks":
        # Remove the last expense input field
        if len(div_children) > 0:
            div_children.pop()

    return div_children

@app.callback(
    Output("income-container", "children"), 
    [Input("add-income", "n_clicks"), Input("remove-income", "n_clicks")],
    [State('income-container', 'children')]
)
def modify_income_container(add_clicks, remove_clicks, div_children):
    triggered_id = dash.callback_context.triggered[0]['prop_id']
    if triggered_id == "add-income.n_clicks":
        new_child = html.Div(children=[
            html.Label(f"Lønindtægt {len(div_children) + 1}: "),
            dcc.Input(id=f"income-name-{len(div_children)}", type="text", className="form-control mb-3", value="Beskrivende tekst (valgfri)"),
            html.Label("Beløb årligt (Før skat): "),
            dcc.Input(id=f"income-{len(div_children)}", type="number", className="form-control mb-3"),
            html.Label("Alder hvor lønindtægt starter:"),
            dcc.Input(id=f"age-income-start-{len(div_children)}", type="number", className="form-control mb-3"),
            html.Label("Alder hvor lønindtægt ophører:"),
            dcc.Input(id=f"age-income-end-{len(div_children)}", type="number", className="form-control mb-3")
        ])
        div_children.append(new_child)
    elif triggered_id == "remove-income.n_clicks":
        # Remove the last expense input field
        if len(div_children) > 0:
            div_children.pop()
    return div_children

@app.callback(
    Output('investment-chart', 'figure'),
    Output('balance-chart','figure'),
    Input('calculate-button','n_clicks'),
    #State('current-year', 'value'),
    State('current-age', 'value'),
    State('final-age', 'value'),
    State('current-investments', 'value'),
    State('expected-yield', 'value'),
    State('expected-inflation', 'value'),
    State('expenses_container', 'children'),
    State("income-container", "children")
    
)


def update_fig(calculate_button, current_age, final_age, current_investments, expected_yield, 
                   expected_inflation, expenses_container,
                   income_container):
    
    corrected_yield = expected_yield/100 - expected_inflation/100
    
    expense_list = []
    for expense in expenses_container:
        expense_data = {
            "expense": expense["props"]["children"][3]["props"]["value"],
            "age_expense_start": expense["props"]["children"][5]["props"]["value"],
            "age_expense_end": expense["props"]["children"][7]["props"]["value"]
        }
        expense_list.append(expense_data)
    
    # Calculate total expence for each year
    total_expense_list = []
    for age in range(current_age, final_age):
        total_expense = 0
        for expense in expense_list:
            if expense["age_expense_start"] <= age < expense["age_expense_end"]:
                total_expense += expense["expense"]
        total_expense_list.append(total_expense)
        
        
    
    income_list = []
    for income in income_container:
        income_data = {
            "income_before": income["props"]["children"][3]["props"]["value"],
            "age_income_start": income["props"]["children"][5]["props"]["value"],
            "age_income_end": income["props"]["children"][7]["props"]["value"]
        }
        income_list.append(income_data)
        
        
        
    # Calculate total income for each year
    total_income_before_list = []
    for age in range(current_age, final_age):
        total_income = 0
        for income in income_list:
            if income["age_income_start"] <= age < income["age_income_end"]:
                total_income += income["income_before"]
        total_income_before_list.append(total_income)
        
    #calculate total income after tax for each year
    total_income_after_list = []
    for i in  range(len(total_income_before_list)):
      if total_income_before_list[i] < 48000: #personfradrag grænse
        total_income_after_list.append(total_income_before_list[i]*0.92) #udelukkende AM-bidrag
      elif total_income_before_list[i] < 568900: #topskattegrænse
        total_income_after_list.append( 48000*0.92 + (total_income_before_list[i]-48000)*0.92*0.62)
      else:
        total_income_after_list.append( 48000*0.92 + (568900-48000)*0.92*0.62 + (total_income_before_list[i] - 568900)*0.92*0.85*0.62)

    # calculate the net of the incomes and expences for each year
    diff_list = []

    for i in range(len(total_income_after_list)):
      item = total_income_after_list[i] - total_expense_list[i]
      diff_list.append(item)


    values = [current_investments]
    ages = [current_age]
    winnings = 0
    withdrawal_list = [0]
    winnings_list = [0]
    for i in range(final_age -current_age-1):
      winnings = winnings + values[-1]*corrected_yield # totale akkumulerede afkast på investeringerne ved udgangen af året
      values.append(values[-1]*(1+corrected_yield)) # værdi af investeringer ved udgangen af året (forrige år + afkast)
      stock_tax_limit = 58900 #progressionsgrænse 2023
      frac = winnings/values[-1] # andelen af afkast i den totale værdi af porteføljen
      withdrawal_tax_limit = stock_tax_limit/frac # Det maksimale beløb man kan hæve fra investeringerne før afkastet overstiger progressionsgrænsen og man beskattes med 42% af afkastet
      disp_withdrawal_tax_limit = withdrawal_tax_limit-stock_tax_limit*0.27 #det maksimale beløb man har disponibelt hvis man vil holde sig under progressionsgrænsen.
    
    
      if diff_list[i] >= 0: #hvis differencen er et postivit tal, skal man ikke trække fra, men lægge til porteføljen.
        withdrawal = diff_list[i] #i dette tilfælde kommer man til at have en withdrawal som er positiv. ja det er lidt bagvendt
      elif 0 > diff_list[i] > -disp_withdrawal_tax_limit:
        withdrawal = diff_list[i]/ ((1-frac)+winnings*frac*0.73) # Beløbet som skal hæves fra investeringer for at dække udgifter efter skat
        winnings = winnings + withdrawal*frac #hvis man har realiseret et afkast skal dette fratrækkes summen af de akkumulerede gevinster
      else:
        withdrawal = (5*(20*diff_list[i]-3*stock_tax_limit))/(100-42*frac) #udledt i wolfram alpha diff = withdrawal*(1-frac)+stock_tax_limit*0.73 + ((withdrawal*frac)-stock_tax_limit)*0.58 solve, withdrawal
        winnings = winnings + withdrawal*frac #hvis man har realiseret et afkast skal dette fratrækkes summen af de akkumulerede gevinster
      
      #opdaterer sidste værdi i listen over beholdningen af aktiver
      
      values[-1] =  values[-2]*(1+corrected_yield) + withdrawal # differencen mellem indtægter og udgifter korrigeret for beskatning (withdrawal) tilføjes til investeringerne
    
      ages.append(ages[-1]+1)
      withdrawal_list.append(withdrawal)
      winnings_list.append(winnings)
  
    data = pd.DataFrame({'ages': ages,
                         'values': values,
                         'diff': diff_list,
                         'winnings': winnings_list,
                         'w' : withdrawal_list,
                         'total_income_after' : total_income_after_list,
                         'total_expence' : total_expense_list})
   


    investment_fig = px.line(data, x='ages', y='values', title='Beholdning af aktiver',
                             labels={'ages': 'Alder', 'values': 'Værdi'},
                  template='plotly_dark', color_discrete_sequence=['blue'])
    investment_fig.update_xaxes(tickangle=45)
    investment_fig.update_yaxes(tickprefix='kr')
    
# =============================================================================
#     balance_fig = px.line(data, x='ages', y=['total_income_after','total_expence','diff'],
#                   labels={'ages': 'Alder', 'diff': 'balance'},
#                   template='plotly_dark', color_discrete_sequence=['green','red','blue'], line_dash=['solid', 'dot', 'dash'])
#     balance_fig.update_xaxes(tickangle=45)
#     balance_fig.update_yaxes(tickprefix='kr')
#     newnames = {'diff':'Balance', 'total_income_after': 'Indtægter efter skat','total_expence' : 'Udgifter efter skat'}
#     balance_fig.for_each_trace(lambda t: t.update(name = newnames[t.name], legendgroup = newnames[t.name], hovertemplate = t.hovertemplate.replace(t.name, newnames[t.name])))
#     balance_fig.update_layout(title="Indtægter og udgifter", xaxis_title="Alder",yaxis_title="Beløb",legend_title="Forklaring")
#  
# =============================================================================
 
    newnames = {'diff':'Balance', 'total_income_after': 'Indtægter efter skat','total_expence' : 'Udgifter efter skat'}
    
    trace1 = go.Scatter(x=data['ages'], y=data['total_income_after'], name=newnames['total_income_after'], line=dict(color='green', dash='dot'))
    trace2 = go.Scatter(x=data['ages'], y=data['total_expence'], name=newnames['total_expence'], line=dict(color='red', dash='dot'))
    trace3 = go.Scatter(x=data['ages'], y=data['diff'], name=newnames['diff'], line=dict(color='blue', dash='solid'))
    trace4 = go.Scatter(x=data['ages'], y=[0]*len(data['ages']), name='Nul', line=dict(color='white', dash='solid'),showlegend=False)
    balance_fig = go.Figure([trace4,trace1, trace2, trace3])
    balance_fig.update_xaxes(tickangle=45)
    balance_fig.update_yaxes(tickprefix='kr')
    balance_fig.update_layout(title="Indtægter og udgifter", 
                              xaxis_title="Alder", 
                              yaxis_title="Beløb", 
                              legend_title="Forklaring", 
                              template='plotly_dark')
    

    return investment_fig, balance_fig             


if __name__ == '__main__':
    app.run_server( port=8051)
 