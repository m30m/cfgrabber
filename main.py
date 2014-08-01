import sys
import urllib
import re
import HTMLParser
from xml.dom import minidom

__author__ = 'amin'


def get_url(url):
  return urllib.urlopen(url).read()


class Submission:
  parser = HTMLParser.HTMLParser()
  def __init__(self, rowdom):
    """
    Given the Row DOM Extracting all the information about the submission
    """
    self.id = int(rowdom.attributes['data-submission-id'].value)
    cells = rowdom.getElementsByTagName('td')
    name = cells[3].getElementsByTagName('a')[0]
    self.lang = re.search(r'\S.*',cells[4].childNodes[0].wholeText).group()
    self.verdict = re.search(r'submissionVerdict="(\w+)"',cells[5].toxml()).group(1)
    self.time = re.search(r'\d+ ms',cells[6].toxml()).group()
    self.memory= re.search(r'\d+ KB',cells[7].toxml()).group()
    self.problem_link = name.attributes['href'].value
    self.isgym = self.problem_link.find('gym') != -1
    (self.contest_id, self.problem_id) = re.search(r'/problemset/\w+/(\d+)/(\w+)', self.problem_link).groups()
    self.contest_id = int(self.contest_id)
    self.name = name.childNodes[0].toxml()
    return

  def get_source(self):
    if self.isgym:
      source_url = 'http://codeforces.com/gym/%d/submission/%d' % (self.contest_id, self.id)
    else:
      source_url = 'http://codeforces.com/contest/%d/submission/%d' % (self.contest_id, self.id)
    html = get_url(source_url)
    start_tag = '<pre class="prettyprint" style="padding:0.5em;">'
    end_tag = '</pre>'
    p1=html.find(start_tag)+len(start_tag)
    p2=html.find(end_tag,p1)
    return Submission.parser.unescape(html[p1:p2])


def get_submission_table(html):
  """
  Extracts the submission table from the complete html page because the whole page XML is not well-formed
  """
  #Warning the RegExp must be fixed. we are using the fact that the submission table is the last table in the html document
  #TODO: just remove the RegExp and do it with simple finding and stuff
  return re.search(r'<table class="status-frame-datatable">[\s\S]*</table>', html).group()


def get_submissions_url(handle, page):
  return 'http://codeforces.com/submissions/%s/page/%d' % (handle, page)


def have_next(html):
  return html.find(r'<span class="inactive">&rarr;</span>')==-1


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
