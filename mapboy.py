import pandas as pd
import urllib.request
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
import argparse
import sys
from colorama import Fore, init
from datetime import datetime


class sitemap:

	def __init__(self):
		init(autoreset=True)
		self.self = self
		self.collection = pd.DataFrame()
		self.paths = ['sitemap.xml',
		              'sitemap.xml.gz',
		              'sitemap_index.xml',
		              'sitemap-index.xml',
		              'sitemap_index.xml.gz',
		              'sitemap-index.xml.gz',
		              '.sitemap.xml',
		              'sitemap',
		              'admin/config/search/xmlsitemap',
		              'sitemap/sitemap-index.xml',
		              'sitemap_news.xml',
		              'sitemap-news.xml',
		              'sitemap_news.xml.gz',
		              'sitemap-news.xml.gz']

	def iterator(self, url):
		if url[-1] == '/':
			url = url[:-1]
		for smp in self.paths:
			sitemapurl = f'{url}/{smp}'
			self.parse(sitemapurl)

	def parse(self, url):
		print(f'Checking: {url}...', end='\r')
		r = requests.get(url)
		replacetokens = ['</sitemap>', '<sitemap>', '<loc>', '</loc>']
		if r.status_code == 200:
			print(Fore.GREEN + f'{url} Found! Extracting...')
			sitemapxml = r.text
			# sitemapxml = r.text.replace("\r\n", "").strip()
			for s in sitemapxml.splitlines():
				if 'xmlns' not in s and 'xsi:' not in s and 'www.sitemaps' not in s:
					if 'http' in s:
						for rt in replacetokens:
							s = s.replace(rt, '')
						result = pd.DataFrame({'Extractor': "sitemap.xml", 'Sitemap': url, 'ExtractedUrl': s.strip()}, index=[0])
						self.collection = pd.concat([self.collection, result])

		else:
			print(Fore.YELLOW + f'{url} Not found! Skipping...')

	def export(self, outputfile):
		outputfile = outputfile.replace('.csv', '')
		self.collection.to_csv(f'{outputfile}_{datetime.now().strftime("%Y%m%d-%I%M%S")}.csv', encoding='utf-8', index=False)


class robots:
	def __init__(self):
		self.self = self
		self.paths = ['robots.txt']
		self.collection = pd.DataFrame()

	def parse(self, url):

		r = requests.get(f'{url}/robots.txt')
		sendrequest = r.text
		if r.status_code == 200:
			print(Fore.GREEN + f'{url}/robots.txt Found! Extracting...')
			split = sendrequest.splitlines(True)
			useragent = ''
			for s in split:
				s = s.replace('\r\n', '')
				original = s
				permission = str()
				robopath = str()
				if 'USER-AGENT' in s[:10].upper():
					z = s[:10]
					useragent = s.replace(z + ': ', '')
					permission = ''
					robopath = ''
				if 'DISALLOW' in s[:8].upper():
					z = s[:8]
					permission = 'Disallow'
					robopath = s.replace(z + ': ', '')
				if 'SITEMAP' in s[:8].upper():
					z = s[:7]
					permission = 'Disallow'
					robopath = s.replace(z + ': ', '')
				if 'ALLOW' in s[:5].upper():
					z = s[:5]
					permission = 'Allow'
					robopath = s.replace(z + ': ', '')
				try:
					if robopath[0] == '/':
						robopath = url + robopath
				except:
					pass
				result = pd.DataFrame({'Extractor': "robots.txt", 'UserAgent': useragent, 'Permission': permission, 'Original': original, 'ExtractedUrl': robopath}, index=[0])
				self.collection = pd.concat([self.collection, result])
		if r.status_code != 200:
			print(Fore.RED + f'{url}/robots.txt not found')

	def export(self, outputfile):
		outputfile = outputfile.replace('.csv', '')
		self.collection.to_csv(f'{outputfile}-robots.csv', encoding='utf-8', index=False)


