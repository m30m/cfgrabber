#!/usr/bin/python -tt
import sys
import urllib
import re
import HTMLParser
import os
import codecs
from xml.dom import minidom

__author__ = 'amin'


def get_url(url):
  return urllib.urlopen(url).read().decode('utf-8')


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
    self.name = re.search(r'\S.*',name.childNodes[0].wholeText).group()
    return

  def get_source(self):
    if hasattr(self,'source_code'):
      return self.source_code
    if self.isgym:
      print "Can't get Gym submissions"
      return
    else:
      source_url = 'http://codeforces.com/contest/%d/submission/%d' % (self.contest_id, self.id)
    html = get_url(source_url)
    start_tag = '<pre class="prettyprint" style="padding:0.5em;">'
    end_tag = '</pre>'
    p1=html.find(start_tag)+len(start_tag)
    p2=html.find(end_tag,p1)
    self.source_code = Submission.parser.unescape(html[p1:p2])
    return self.source_code

  def get_source_with_stats(self):
    if self.lang.find('C++')!=-1 or self.lang.find('Java')!=-1:
      comment_str=u'//'
    else:
      comment_str=u'#'
    header = comment_str + u'Problem Name : %s\n' % self.name
    header += comment_str + u'Execution Time : %s\n' % self.time
    header += comment_str + u'Memory : %s\n' % self.memory
    return header+self.get_source()




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

def store_submission(submission,dir=''):
  dir=os.path.join(dir,'contests/%d/' % submission.contest_id)
  if not os.path.exists(dir):
    os.makedirs(dir)
  dir+=submission.problem_id
  if submission.lang.find('C++')!=-1:
    format='.cpp'
  elif submission.lang.find('Java')!=-1:
    format='.java'
  else:
    format='.py'
  if os.path.exists(dir+format):
    num=2
    dir+='_'
    while os.path.exists(dir+str(num)+format):
      num+=1
    dir+=str(num)

  data=submission.get_source_with_stats()
  try:
    data.encode('ascii')
    fh = open(dir+format,'w')
  except UnicodeEncodeError:
    fh = codecs.open(dir+format,'w','utf-8')
  fh.write(data)
  fh.close()



def main():
  if len(sys.argv)<2:
    print 'Usage : username [directory]'
    sys.exit(1)
  handle = sys.argv[1]
  path =''
  if len(sys.argv)>2:
    path=sys.argv[2]
  subs = get_submissions(handle)
  for sub in subs:
    if sub.verdict=='OK' and not sub.isgym:
      print "Storing Submission #%d for question : %s " % (sub.id, sub.name)
      store_submission(sub,dir=path)
  return


if __name__ == '__main__':
  main()
