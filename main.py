# -*- coding: utf-8 -*-
# Module:  default
# Author:  Pete Arnold.
# Date:    9.10.2016
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys
from urlparse import parse_qsl
import xbmcgui
import xbmcplugin

import requests;
from collections import defaultdict

# import time;

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

"""
# The videos data structure for the example code.
SOURCES = {'programme name': 
            [
              {'name': 'episode name',
               'thumb': 'image url',
               'link': 'episode page url',
               'video': 'video url',
               'genre': 'S4C'},
              {'name': 'episode name',
               'thumb': 'image url',
               'link': 'episode page url',
               'video': 'video url',
               'genre': 'S4C'}
            ],
          'programme name':
            [
              {'name': 'episode name',
               'thumb': 'image url',
               'link': 'episode page url',
               'video': 'video url',
               'genre': 'S4C'},
              {'name': 'episode name',
               'thumb': 'image url',
               'link': 'episode page url',
               'video': 'video url',
               'genre': 'S4C'}
            ]
         }
#
"""

# The list of programmes and the episodes available. We fill this up in two
# stages so as not to do too much unnecessary work. Firstly we get the list of
# all the programmes available on S4C click but with not episode video data.
# When the user selects a programme on the Kodi menu, we go and find videos for
# episodes of that programme only.
SOURCES = defaultdict(list);
# pageCount = 0;
# start = time.time();

# Part 1: The S4C website scrape.
# ------------------------------------------------------------------------------

# S4C A-Z search URL. Set l to an empty string to search for everything.
programURL = 'http://www.s4c.cymru/clic/c_a2z.shtml?l=';

def alreadyHaveVideo(name, url) :
    # Return True if there is a programme with 'name' which has a video with the
    # specified URL.
    for video in SOURCES[name] :
        if video['link'] == url :
            return True;
    return False;

def getVideo(URL, getEpisodes) :
    # Get the video episode from the programme page which also lists programme
    # pages for any additional episodes for this programme.
    # global pageCount;
    global SOURCES;
    # print (b'Getting video ' + URL + b'...');
    page = requests.get(URL);
    # pageCount += 1;
    length = len(page.content);
    pos = 0;
    # Find the video: <section class="playerSection" ... >.
    index = page.content.find(b'playerSection', pos, length);
    if (index < 0) :
        return;
    # Get the thumbnail image: in the playerSection style="...".
    start = page.content.find(b'background-image:url(', index, length) + 21;
    end = page.content.find(b')', start, length);
    if ((start < 0) or (end < 0)) :
        thumb = b'';
    else :
        thumb = page.content[start: end];
    # Get the programme name: in the following <h1>.
    start = page.content.find(b'<h1>', index, length) + 8;
    if (start < 0) :
        return;
    end = page.content.find(b'<span', start, length);
    if (end < 0) :
        return;
    name = page.content[start: end].lstrip().rstrip();
    # Get the programme tag-line: in the <span> in the <h1> although this may
    # be empty.
    start = page.content.find(b'>', end, length) + 1;
    end = page.content.find(b'</span>', start, length);
    if ((start < 0) or (end < 0)) :
        tag = b'';
    else :
        tag = page.content[start: end].lstrip().rstrip();
    # Get the video URL: find <video> tag, then its <source> tag and then that's
    # src parameter.
    start = page.content.find(b'<video', end, length);
    if (start < 0) :
        return;
    start = page.content.find(b'<source', start, length);
    if (start < 0) :
        return;
    start = page.content.find(b'src="', start, length) + 5;
    if (start < 0) :
        return;
    end = page.content.find(b'"', start, length);
    if (end < 0) :
        return;
    url = page.content[start: end];
    # Get an alternative tag if the tag-line is empty: get the broadcast date
    # from the following data <li>.
    if (tag == b''):
        start = page.content.find(b'class="aired"', end, length);
        start = page.content.find(b'</span>', start, length) + 7;
        end = page.content.find(b'</li>', start, length);
        if ((start < 0) or (end < 0)) :
            tag = b'';
        else :
            tag = page.content[start: end].lstrip().rstrip();
    pos = index + 1;
    # Add the video to the list.
    # print (b'   Added video episode ' + tag);
    SOURCES[name].append({'name': tag, 'thumb': thumb, 'link': URL, 'video': url, 'genre': 'S4C'});
    # Now look for more episodes. If there are any, they'll be in a section
    # 'moreEpisodes'.
    if (getEpisodes) :
        index = page.content.find(b'moreEpisodes', pos, length);
        if (index < 0) :
            return;
        while (pos < length) :
            index = page.content.find(b'featureInfo', pos, length);
            if (index < 0) :
                break;
            # Get the programme URL.
            start = page.content.rfind(b'href="', 0, index) + 6;
            if (start < 0) :
                break;
            end = page.content.find(b'"', start, length);
            if (end < 0) :
                break;
            # The URL provided on the more episodes is relative to the clic
            # website.
            url = b'http://www.s4c.cymru/clic/' + page.content[start: end];
            # Get the programme name.
            start = page.content.find(b'</span>', index, length) + 8;
            if (start < 0) :
                break;
            end = page.content.find(b'<span', start, length);
            if (end < 0) :
                break;
            # Check that the name is the same as the sought programme; if not,
            # we have probably just skipped into the section listing other
            # programmes that might be of interest.
            anotherName = page.content[start: end].lstrip().rstrip();
            if (name != anotherName) :
                # print (b'   Not another episode: probably a link to a different programme (' + anotherName + b'), breaking...');
                break;
            # If the episode page URL is not in the list of episodes already
            # found, go and get the video data, otherwise, ignore it, we already
            # have it from the more episodes of a previous episode.
            if not alreadyHaveVideo(name, url) :
            #    # print (b'   Already have the URL for this video in the list (' + name + b'), breaking...');
            #else :
            #    # print (b'   Getting video ' + name + b'...');
                getVideo(url, False);
            pos = index + 1;

