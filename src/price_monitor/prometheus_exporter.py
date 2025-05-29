from prometheus_client import start_http_server, Gauge

start_http_server(8000)

PRICE_GAUGE = Gauge('token_price', 'Token price by pair', ['pair_name'])
DEVIATION_GAUGE = Gauge('price_deviation_pct', 'Price deviation % between pairs', ['pair'])