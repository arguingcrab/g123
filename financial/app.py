# API portion to process values in financial data for API
# Zen Lu - 2023-04
import flask
import math

from datetime import datetime
from flask import abort, json, request, Response
from werkzeug.exceptions import HTTPException
from sqlalchemy import create_engine, text

from .config import *


# flask instance and configs
app = flask.Flask(__name__)


# some constants for warnings
ERROR_MISSING_PARAM = 'error_missing_param'
ERROR_INVALID_FORMAT = 'error_invalid_format'


# Start general route(s)
@app.route('/', methods=['GET'])
def index():
    return ''


# Start of API routes
@app.route('/api/financial_data', methods=['GET'])
def get_financial_data():
    """
    Outputs financial data gathered from get_raw_daya and alphavantage
    Parameters:
        optional: symbol, start_date, end_date, limit, page
    Returns:
        data:
            - symbol
            - date
            - open_price based on earliest record per day's price
            - close_price based on latest reocrd per day's price
            - volume is sum of volume per day
        info:
            - error if there is one ("No Data")
        pagination:
            - count how many records are returned
            - limit of results per page
            - page currently on
            - pages total of results
    """
    # General variables
    data = []
    results_count = 0
    symbol_str = ''
    start_date_str = ''
    end_date_str = ''
    limit_offset_str = ''
    symbol = request.args.get('symbol')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = request.args.get('limit') or 5
    page = request.args.get('page') or 1

    # Handle date not yyyy-mm-dd
    if start_date:
        try:
            if not validate_date(start_date):
                raise ValueError
        except ValueError:
            return json.dumps({
                'data': data,
                'info': {'error': generate_param_error(
                    'start_date', ERROR_INVALID_FORMAT)}}), 400

    if end_date:
        try:
            if not validate_date(end_date):
                raise ValueError
        except ValueError:
            return json.dumps({
                'data': data,
                'info': {'error': generate_param_error(
                    'end_date', ERROR_INVALID_FORMAT)}}), 400

    # Process optional params and sql
    if symbol is not None:
        symbol_str = ' AND `symbol` = :symbol'
    if start_date is not None:
        start_date_str = ' AND `date` >= :start'
    if end_date is not None:
        end_date_str = ' AND `date` <= :end'

    # Handle non numeric limit
    if not str(limit).isdigit():
        return json.dumps({
                'data': data,
                'info': {'error': generate_param_error(
                    'limit', ERROR_INVALID_FORMAT)}}), 400

    # Calculate offset, handle non numeric page
    if not str(page).isdigit():
        return json.dumps({
                'data': data,
                'info': {'error': generate_param_error(
                    'page', ERROR_INVALID_FORMAT)}}), 400
    elif int(page) <= 1:
        offset = 0
    else:
        offset = int(limit) * (int(page) - 1)

    # Generate offset and limit sql
    limit_offset_str = ' LIMIT {0} OFFSET {1}'.format(int(limit), int(offset))
    order_by_str = ' ORDER BY `date` DESC, `symbol`'

    # Statements we need to check
    stmt = ('SELECT * FROM `{0}` '
            'WHERE 1=1 '.format(DB_TABLE)
            + symbol_str
            + start_date_str
            + end_date_str
            + order_by_str
            + limit_offset_str)

    count_stmt = ('SELECT COUNT(id) FROM `{0}` '
                  'WHERE 1=1 '.format(DB_TABLE)
                  + symbol_str
                  + start_date_str
                  + end_date_str)

    engine = create_engine(DB_CONNECT_STR)

    with engine.connect() as conn:
        # Start the db process, bind data to prevent sql injections
        results_count = conn.scalar(
            text(count_stmt),
            symbol=symbol, start=start_date, end=end_date)
        results = conn.execute(
            text(stmt),
            symbol=symbol, start=start_date, end=end_date)

        if results.rowcount == 0:
            # Data surpasses pages
            return json.dumps({
                'data': data,
                'info': {'error': 'No data'}}), 200

        for results_data in results.mappings():
            data.append({
                'symbol': results_data['symbol'],
                'date': results_data['date'],
                'open_price': results_data['open_price'],
                'close_price': results_data['close_price'],
                'volume': results_data['volume']})

    # Calculate the page total
    if int(limit) > int(results_count):
        page_count = 1
    else:
        page_count = math.ceil(int(results_count) / int(limit))

    return json.dumps({
        'data': data,
        'pagination': {
            'count': results_count,
            'page': page,
            'limit': limit,
            'pages': page_count},
        'info': {'error': ''}}, sort_keys=False), 200


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """
    Get an average of the date range of data
    Parameters:
        required: symbols, start_date, end_date
    Returns:
        - start_date
        - end_date
        - (each) symbol
        - average for open_price, end_price, volume
    """
    data = []
    symbols = request.args.get('symbols')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    avg_daily_open_price = 0
    avg_daily_close_price = 0
    avg_daily_volume = 0

    # Make sure the param are required
    if symbols is None:
        return json.dumps({
                'data': data,
                'info': {'error': generate_param_error('symbols')}}), 400
    if start_date is None:
        return json.dumps({
                'data': data,
                'info': {'error': generate_param_error('start_date')}}), 400
    if end_date is None:
        return json.dumps({
                'data': data,
                'info': {'error': generate_param_error('end_date')}}), 400

    # Handle date not yyyy-mm-dd
    if start_date:
        try:
            if not validate_date(start_date):
                raise ValueError
        except ValueError:
            return json.dumps({
                'data': data,
                'info': {'error': generate_param_error(
                    'start_date', ERROR_INVALID_FORMAT)}}), 400

    if end_date:
        try:
            if not validate_date(end_date):
                raise ValueError
        except ValueError:
            return json.dumps({
                'data': data,
                'info': {'error': generate_param_error(
                    'end_date', ERROR_INVALID_FORMAT)}}), 400

    # Split the symbols into comma separated strings for db
    symbols = tuple(symbols.split(','))

    # Db statements
    stmt = f"""
        SELECT symbol,
        AVG(open_price) as "avg_open_price",
        AVG(close_price) as "avg_close_price",
        AVG(volume) as "avg_volume"
        FROM financial_data
        WHERE `symbol` IN :symbols
        AND `date` BETWEEN :start AND :end
        GROUP BY `symbol`
        ORDER BY `symbol`
        """

    engine = create_engine(DB_CONNECT_STR)

    with engine.connect() as conn:
        # Start the query and bind values to prevent sql injection
        results = conn.execute(
            text(stmt),
            symbols=tuple(symbols),
            start=start_date,
            end=end_date)

        # No results for query
        if results.rowcount == 0:
            return json.dumps({
                'data': data,
                'info': {'error': 'No data'}}), 200

        # Use sql's avg function and process data
        for results_data in results.mappings():
            data.append({
                'start_date': start_date,
                'end_date': end_date,
                'symbol': results_data['symbol'],
                'average_daily_open_price': round(results_data['avg_open_price'], 2),
                'average_daily_close_price': round(results_data['avg_close_price'], 2),
                'average_daily_volume': round(results_data['avg_volume'], 2), })

    return json.dumps({
        'data': data,
        'info': {'error': ''}}, sort_keys=False), 200


def generate_param_error(field, msg_type=ERROR_MISSING_PARAM):
    """
    Generate message for missing param
    """
    if msg_type == ERROR_MISSING_PARAM:
        msg = "'{0}' is required but not found in the parameter".format(field)
    elif msg_type == ERROR_INVALID_FORMAT:
        msg = "'{0}' format is invalid".format(field)
    return msg


@app.errorhandler(HTTPException)
def handle_exception(e):
    """
    Handle api errors
    Also can be used with abort(...)
    """
    response = e.get_response()
    response.data = json.dumps({
        'code': e.code,
        'name': e.name,
        'description': e.description,
    })

    response.content_type = 'application/json'
    return response


def validate_date(date_value, format='%Y-%m-%d'):
    return date_value == datetime.strptime(date_value, format).strftime(format)
