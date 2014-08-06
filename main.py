#!/usr/bin/python2.7 -tt
import re
import HTMLParser
import os
import codecs
import thread
import time
import getpass
from BeautifulSoup import BeautifulSoup
from optparse import OptionParser
import mechanize

__author__ = 'Mohammad Amin Khashkhashi Moghaddam'

class CFBrowser:
  def __init__(self):
    self.br = mechanize.Browser()
    self.br.set_handle_refresh(False)
    self.br.set_handle_robots(False)
    self.br.addheaders = [('User-agent', 'Firefox')]
  def login(self,handle,password):
    #TODO:Check whether the password is correct or not
    self.br.open('http://codeforces.com/enter')
    self.br.form = list(self.br.forms())[1]
    self.br['handle']=handle
    self.br['password']=password
    self.br.submit()
  def get_url(self,url):
    tries = 0
    while tries < 10:
      try:
        return self.br.open(url).read().decode('utf-8')
      except:
        time.sleep(0.25)
        tries+=1
    print "Sorry Couldn't get the url : %s" % url


cf = CFBrowser()

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
    source_url = 'http://codeforces.com/%s/%d/submission/%d' % ('gym' if self.isgym else 'contest',self.contest_id, self.id)
    print "Downloading Submission #%d for question : %s " % (self.id, self.name)
    #print "the url is : %s" % source_url
    Submission.active += 1
    html = cf.get_url(source_url)
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
  subpages.append((num, cf.get_url(url)))


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
  lastpage = get_lastpage_num(cf.get_url(url))
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
  print "Saving Submission #%d for question : %s " % (submission.id, submission.name)
  dir = os.path.join(dir, '%s/%d/' % ('gym' if submission.isgym else 'contests', submission.contest_id))
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
    fh = open(dir + format, 'wb')
  except UnicodeEncodeError:
    fh = codecs.open(dir + format, 'wb', 'utf-8')
  fh.write(data)
  fh.close()



def main():
  parser = OptionParser(usage='Usage: %prog --username HANDLE [options]')
  parser.add_option('-u','--username',dest='handle',help='User handle in codeforces site')
  parser.add_option('-g','--gym',action='store_true',dest='storegym',help='Store gym submissions too',default=False)
  parser.add_option('-p','--path',dest='path',help='Directory to store the submissions',default='')
  (options,args) = parser.parse_args()
  if not options.handle:
    parser.error('User handle is missing use --help for more information')
  subs = get_submissions(options.handle)
  if options.storegym:
    print 'To Store gym submission you have to enter password'
    pw = getpass.getpass()
    cf.login(options.handle,pw)
  ok_subs = [sub for sub in subs if sub.verdict == 'OK' and (not sub.isgym or options.storegym)]
  for sub in ok_subs:
    while Submission.active > 80:
      time.sleep(0.1)
    thread.start_new_thread(sub.get_source, ())
  while Submission.active:
    time.sleep(0.1)
  for sub in ok_subs:
    store_submission(sub, dir=options.path)
  return


if __name__ == '__main__':
  main()
