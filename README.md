# mapboy

                                                    88                                   
                                                    88                                   
                                                    88                                   
          88,dPYba,,adPYba,  ,adPPYYba, 8b,dPPYba,  88,dPPYba,   ,adPPYba,  8b       d8   
          88P'   "88"    "8a ""     `Y8 88P'    "8a 88P'    "8a a8"     "8a `8b     d8'  
          88      88      88 ,adPPPPP88 88       d8 88       d8 8b       d8  `8b   d8'   
          88      88      88 88,    ,88 88b,   ,a8" 88b,   ,a8" "8a,   ,a8"   `8b,d8'    
          88      88      88 `"8bbdP"Y8 88`YbbdP"'  8Y"Ybbd8"'   `"YbbdP"'      Y88'     
                                        88                                      d8'      
                                        88                                     d8'      
  
------------------------------------------------------------------------------------------------------
**Build 1.0.0 - March 2022**
This tool was designed to extract URLs & domain information from a websites robots.txt and sitemap.xml files.

------------------------------------------------------------------------------------------------------
**TO DO:**
------------------------------------------------------------------------------------------------------

- Read settings from config file
------------------------------------------------------------------------------------------------------
**USAGE:**
------------------------------------------------------------------------------------------------------
This can be executed from your Python IDE, or from the command line.   
**Supported robots.txt patterns:**  
- */robots.txt  

**Supported sitemap.xml patterns:**  
- */sitemap.xml  
- */sitemap.xml.gz  
- */sitemap_index.xml  
- */sitemap-index.xml  
- */sitemap_index.xml.gz  
- */sitemap-index.xml.gz  
- */.sitemap.xml  
- */sitemap  
- */admin/config/search/xmlsitemap  
- */sitemap/sitemap-index.xml  
- */sitemap_news.xml  
- */sitemap-news.xml  
- */sitemap_news.xml.gz  
- */sitemap-news.xml.gz  
  
  
When run from the IDE, it will prompt the user for a domain name - and then go scan it. The output will default to */mapboy_yyyymmdd-hhmmss.csv  
  
When run from the command line, the below parameters can be parsed.  
  
------------------------------------------------------------------------------------------------------
**PARAMETERS:**
------------------------------------------------------------------------------------------------------
**-u --url**
The URL that you would like to scan.

**-o --output**
The name of the file you would like to output to. Currently only supports .CSV

**-r --robots**
Default FALSE - Passing this arg indicates that you only intend to scan the robots.txt file. Sitemaps will **NOT** be scanned.

**-s --sitemap**
Default FALSE - Passing this arg indicates that you only intend to scan the sitemap.xml files. Robots.txt will **NOT** be scanned.

