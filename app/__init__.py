from datetime import datetime
import pandas as pd
from flask import Flask, render_template, request
import requests

import app.stats_model as model

app = Flask(__name__)


def valet_api_wrapper(ticker, start_date: datetime, end_date: datetime):
    """
    Calls Valet API with the specified ticker(s), start date and end date, to return ready-to-work-with Pandas
    dataframe or series

    :param ticker: either a string, or a list of strings i.e. 'FXUSDCAD', or ['FXUSDCAD', 'AVG.INTWO']
    :param start_date: datetime start date
    :param end_date: datetime   end date
    :return:
    """
    if isinstance(ticker, str):
        ticker = [ticker]

    # prepare url to make request
    VALET_API_BASE_URL = 'https://www.bankofcanada.ca/valet/observations'
    ticker_parsed = ",".join(ticker)
    start_date_parsed = datetime.strftime(start_date, '%Y-%m-%d')
    end_date_parsed = datetime.strftime(end_date, '%Y-%m-%d')
    request_url = f'{VALET_API_BASE_URL}/{ticker_parsed}?start_date={start_date_parsed}&end_date={end_date_parsed}'
    resp = requests.get(url=request_url).json()

    # convert to Pandas DataFrame (if more than one ticker) or Series for easy use
    observations = resp['observations']
    rearranged_dict = {}
    for observation in observations:
        date = observation['d']
        del observation['d']  # we want to iterate through the dictionary to get ticker values without the date
        rearranged_dict[date] = {ticker: float(value['v']) for ticker, value in observation.items()}
    df = pd.DataFrame.from_dict(rearranged_dict, orient='index')  # dates are rows, tickers are columns
    return df


def validate_date_range(start_date, end_date):
    """
    Check to ensure start date < end date < now, and that the dates are valid

    :param start_date:
    :param end_date:
    :return:
    """
    error_msg = ''

    # check that the start date is not empty
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    except:
        error_msg += 'Please input a start date.'

    # check that the end date is not empty
    try:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    except:
        if len(error_msg) > 0:
            error_msg += ' Also input an end date.'
        else:
            error_msg += 'Please input an end date.'

    if len(error_msg) > 0:
        return error_msg

    # check that start date < end date < now
    if start_date > end_date:
        error_msg += 'Please ensure that the start date is earlier than the end date.'
    if start_date > datetime.now():
        if len(error_msg) > 0:
            error_msg += ' Also ensure the start date is before today.'
        else:
            error_msg += 'Please ensure that the start date is before today.'
    if end_date > datetime.now():
        if len(error_msg) > 0:
            error_msg += ' Also ensure the end date is before today.'
        else:
            error_msg += 'Please ensure that the end date is before today.'

    return error_msg


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/compute_stats', methods=['GET'])
def get_correlation_usdcad_corra():
    try:
        # get start and end dates from request
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # checking that the start date < end date < today and not empty
        error_msg = validate_date_range(start_date=start_date, end_date=end_date)
        if len(error_msg) > 0:
            return render_template('index.html', error=error_msg)

        df = valet_api_wrapper(ticker=['FXUSDCAD', 'AVG.INTWO'],
                               start_date=datetime.strptime(start_date, '%Y-%m-%d'),
                               end_date=datetime.strptime(end_date, '%Y-%m-%d'))
        corra, usd_cad = df['AVG.INTWO'], df['FXUSDCAD']
        try:
            pearsonr = model.pearson_correlation(ts1=usd_cad, ts2=corra)
        except ZeroDivisionError:
            error_msg = 'A division by zero has occurred when computing the Pearson Correlation Coefficient. ' \
                        'Please ensure that you have selected a date range that is wide enough.'
            return render_template('index.html', error=error_msg)

        usd_cad_basic_stats = model.describe_series_stats(timeseries=usd_cad)
        corra_basic_stats = model.describe_series_stats(timeseries=corra)
        stats_df = pd.DataFrame.from_dict({'USD/CAD': usd_cad_basic_stats, 'CORRA': corra_basic_stats}, orient='index')
        return render_template('index.html', basic_stats_df=pd.DataFrame.to_html(stats_df),
                               pearsonr=pearsonr, show_result=True, start_date=start_date, end_date=end_date)
    except:
        return render_template('index.html',
                               error='An unidentified error has been caught. Please contact the Quantitative '
                                     'Engineering team for more support')
