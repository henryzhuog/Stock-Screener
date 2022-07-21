import requests
import bs4
from bs4 import BeautifulSoup
from lxml import html
import pandas as pd

# Given a string 'element', returns it as a number (e.g. 14.3B --> 14300000000)
def to_number(element):
	if element == '-':
		return 0
	if len(element) == 1:
		return int(element)
	prefix = float(element[0:-1])
	suffix =  element[-1]
	if suffix.isalpha():
		match suffix:
			case 'K':
				return prefix * 1000
			case 'M':
				return prefix * 1000000
			case 'B':
				return prefix * 1000000000
			case 'T':
				return prefix * 1000000000000

stock = input('Enter a stock ticker: ').lower()
print()

# Market Cap (total value) & Name
response = requests.get('https://www.marketwatch.com/investing/stock/' + stock + '?mod=mw_quote_tab')
doc = html.fromstring(response.content)
soup = BeautifulSoup(response.text, 'lxml')
company_name = soup.find('h1', {"class": "company__name"}).contents[0]
market_cap = doc.xpath('//small[.="Market Cap"]/following-sibling::span/text()')[0]

# Valuation
value_page = requests.get('https://www.marketwatch.com/investing/stock/' + stock + '/company-profile?mod=mw_quote_tab')
value_doc = html.fromstring(value_page.content)
pe = value_doc.xpath('//td[.="P/E Ratio (w/ extraordinary items)"]/following-sibling::td/text()')[0]
pcf = value_doc.xpath('//td[.="Price to Cash Flow Ratio"]/following-sibling::td/text()')[0]
ps = value_doc.xpath('//td[.="Price to Sales Ratio"]/following-sibling::td/text()')[0]
pb = value_doc.xpath('//td[.="Price to Book Ratio"]/following-sibling::td/text()')[0]

# Financial Health
cr = value_doc.xpath('//td[.="Current Ratio"]/following-sibling::td/text()')[0]
qr = value_doc.xpath('//td[.="Quick Ratio"]/following-sibling::td/text()')[0]

# Profitability
om = value_doc.xpath('//td[.="Operating Margin"]/following-sibling::td/text()')[0]
nm = value_doc.xpath('//td[.="Net Margin"]/following-sibling::td/text()')[0]
roa = value_doc.xpath('//td[.="Return on Assets"]/following-sibling::td/text()')[0]
roe = value_doc.xpath('//td[.="Return on Equity"]/following-sibling::td/text()')[0]
roic = value_doc.xpath('//td[.="Return on Invested Capital"]/following-sibling::td/text()')[0]

# Free Cash Flow
fin_table_source = pd.read_html('https://www.marketwatch.com/investing/stock/' + stock + '/financials/cash-flow')
fin_df = fin_table_source[6]
fcf = fin_df.loc[22].iat[5] # for most recent year
fcf = to_number(fcf)

# Debt Information
balance_sheet = pd.read_html('https://www.marketwatch.com/investing/stock/' + stock + '/financials/balance-sheet')
debt_df = balance_sheet[5]
short_term_debt = debt_df.loc[1].iat[5]
short_term_debt = to_number(short_term_debt)
long_term_debt = debt_df.loc[11].iat[5]
long_term_debt = to_number(long_term_debt)
total_debt = short_term_debt + long_term_debt
debt_to_fcf = total_debt/fcf

# Useful for DCF calculation
income_statement = pd.read_html('https://www.marketwatch.com/investing/stock/' + stock + '/financials?mod=mw_quote_tab')
income_table = income_statement[4]
shares_outstanding = income_table.loc[50].iat[5]
shares_outstanding = to_number(shares_outstanding)

print('Company Name: ' + company_name + '\n')
print('--- Valuation Metrics ---')
print('Market Cap: ' + market_cap)
print('P/E: ' + pe)
print('P/CF: ' + pcf)
print('P/S: ' + ps)
print('P/B: ' + pb)
print()
print('--- Financial Health ---')
print('Current Ratio: ' + cr)
print('Quick Ratio: ' + qr)
print('Debt/FCF:', round(debt_to_fcf, 2))
print()
print('--- Profitability ---')
print('Operating Margin: ' + om)
print('Net Margin: ' + nm)
print('Return on Assets: ' + roa)
print('Return on Equity: ' + roe)
print('Return on Invested Capital: ' + roic)
print()

if input('Do you want to perform a DCF analysis? (y/n) ').lower() == 'y':
	required_rate = float(input('Enter your required rate of return (%): '))/100
	pg_rate = float(input('Enter your perpetual growth rate (%): '))/100
	fcf_growth_rate = float(input('Enter your FCF growth rate (%): '))/100

	years = [1, 2, 3, 4, 5] # 5 years is an appropriate timeframe

	future_fcf = []
	discount_factor = []
	discounted_future_fcf = []

	terminal_value = fcf * (1 + pg_rate)/(required_rate - pg_rate)
	
	for year in years:
		cash_flow = fcf * (1 + fcf_growth_rate)**year
		future_fcf.append(cash_flow)
		discount_factor.append((1 + required_rate)**year)
		discounted_future_fcf.append(future_fcf[year - 1]/discount_factor[year - 1])

	discounted_terminal_value = terminal_value / (1 + required_rate)**5
	discounted_future_fcf.append(discounted_terminal_value)
	present_value = sum(discounted_future_fcf)
	fair_value = present_value/shares_outstanding

	print()
	print('Fair value of ' + stock.upper() + ': $', round(fair_value, 2), sep = '')