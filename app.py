import dash
from dash import dcc
from dash import html
from datetime import datetime as dt
import yfinance as yf
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
# model
from model import prediction
from sklearn.svm import SVR
import requests




def get_stock_price_fig(df):
    
# Create a candlestick chart
    fig = go.Figure(data=[go.Candlestick(x=df.Date,
                                     open=df['Open'],
                                     high=df['High'],
                                     low=df['Low'],
                                     close=df['Close'])])

# Set the plot title and labels
    fig.update_layout(title=' Stock Price Chart',
                  xaxis_title='Date',
                  yaxis_title='Price',
                  plot_bgcolor='white',
                  paper_bgcolor='white',
                  )

    return fig


def get_more(df):
            
# Calculate the indicators
    df['SMA_20'] = df['Close'].rolling(window=20).mean()  # Simple Moving Average
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()  # Exponential Moving Average
    df['Bollinger_Band_Upper'] = df['Close'].rolling(window=20).mean() + 2*df['Close'].rolling(window=20).std()  # Bollinger Band Upper
    df['Bollinger_Band_Lower'] = df['Close'].rolling(window=20).mean() - 2*df['Close'].rolling(window=20).std()  # Bollinger Band Lower

# Create a figure with multiple subplots
    fig = go.Figure(data=[go.Scatter(x=df['Date'], y=df['Close'], name='Close Price')])

# Add the indicators
    fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA_20'], name='SMA 20'))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['EMA_20'], name='EMA 20'))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Bollinger_Band_Upper'], name='Bollinger Band Upper'))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Bollinger_Band_Lower'], name='Bollinger Band Lower'))

# Set the layout
    fig.update_layout(title='Stock Price with Indicators',
                  xaxis_title='Date',
                  yaxis_title='Price',
                  legend_title='Legend',plot_bgcolor='white',
                  paper_bgcolor='white')

    return fig


app = dash.Dash(
    __name__,
    external_stylesheets=[
        "https://codepen.io/dhananjay16449/pen/GRampGJ"
    ])
server = app.server
# html layout of site
app.layout = html.Div(
    [
        html.Div(
            [
                # Navigation
                html.P("Visualization of stocks!!!", className="start"),
                html.Div([
                    html.P("Input stock code: "),
                    html.Div([
                        dcc.Input(id="dropdown_tickers", type="text"),
                        html.Button("Submit", id='submit'),
                    ],
                             className="form")
                ],
                         className="input-place"),
                html.Div([
                    dcc.DatePickerRange(id='my-date-picker-range',
                                        min_date_allowed=dt(1995, 8, 5),
                                        max_date_allowed=dt.now(),
                                        initial_visible_month=dt.now(),
                                        end_date=dt.now().date()),
                ],
                         className="date"),
                html.Div([
                    html.Button(
                        "Stock Price", className="stock-btn", id="stock",n_clicks=0),
                    html.Button("Indicators",
                                className="indicators-btn",
                                id="indicators"),
                    dcc.Input(id="n_days",
                              type="text",
                              placeholder="number of days"),
                    html.Button(
                        "Forecast", className="forecast-btn", id="forecast")
                ],
                         className="buttons"),
                # here
            ],
            className="nav"),

        # content
        html.Div(
            [
                html.Div(
                    [  # header
                        html.Img(id="logo"),
                        html.P(id="ticker")
                    ],
                    className="header"),
                html.Div(id="description", className="decription_ticker"),
                html.Div([], id="graphs-content"),
                html.Div([], id="main-content"),
                html.Div([], id="forecast-content")
            ],
            className="content"),
    ],
    className="container")
# callback for company info
@app.callback([
    Output("description", "children"),
    Output("logo", "src"),
    Output("ticker", "children"),
    Output("stock", "n_clicks"),
    Output("indicators", "n_clicks"),
    Output("forecast", "n_clicks")
], [Input("submit", "n_clicks")], [State("dropdown_tickers", "value")])


def update_data(n, val):
    if n == None:
        return "Hey there! Please enter a legitimate stock code to get details.", None, None, None, None,None
    else:
        if val == None:
            raise PreventUpdate
        else:
            ticker = yf.Ticker(val)
            inf = ticker.info
            logo_url = None
            if 'logo_url' in inf:
                logo_url = inf['logo_url']
            else:
                domain = inf['website'].split('//')[-1].split('/')[0]
                response = requests.get(f'https://logo.clearbit.com/{domain}')
                if response.status_code == 200:
                    logo_url = response.url
            return inf['longBusinessSummary'], inf['shortName'], dcc.Markdown(children=f"![Company Logo]({logo_url})"), None, None, None


# callback for stocks graphs
@app.callback([
    Output("graphs-content", "children"),
], [
    Input("stock", "n_clicks"),
    Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date')
], [State("dropdown_tickers", "value")])
def stock_price(n, start_date, end_date, val):
    if n == None:
        return [""]
        #raise PreventUpdate
    if val == None:
        raise PreventUpdate
    else:
        if start_date != None:
            df = yf.download(val, str(start_date), str(end_date))
        else:
            df = yf.download(val)

    df.reset_index(inplace=True)
    fig = get_stock_price_fig(df)
    return [dcc.Graph(figure=fig)]


# callback for indicators
@app.callback([Output("main-content", "children")], [
    Input("indicators", "n_clicks"),
    Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date')
], [State("dropdown_tickers", "value")])
def indicators(n, start_date, end_date, val):
    if n == None:
        return [""]
    if val == None:
        return [""]

    if start_date == None:
        df_more = yf.download(val)
    else:
        df_more = yf.download(val, str(start_date), str(end_date))

    df_more.reset_index(inplace=True)
    fig = get_more(df_more)
    return [dcc.Graph(figure=fig)]


# callback for forecast
@app.callback([Output("forecast-content", "children")],
              [Input("forecast", "n_clicks")],
              [State("n_days", "value"),
               State("dropdown_tickers", "value")])
def forecast(n, n_days, val):
    if n == None:
        return [""]
    if val == None:
        raise PreventUpdate
    fig = prediction(val, int(n_days) + 1)
    return [dcc.Graph(figure=fig)]

if __name__ == '__main__':
   app.run_server(debug=True)
  