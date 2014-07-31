import sys
import urllib
import re

__author__ = 'amin'


def geturl(url):
  return urllib.urlopen(url).read()


def get_submission_table(html):
  """
  Extracts the submission table from the complete html page
  """
  #Warning the RegExp must be fixed. we are using the fact that the submission table is the last table in the html doment
  return re.search(r'<table class="status-frame-datatable">[\s\S]*</table>', html).group()


def main():
  handle = sys.argv[1:]
  if not handle:
    print 'Usage : username'
    sys.exit(1)
  return


if __name__ == '__main__':
  main()
