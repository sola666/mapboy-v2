import pandas as pd
import urllib.request
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
import argparse
import sys
from colorama import Fore, init
from datetime import datetime
import asyncio
import aiohttp
import gzip
import io
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

# Configure logging
logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
CONCURRENT_REQUESTS = 5
BACKOFF_FACTOR = 0.3

class RetryableSession:
	@staticmethod
	def get_session():
		session = requests.Session()
		retry_strategy = Retry(
			total=MAX_RETRIES,
			backoff_factor=BACKOFF_FACTOR,
			status_forcelist=[429, 500, 502, 503, 504],
		)
		adapter = HTTPAdapter(max_retries=retry_strategy)
		session.mount("http://", adapter)
		session.mount("https://", adapter)
		return session

class sitemap:
	def __init__(self):
		init(autoreset=True)
		self.self = self
		self.collection = pd.DataFrame()
		self.session = RetryableSession.get_session()
		self.semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
		self.console_lock = asyncio.Lock()  # Add lock for console output
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

	async def iterator(self, url: str) -> None:
		if url[-1] == '/':
			url = url[:-1]
		
		tasks = []
		for smp in self.paths:
			sitemapurl = f'{url}/{smp}'
			tasks.append(self.parse(sitemapurl))
		
		await asyncio.gather(*tasks)

	async def parse(self, url: str) -> None:
		async with self.semaphore:
			try:
				async with self.console_lock:
					print(f'Checking: {url}')
				async with aiohttp.ClientSession() as session:
					async with session.get(url, timeout=DEFAULT_TIMEOUT) as response:
						if response.status == 200:
							async with self.console_lock:
								print(Fore.GREEN + f'Found: {url} - Extracting...')
							
							content_type = response.headers.get('Content-Type', '')
							if 'gzip' in content_type or url.endswith('.gz'):
								# Handle gzipped content
								compressed_data = await response.read()
								with gzip.GzipFile(fileobj=io.BytesIO(compressed_data)) as gz:
									sitemapxml = gz.read().decode('utf-8')
							else:
								sitemapxml = await response.text()

							await self._process_sitemap_content(sitemapxml, url)
						else:
							async with self.console_lock:
								print(Fore.YELLOW + f'{url} Not found! (Status: {response.status}) Skipping...')
							
			except asyncio.TimeoutError:
				logger.error(f"Timeout while fetching {url}")
			except aiohttp.ClientError as e:
				logger.error(f"Network error while fetching {url}: {str(e)}")
			except Exception as e:
				logger.error(f"Unexpected error while processing {url}: {str(e)}")

	async def _process_sitemap_content(self, content: str, url: str) -> None:
		replacetokens = ['</sitemap>', '<sitemap>', '<loc>', '</loc>']
		try:
			for s in content.splitlines():
				if 'xmlns' not in s and 'xsi:' not in s and 'www.sitemaps' not in s:
					if 'http' in s:
						for rt in replacetokens:
							s = s.replace(rt, '')
						result = pd.DataFrame({
							'Extractor': "sitemap.xml",
							'Sitemap': url,
							'ExtractedUrl': s.strip()
						}, index=[0])
						self.collection = pd.concat([self.collection, result])
		except Exception as e:
			logger.error(f"Error processing sitemap content from {url}: {str(e)}")

	def export(self, outputfile: str) -> None:
		try:
			outputfile = outputfile.replace('.csv', '')
			output_path = f'{outputfile}_{datetime.now().strftime("%Y%m%d-%I%M%S")}.csv'
			self.collection.to_csv(output_path, encoding='utf-8', index=False)
			logger.info(f"Successfully exported data to {output_path}")
		except Exception as e:
			logger.error(f"Error exporting data: {str(e)}")