def main():
	args = parse_args()
	url = args.url if args.url is not None else input('Scan URL : ')
	print(Fore.LIGHTWHITE_EX + '-------------------------------------------------------------------------------')
	r = args.robots
	s = args.sitemap
	output = args.output
	output = output.replace('.csv', '')

	if url[-1] == '/':
		url = url[:-1]
	if s is False and r is True:
		robot = robots()
		robot.parse(url)
		robot.export(output)
		pass

	if r is False and s is True:
		sitemaps = sitemap()
		sitemaps.parse(url)
		sitemaps.export(output)
		pass

	if s is False and r is False:
		robot = robots()
		robot.parse(url)
		sitemaps = sitemap()
		sitemaps.iterator(url)
		combinedfile = pd.concat([robot.collection, sitemaps.collection])
		combinedfile.to_csv(f'{output}.csv', encoding='utf-8', index=False)
		for index, row in combinedfile.iterrows():
			if r"*" in row['ExtractedUrl']:
				with open('wildcards.txt', 'a') as f:
					f.write(row['ExtractedUrl'].replace(f'{url}/', '') + '\n')


def parser_error(errmsg):
	print("Usage: python " + sys.argv[0] + " [Options] use -h for help")
	print("Error: " + errmsg)
	sys.exit()


def parse_args():
	# parse the arguments
	parser = argparse.ArgumentParser(epilog='\tExample: \r\npython ' + sys.argv[0] + " -d google.com -p basicscan")
	parser.error = parser_error
	parser._optionals.title = "OPTIONS"
	parser.add_argument('-u', '--url', help="URL to extract information from", required=False)
	parser.add_argument('-o', '--output', help="File you would like to output to", required=False, default='mapboy.csv')
	parser.add_argument('-r', '--robots', help="Only scan for robots.txt files", required=False, default=False, action='store_true')
	parser.add_argument('-s', '--sitemap', help="Only scan for sitemap xml", required=False, default=False, action='store_true')
	return parser.parse_args()


def splash():
	mapboytitle = f'''
{Fore.LIGHTMAGENTA_EX}                                          {Fore.LIGHTWHITE_EX}88                                   
{Fore.LIGHTMAGENTA_EX}                                          {Fore.LIGHTWHITE_EX}88                                   
{Fore.LIGHTMAGENTA_EX}                                          {Fore.LIGHTWHITE_EX}88                                   
{Fore.LIGHTMAGENTA_EX}88,dPYba,,adPYba,  ,adPPYYba, 8b,dPPYba,  {Fore.LIGHTWHITE_EX}88,dPPYba,   ,adPPYba,  8b       d8  
{Fore.LIGHTMAGENTA_EX}88P'   "88"    "8a ""     `Y8 88P'    "8a {Fore.LIGHTWHITE_EX}88P'    "8a a8"     "8a `8b     d8'  
{Fore.LIGHTMAGENTA_EX}88      88      88 ,adPPPPP88 88       d8 {Fore.LIGHTWHITE_EX}88       d8 8b       d8  `8b   d8'   
{Fore.LIGHTMAGENTA_EX}88      88      88 88,    ,88 88b,   ,a8" {Fore.LIGHTWHITE_EX}88b,   ,a8" "8a,   ,a8"   `8b,d8'    
{Fore.LIGHTMAGENTA_EX}88      88      88 `"8bbdP"Y8 88`YbbdP"'  {Fore.LIGHTWHITE_EX}8Y"Ybbd8"'   `"YbbdP"'      Y88'     
{Fore.LIGHTMAGENTA_EX}                              88          {Fore.LIGHTWHITE_EX}                            d8'      
{Fore.LIGHTMAGENTA_EX}                              88          {Fore.LIGHTWHITE_EX}                           d8'       '''
	print(mapboytitle)
	print(Fore.LIGHTYELLOW_EX + '                                                         build 1.0.0 march 2022')
	print(Fore.LIGHTWHITE_EX + '-------------------------------------------------------------------------------')


if __name__ == '__main__':
	init(autoreset=True)
	splash()
	main()
