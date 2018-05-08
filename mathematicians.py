from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import click
from multiprocessing.dummy import Pool


def simple_get(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the text content or return none.
    :param url: address of the website to use with GET
    :return:
        Text: If response is HTML/XML
        None: Otherwise
    """

    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        log_error("Error during requests to {0} : {1}".format(url, str(e)))


def is_good_response(resp):
    """
    Checks if response is HTML/XML
    :param resp: response received by GET
    :return:
        True: If response if HTML
        False: Otherwise
    """
    print(resp)
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1
            )


def log_error(e):
    """
    Stores log errors
    :param e: the error message to be stored
    :return: None
    """
    print(e)


def process_raw_html(resp):
    """
    Using BeautifulSoup, converts raw_html to html
    :param resp: raw_html data
    :return: raw html file converted to html
    """
    return BeautifulSoup(resp, "html.parser")


def get_names(html):
    """
    extracts names from the html passed
    :param html: website html from where to parse
    :return: names: list of mathematicians
    """
    names = set()
    for li in html.select('li'):
        for name in li.text.split('\n'):
            if len(name) > 0:
                names.add(name.strip())

    return list(names)


def display_names(names):
    """
    Displays name from a list of name of mathematicians
    :param names: list containing name of mathematicians
    :return: None
    """
    for name in names:
        print(name)


def get_hits(name):
    """
    Accepts a mathematician's name and returns the hits of his wikipedia page
    in the last 60 days.
    :param name:
    :return:
        hits: if hit_count is greater than zero
        int(0): if hit_count is 0
    """
    url_root = 'https://xtools.wmflabs.org/articleinfo/en.wikipedia.org/{}'
    html_response = process_raw_html(simple_get(url_root.format(name)))

    hit_link = [a for a in html_response.select('a')
                if a['href'].find('latest-60') > -1
                ]

    if len(hit_link) > 0:
        link_text = hit_link[0].text.replace(',', '')  # strip commas

        try:
            return int(link_text)
        except TypeError:
            log_error("couldn't parse {} as an `int`".format(link_text))

    else:
        log_error("No page-views found for {mathematician}".format(mathematician=name))
        return int(0)


def add_hits(name_list):
    """
    create list with name and hits value
    :param name_list: list of mathematicians
    :return: list of (names, hit_count)
    """
    top_names = []

    def append_hit(name):
        print("here")
        top_names.append((name, get_hits(name)))

    pool = Pool(25)  # in tests 25 was the highest supported number of simultaneous processes
    pool.map(append_hit, name_list)
    pool.close()
    pool.join()

    return top_names


@click.command()
@click.option('--url', "-u", default="http://www.fabpedigree.com/james/mathmen.htm",
              help="URL from where the mathematicians list is fetched")
def main(url):
    """
    A simple script that displays top ten mathematicians fetched from the URL provided
    :param url: URL from where the list of mathematicians is ot be fetched
    """
    raw_response = simple_get(url)
    html_response = process_raw_html(raw_response)
    name_list = get_names(html_response)
    results = add_hits(name_list)
    results = sorted(results, key=lambda x: x[1], reverse=True)
    for i, name in enumerate(results):
        if i >= 10:
            break
        print("{position} -> {mathematician} has {hit_count} hits".format(position=(i+1), mathematician=name[0],
                                                                          hit_count=name[1]))


if __name__ == '__main__':
    main()