class robots:
	def __init__(self):
		self.self = self
		self.paths = ['robots.txt']
		self.collection = pd.DataFrame()
		self.session = RetryableSession.get_session()
		self.console_lock = asyncio.Lock()  # Add lock for console output

	async def parse(self, url: str) -> None:
		try:
			robots_url = f'{url}/robots.txt'
			async with self.console_lock:
				print(f'Checking: {robots_url}')
			async with aiohttp.ClientSession() as session:
				async with session.get(robots_url, timeout=DEFAULT_TIMEOUT) as response:
					if response.status == 200:
						async with self.console_lock:
							print(Fore.GREEN + f'Found: {robots_url} - Extracting...')
						content = await response.text()
						await self._process_robots_content(content, url)
					else:
						async with self.console_lock:
							print(Fore.RED + f'Not found: {robots_url} (Status: {response.status})')
		except asyncio.TimeoutError:
			logger.error(f"Timeout while fetching {robots_url}")
		except aiohttp.ClientError as e:
			logger.error(f"Network error while fetching {robots_url}: {str(e)}")
		except Exception as e:
			logger.error(f"Unexpected error while processing {robots_url}: {str(e)}")

	async def _process_robots_content(self, content: str, url: str) -> None:
		try:
			split = content.splitlines()
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
					if robopath and robopath[0] == '/':
						robopath = url + robopath
				except IndexError:
					continue

				result = pd.DataFrame({
					'Extractor': "robots.txt",
					'UserAgent': useragent,
					'Permission': permission,
					'Original': original,
					'ExtractedUrl': robopath
				}, index=[0])
				self.collection = pd.concat([self.collection, result])
		except Exception as e:
			logger.error(f"Error processing robots.txt content from {url}: {str(e)}")

	def export(self, outputfile: str) -> None:
		try:
			outputfile = outputfile.replace('.csv', '')
			output_path = f'{outputfile}-robots.csv'
			self.collection.to_csv(output_path, encoding='utf-8', index=False)
			logger.info(f"Successfully exported robots.txt data to {output_path}")
		except Exception as e:
			logger.error(f"Error exporting robots.txt data: {str(e)}")

async def async_main(args):
	url = args.url if args.url is not None else input('Scan URL : ')
	print(Fore.LIGHTWHITE_EX + '-------------------------------------------------------------------------------')
	r = args.robots
	s = args.sitemap
	output = args.output
	output = output.replace('.csv', '')

	if url[-1] == '/':
		url = url[:-1]

	try:
		if s is False and r is True:
			robot = robots()
			await robot.parse(url)
			robot.export(output)

		elif r is False and s is True:
			sitemaps = sitemap()
			await sitemaps.iterator(url)
			sitemaps.export(output)

		else:
			robot = robots()
			sitemaps = sitemap()
			
			# Run both operations concurrently
			await asyncio.gather(
				robot.parse(url),
				sitemaps.iterator(url)
			)
			
			try:
				combinedfile = pd.concat([robot.collection, sitemaps.collection])
				combinedfile.to_csv(f'{output}.csv', encoding='utf-8', index=False)
				
				# Process wildcards
				wildcards = combinedfile[combinedfile['ExtractedUrl'].str.contains(r'\*', na=False)]
				if not wildcards.empty:
					with open('wildcards.txt', 'w') as f:
						for url_path in wildcards['ExtractedUrl']:
							f.write(url_path.replace(f'{url}/', '') + '\n')
			except Exception as e:
				logger.error(f"Error combining and saving results: {str(e)}")
				
	except Exception as e:
		logger.error(f"Error in main execution: {str(e)}")
		sys.exit(1)

def parser_error(errmsg):
	print("Usage: python " + sys.argv[0] + " [Options] use -h for help")
	print("Error: " + errmsg)
	sys.exit()

def parse_args():
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
	print(Fore.LIGHTYELLOW_EX + '                                                         v2.0.0 march 2025')
	print(Fore.LIGHTWHITE_EX + '-------------------------------------------------------------------------------')

if __name__ == '__main__':
	init(autoreset=True)
	splash()
	args = parse_args()
	asyncio.run(async_main(args))