def getProgrammes(URL, getEpisodes, programme) :
    # Get the programmes from the page where they are listed by the search URL.
    # global pageCount;
    global SOURCES;
    if (len(SOURCES)) < 1 :
        # The page will be an S4C A-Z page which will have one link for each
        # programme.
        # print ('Getting programme ' + URL + '...');
        page = requests.get(URL);
        # pageCount += 1;
        length = len(page.content);
        pos = 0;
        while (pos < length) :
            # Find the programme data: <div class="featureInfo">.
            index = page.content.find(b'featureInfo', pos, length);
            if (index < 0) :
                break;
            # Get the programme URL: back-up to the preceding href.
            start = page.content.rfind(b'href="', 0, index) + 6;
            if (start < 0) :
                break;
            end = page.content.find(b'"', start, length);
            if (end < 0) :
                break;
            url = page.content[start: end];
            # Get the programme name: after the icon </span>.
            start = page.content.find(b'</span>', index, length) + 8;
            if (start < 0) :
                break;
            end = page.content.find(b'<span', start, length);
            if (end < 0) :
                break;
            name = page.content[start: end].lstrip().rstrip();
            # If we want to get episodes and the name of this programme matches
            # the specified name, get the episodes from the programme url.
            # Otherwise just add an empty video source so that the programme
            # appears on the video menu.
            if ((getEpisodes == True) and (name == programme)) :                
                # print ('\nProgramme: %s at %s, getting video ...)' % (name, url));
                getVideo(url, getEpisodes);
            else :
                SOURCES[name].append({'name': '', 'thumb': '', 'link': '', 'video': url, 'genre': 'S4C'});
            pos = index + 1;

def makeList(programme) :
    # Append the search character to the S4C A-Z search URL.
    # A-Z are just that (except that double letters are <double>&nm=<first>.
    # 0-9 are all '0-9' and anything else is '-'.
    # If the programme name is empty just get a list of programmes. If the name
    # is specified, get a list of programmes starting with the same letter (that
    # is the only search available, but then only get episodes for any
    # programme that has the same name.
    if (len(programme) > 0) :
        search = programme[0].lower();
        if ((search >= '0') and (search <= '9')) :
            search = '0-9';
        elif ((search < 'a') or (search > 'z')) :
            search = '-';
        # Handle Welsh double letters.
        double = programme[0:1].lower();
        if ((double == 'ch') or (double == 'ff') or (double == 'ng') or
            (double == 'll') or (double == 'ph') or (double == 'rh') or
            (double == 'th')) :
            search = double + '&nm=' + search;            
        getProgrammes(programURL + search, True, programme);
    else :
        getProgrammes(programURL, False, '');
    """
    end = time.time();
    print ('Extracted data from ' + str(pageCount) + ' pages in ' + str(end - start) + 's.');

    for category in SOURCES.keys() :
        print (category);
        for video in SOURCES[category] :
            print (b'   ' + video['name']);
        
    # print (SOURCES);
    """

# Part 2 : The video selection menus (as per Roman_VM's video add-on sample).
# ------------------------------------------------------------------------------

def get_categories():
    return SOURCES.keys()

def get_videos(category):
    return SOURCES[category]

def list_categories():
    # Get video categories
    categories = get_categories()
    xbmc.log('Found ' + str(len(categories)) + ' categories.');
    # Create a list for our items.
    listing = []
    # Iterate through categories
    for category in categories:
        xbmc.log('Adding category ' + category);
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=category)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({'thumb': SOURCES[category][0]['thumb'],
                          'icon': SOURCES[category][0]['thumb'],
                          'fanart': SOURCES[category][0]['thumb']})
        # Set additional info for the list item.
        # Here we use a category name for both properties for for simplicity's sake.
        # setInfo allows to set various information for an item.
        # For available properties see the following link:
        # http://mirrors.xbmc.org/docs/python-docs/15.x-isengard/xbmcgui.html#ListItem-setInfo
        list_item.setInfo('video', {'title': category, 'genre': category})
        # Create a URL for the plugin recursive callback.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = '{0}?action=listing&category={1}'.format(_url, category)
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the listing as a 3-element tuple.
        listing.append((url, list_item, is_folder))
    # Add our listing to Kodi.
    # Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
    # instead of adding one by one via addDirectoryItem.
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def list_videos(category):
    # Get the list of videos in the category.
    videos = get_videos(category)
    xbmc.log('Found ' + str(len(videos)) + ' videos for ' + category + '.');
    # Create a list for our items.
    listing = []
    # Iterate through videos.
    for video in videos:
        xbmc.log('Adding video ' + video['name']);
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=video['name'])
        # Set additional info for the list item.
        list_item.setInfo('video', {'title': video['name'], 'genre': video['genre']})
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({'thumb': video['thumb'], 'icon': video['thumb'], 'fanart': video['thumb']})
        # Set 'IsPlayable' property to 'true'.
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')
        # Create a URL for the plugin recursive callback.
        # Example: plugin://plugin.video.example/?action=play&video=http://www.vidsplay.com/vids/crab.mp4
        url = '{0}?action=play&video={1}'.format(_url, video['video'])
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = False
        # Add our item to the listing as a 3-element tuple.
        listing.append((url, list_item, is_folder))
    # Add our listing to Kodi.
    # Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
    # instead of adding one by ove via addDirectoryItem.
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def play_video(path):
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=path)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)
  
def router(paramstring):
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'listing':
            # Display the list of episodes for the specified programme.
            makeList(params['category']);
            list_videos(params['category'])
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['video'])
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of programmes.
        makeList('');
        list_categories()

if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
  