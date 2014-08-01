import sys
import urllib
import re
from xml.dom import minidom

__author__ = 'amin'


class Submission:
  def __init__(self, rowdom):
    """
    Given the Row DOM Extracting all the information about the submission
    """
    self.id = int(rowdom.attributes['data-submission-id'].value)
    cells = rowdom.getElementsByTagName('td')
    name = cells[3].getElementsByTagName('a')[0]
    #TODO:parse these cells doms so it will be something useful
    self.lang = cells[4]
    self.verdict = cells[5]
    self.time = cells[6]
    self.memory = cells[7]
    self.problem_link = name.attributes['href'].value
    (self.contest_id, self.problem_id) = re.search(r'/problemset/problem/(\d+)/(\w+)', self.problem_link).groups()
    self.name = name.childNodes[0].toxml()
    return


def get_url(url):
  return urllib.urlopen(url).read()


def get_submission_table(html):
  """
  Extracts the submission table from the complete html page because the whole page XML is not well-formed
  """
  #Warning the RegExp must be fixed. we are using the fact that the submission table is the last table in the html document
  return re.search(r'<table class="status-frame-datatable">[\s\S]*</table>', html).group()


def get_submissions_url(handle, page):
  return 'http://codeforces.com/submissions/%s/page/%d' % (handle, page)


def have_next(html):
  return not re.search(r'<span class="inactive">&rarr;</span>', html)


def get_submissions(handle):
  pagenum = 1
  submissions = []
  url = get_submissions_url(handle, pagenum)
  while url:
    print 'Getting the submissions from page #%d' % pagenum
    html = get_url(url)
    table = get_submission_table(html)
    table = minidom.parseString(table)
    table_rows = table.getElementsByTagName('tr')[1:]  #first row is just the headers and useless
    for row in table_rows:
      submissions.append(Submission(row))
    if have_next(html):
      pagenum += 1
      url = get_submissions_url(handle, pagenum)
    else:
      break
  return submissions


def main():
  handle = sys.argv[1:]
  if not handle:
    print 'Usage : username'
    sys.exit(1)
  subs = get_submissions(handle)
  for sub in subs:
    print "Submission #%d for question : %s " % (sub.id, sub.name)
  return


if __name__ == '__main__':
  main()
