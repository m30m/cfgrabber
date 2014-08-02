#!/usr/bin/python -tt
import sys
import urllib
import re
import HTMLParser
import os
import codecs
import thread
import time
from BeautifulSoup import BeautifulSoup
import mechanize

__author__ = 'Mohammad Amin Khashkhashi Moghaddam'

class CFBrowser:
  def __init__(self):
    self.br = mechanize.Browser()
    self.br.set_handle_refresh(False)
    self.br.addheaders = [('User-agent', 'Firefox')]
  def login(self,handle,password):
    self.br.open('http://codeforces.com/enter')
    self.br.form = list(self.br.forms())[1]
    self.br['handle']=handle
    self.br['password']=password
    self.br.submit()
  def get_url(self,url):
    return self.br.open(url).read().decode('utf-8')


class Submission:
  """
  Stores all the data about a submission
  """
  parser = HTMLParser.HTMLParser()
  #langs is a dict with each language mapping to a pair with file format and comment format
  langs = {
    r'C\+\+': ('.cpp', u'//'),
    r'Java': ('.java', u'//'),
    r'Python': ('.py', u'#'),
    r'': ('.unknown', u'//')
  }
  #TODO:fix this TOF with threading
  active = 0

  def __init__(self, rowdom):
    """
    Given the Row DOM Extracting all the information about the submission
    """
    self.id = int(rowdom['data-submission-id'])
    cells = rowdom.findAll('td')
    self.lang = cells[4].getText()
    for item in Submission.langs.items():
      if re.search(item[0], self.lang):
        (self.file_format, self.comment_format) = item[1]
    self.verdict = cells[5].span['submissionverdict']
    self.time = cells[6].getText()
    self.memory = cells[7].getText()
    self.problem_link = cells[3].a['href']
    self.isgym = self.problem_link.find('gym') != -1
    (self.contest_id, self.problem_id) = re.search(r'/problemset/\w+/(\d+)/(\w+)', self.problem_link).groups()
    self.contest_id = int(self.contest_id)
    self.name = Submission.parser.unescape(cells[3].getText())
    return

  def get_source(self):
    """
    Downloads the sourcecode
    """
    if hasattr(self, 'source_code'):
      return self.source_code
    if self.isgym:
      print "Can't get Gym submissions"
      return
    else:
      source_url = 'http://codeforces.com/contest/%d/submission/%d' % (self.contest_id, self.id)
    Submission.active += 1
    html = get_url(source_url)
    start_tag = '<pre class="prettyprint" style="padding:0.5em;">'
    end_tag = '</pre>'
    p1 = html.find(start_tag) + len(start_tag)
    p2 = html.find(end_tag, p1)
    # self.source_code = Submission.parser.unescape(BeautifulSoup(html).findAll(attrs={'class':'prettyprint'})[0].getText())
    self.source_code = Submission.parser.unescape(html[p1:p2])
    Submission.active -= 1
    return self.source_code

  def get_source_with_stats(self):
    """
    Add some information to the top of source code
    """
    header = self.comment_format + u'Problem Name : %s\n' % self.name
    header += self.comment_format + u'Execution Time : %s\n' % self.time
    header += self.comment_format + u'Memory : %s\n' % self.memory
    return header + self.get_source()


def get_submissions_url(handle, page):
  return 'http://codeforces.com/submissions/%s/page/%d' % (handle, page)


def get_lastpage_num(html):
  """
  Finds out what how many submission pages the user have
  """
  return max([int(num) for num in re.findall(r'/submissions/.*/page/(\d+)', html)])


def get_submissionpage(url, num, subpages):
  print 'Downloading Submission Page #%d' % num
  subpages.append((num, get_url(url)))


def get_submission_table(html):
  """
  Extracts the submission table from the complete html page so BeautifulSoup would only parse the table to improve speed
  """
  start_tag = '<table class="status-frame-datatable">'
  end_tag = '</table>'
  p1 = html.find(start_tag)
  p2 = html.find(end_tag, p1) + len(end_tag)
  return html[p1:p2]


def get_submissions(handle):
  """
  Returns all the submission the user has
  """
  pagenum = 1
  submissions = []
  url = get_submissions_url(handle, pagenum)
  lastpage = get_lastpage_num(get_url(url))
  subpages = []
  for i in range(1, lastpage + 1):
    thread.start_new_thread(get_submissionpage, (get_submissions_url(handle, i), i, subpages,))
  while len(subpages) != lastpage:
    time.sleep(0.1)
  for page in sorted(subpages):
    print 'Parsing the submissions from page #%d' % page[0]
    html = page[1]
    #soup = BeautifulSoup(html)
    #table = soup.findAll(attrs={'class':'status-frame-datatable'})[0]
    table = BeautifulSoup(get_submission_table(html))
    table_rows = table.findAll('tr')[1:]  #first row is just the headers and useless
    for row in table_rows:
      submissions.append(Submission(row))
  return submissions


def store_submission(submission, dir=''):
  dir = os.path.join(dir, 'contests/%d/' % submission.contest_id)
  if not os.path.exists(dir):
    os.makedirs(dir)
  dir += submission.problem_id
  format = submission.file_format
  if os.path.exists(dir + format):
    num = 2
    dir += '_'
    while os.path.exists(dir + str(num) + format):
      num += 1
    dir += str(num)

  data = submission.get_source_with_stats()
  try:
    data.encode('ascii')
    fh = open(dir + format, 'w')
  except UnicodeEncodeError:
    fh = codecs.open(dir + format, 'w', 'utf-8')
  fh.write(data)
  fh.close()



def main():
  if len(sys.argv) < 2:
    print 'Usage : username [directory]'
    sys.exit(1)
  handle = sys.argv[1]
  path = ''
  if len(sys.argv) > 2:
    path = sys.argv[2]
  subs = get_submissions(handle)
  ok_subs = [sub for sub in subs if sub.verdict == 'OK' and not sub.isgym]
  for sub in ok_subs:
    while Submission.active > 80:
      time.sleep(0.1)
    print "Downloading Submission #%d for question : %s " % (sub.id, sub.name)
    thread.start_new_thread(sub.get_source, ())
  while Submission.active:
    time.sleep(0.1)
  for sub in ok_subs:
    print "Saving Submission #%d for question : %s " % (sub.id, sub.name)
    store_submission(sub, dir=path)
  return


if __name__ == '__main__':
  main()
