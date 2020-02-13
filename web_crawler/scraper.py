from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, parse_qs
from _collections import defaultdict
import string, lxml


# things to tackle: robots.txt, politeness, coming across a page you've seen before

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links]


def extract_next_links(url, resp):
    # Implementation requred.
    next_links = set()
    if resp.status in range(200, 300):
        html = resp.raw_response.content
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a'):
            if link.get('href') is not None:
                link = is_abs_url(url, link.get('href'))
                if is_valid(link) and high_value_page_tester(resp):
                    next_links.add(link)

    return next_links

# This is where most of the code is going to in terms of checking whether the URLs are valid
# ------------------------- Things to Do -------------------------
#   1. Implement some sort of timeout function --> crawler moves on if there's stalling
#   2. Detect and avoid crawler traps
#       - [] Check for path duplications (i.e. about/contact/a & about/contact/b)
#           - Need to double check implementation for this
#       - [x] Check length of URL
#       - [] Check for dynamic links
#       - [x] Check for repeating subdirectories
#       - [x] Check for anchors & calendar/dates
#       - [x] Check for URLs with more than 1 query parameters
#   3. Implement simhash to determine if pages are duplicates and if pages have low content value
#       - pages could be consider low content value if they have majority common words (?)
#       - use this algorithm to test if pages have high/low content
#       - do not download pages if page has low content
#       - find fingerprint/simhash
#   4. Implement a history base link

def is_valid(url):
    valid_domains = ["www.ics.uci.edu",
                     "www.cs.uci.edu",
                     "www.informatics.uci.edu",
                     "www.stat.uci.edu",
                     "today.uci.edu/department/information_computer_sciences"]
    try:
        parsed = urlparse(url)

        # Checks if scheme is valid
        if parsed.scheme not in set(["http", "https"]):
            return False

        # Checks if domain or if subdomain is valid
        # Need to edit and accept subdomains ie.e visions.ics.uci.edu
        domain = "(ics\.uci\.edu|cs\.uci\.edu|informatics\.uci\.edu|stat\.uci\.edu|today\.uci\.edu\/department\/information_computer_sciences)"
        if not re.search(domain, parsed.netloc):
            return False

        # cannot crawl to sites with the following in their url
        # i.e. /about/pdf/textbook.html is not a valid url
        # i.e. /about/hello/textbook.pdf is not a valid url
        extensions = "(\.)?(css|js|bmp|gif|jpe?g|ico|png|tiff?|mid|mp2|mp3|mp4|wav|avi|mov|mpeg|ram|" \
                     "m4v|mkv|ogg|ogv|pdf|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|data|dat|exe|" \
                     "bz2|tar|msi|bin|7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1|thmx|mso|arff|rtf|jar|csv|" \
                     "rm|smil|wmv|swf|wma|zip|rar|gz)"
        if re.search(extensions, parsed.path) != None:
            return False

        if re.search(extensions, parsed.netloc) != None:
            return False

        # Check if the URL has more than 1 query parameter
        if len(parse_qs(parsed.query)) > 1:
            return False

        if 'reply' in parse_qs(parsed.query):
            return False

        # Checks the len of the URL, if it has more than 250, it is not valid
        if len(url) > 250:
            return False

        # Check if URL is an anchor or a calendar
        if '#' in url or 'calendar' in url:
            return False

        # Check if the subdirectories in the path do not repeat
        path_directory = parsed.path[1:].split('/')
        if len(path_directory) != len(set(path_directory)):
            return False

        else:
            return True

    except TypeError:
        raise


def is_abs_url(base_url, found_url):
    parsed_found = urlparse(found_url)
    parsed_base = urlparse(base_url)

    if parsed_found.scheme == '' and parsed_found.netloc == '':
        missing = parsed_base.scheme + '://' + parsed_base.netloc
        found_url = missing + found_url

    elif parsed_found.scheme == '':
        missing = parsed_base.scheme + '://'
        found_url = missing + found_url


    if parsed_found.fragment != '':
        found_url = found_url.replace(('#' + parsed_found.fragment), '')

    return found_url


def high_value_page_tester(resp_object):
    stopwords = ['a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't",
                 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by',
                 "can't", 'cannot', 'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', "don't",
                 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have',
                 "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here', "here's", 'hers', 'herself', 'him',
                 'himself', 'his', 'how', "how's", 'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', "isn't",
                 'it', "it's", 'its', 'itself', "let's", 'me', 'more', 'most', "mustn't", 'my', 'myself', 'no', 'nor',
                 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours\tourselves', 'out',
                 'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's", 'should', "shouldn't", 'so',
                 'some', 'such', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves', 'then',
                 'there', "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this', 'those',
                 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll",
                 "we're", "we've", 'were', "weren't", 'what', "what's", 'when', "when's", 'where', "where's", 'which',
                 'while', 'who', "who's", 'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd",
                 "you'll", "you're", "you've", 'your', 'yours', 'yourself', 'yourselves']

    # code inspiration source: https://stackoverflow.com/questions/30565404/remove-all-style-scripts-and-html-tags-from-an-html-page/30565420

    raw_html = resp_object.raw_response.content
    soup = BeautifulSoup(raw_html, features="lxml")
    for script in soup(["script", "style"]):
        script.extract()

    lines = (line.strip() for line in soup.get_text().splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)

    original_text = [word.translate(str.maketrans('', '', string.punctuation)) for word in text.split() if
                     word in stopwords or word.isalpha()]
    filtered_text = set([word for word in original_text if word not in stopwords and word.isalpha()])
    #
    # for word in filtered_text:
    #     seen_words[word] += 1

    ratio = len(filtered_text) / len(original_text)
    if ratio > 0.25 and ratio < 0.5:
        print(ratio)
        
    return True if 0.25 < len(filtered_text) / len(original_text) < 0.5 else False



# ----------------------- Analytics Functions -------------------------------- #

# How man unique pages did we find

# Longest Page in terms of Word

def word_count(resp_object):
	raw_html = resp_object.raw_response.content

# 50 most common words but not stopwords --> compute the frequencies

# should we have a global dictonary that keeps track of all the words found
# from each page and update the dictionary every single time we find a valid
# URL
#     to get the 50 most common words, we could just sort the dict and then run
#     the for loop 50 times to get the 50 most common words
def compute_word_freq(url_text):
    stopwords = open('stopwords.txt', 'r')
    word_freq = defaultdict(int)
    regEx = '[A-Z|a-z|0-9]+'

    url_text = url_text.split()
    for word in url_text:
        if word in stopwords:
            break
        if re.match(regEx, word):
            word_freq[word] += 1
    return word_freq



# How many subdomains in ics.uci.edu domain and # of unique pages in each domain
