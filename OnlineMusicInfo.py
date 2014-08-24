import xbmcaddon, os, xbmc, xbmcvfs, time, sys
if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson
from Utils import *
import urllib

bandsintown_apikey = 'xbmc_open_source_media_center'
lastfm_apikey = '6c14e451cd2d480d503374ff8c8f4e2b'
googlemaps_key_old = 'AIzaSyBESfDvQgWtWLkNiOYXdrA9aU-2hv_eprY'
Addon_Data_Path = os.path.join( xbmc.translatePath("special://profile/addon_data/%s" % xbmcaddon.Addon().getAddonInfo('id') ).decode("utf-8") )

def HandleBandsInTownResult(results):
    events = []
    for event in results:
        try:
            venue = event['venue']
            artists = event['artists']
            my_arts = ''
            for art in artists:
                my_arts += ' / '
                my_arts += art['name']
            my_arts = my_arts.replace(" / ", "",1)        
            event = {'date': event['datetime'].replace("T", " - ").replace(":00", "",1),
                     'city': venue['city'],
                     'name': venue['name'],
                     'region': venue['region'],
                     'country': venue['country'],
                     'artists': my_arts  }
            events.append(event)
        except: pass
    return events

def cleanText(text):
    import re
    text = re.sub('<br \/>','[CR]',text)
    text = re.sub('<(.|\n|\r)*?>','',text)
    text = re.sub('&quot;','"',text)
    text = re.sub('&amp;','&',text)
    text = re.sub('&gt;','>',text)
    text = re.sub('&lt;','<',text)
    text = re.sub('User-contributed text is available under the Creative Commons By-SA License and may also be available under the GNU FDL.','',text)
    return text.strip()    
    
def HandleLastFMEventResult(results):
    events = []
    if "events" in results and results['events'].get("event"):
        for event in results['events']['event']:
            artists = event['artists']['artist']
            if isinstance(artists, list):
                my_arts = ' / '.join(artists)
            else:
                my_arts = artists
            lat = ""
            lon = ""               
            if event['venue']['location']['geo:point']['geo:long']:
                lon = event['venue']['location']['geo:point']['geo:long']
                lat = event['venue']['location']['geo:point']['geo:lat']
                search_string = ""
            elif event['venue']['location']['street']:
                search_string = event['venue']['location']['city'] + " " + event['venue']['location']['street']
            elif event['venue']['location']['city']:
                search_string = event['venue']['location']['city'] + " " + event['venue']['name']               
            else:
                search_string = event['venue']['name']
            googlemap = 'http://maps.googleapis.com/maps/api/staticmap?&sensor=false&scale=2&maptype=roadmap&center=%s&zoom=13&markers=%s&size=640x640&key=%s' % (search_string, search_string, googlemaps_key_old)
            event = {'date': event['startDate'],
                     'name': event['venue']['name'],
                     'id': event['venue']['id'],
                     'street': event['venue']['location']['street'],
                     'eventname': event['title'],
                     'website': event['website'],
                     'description': cleanText(event['description']),
                    # 'description': event['description'], ticket missing
                 #    'city': event['venue']['location']['postalcode'] + " " + event['venue']['location']['city'],
                     'city': event['venue']['location']['city'],
                     'country': event['venue']['location']['country'],
                     'geolong': event['venue']['location']['geo:point']['geo:long'],
                     'geolat': event['venue']['location']['geo:point']['geo:lat'],
                     'artists': my_arts,
                     'googlemap': googlemap,
                     'artist_image': event['image'][-1]['#text'],
                     'venue_image': event['venue']['image'][-1]['#text'],
                     'headliner': event['artists']['headliner']  }
            events.append(event)
    else:
        log("Error when handling LastFM results")
    return events
       
def HandleLastFMAlbumResult(results):
    albums = []
    log("starting HandleLastFMAlbumResult")
    try:
        for album in results['topalbums']['album']:
            album = {'artist': album['artist']['name'],
                     'mbid': album['mbid'],
                     'thumb': album['image'][-1]['#text'],
                     'name':album['name']  }
            albums.append(album)
    except:
        log("Error when handling LastFM results")
    return albums
           
def HandleLastFMShoutResult(results):
    shouts = []
    log("starting HandleLastFMShoutResult")
    try:
        for shout in results['shouts']['shout']:
            newshout = {'comment': shout['body'],
                        'author': shout['author'],
                        'date':shout['date'][4:]  }
            shouts.append(newshout)
    except:
        log("Error when handling LastFM Shout results")
    return shouts
           
def HandleLastFMArtistResult(results):
    artists = []
    log("starting HandleLastFMArtistResult")
    try:
        for artist in results['artist']:
            if 'name' in artist:
                artist = {'Title': artist['name'],
                          'name': artist['name'],
                          'mbid': artist['mbid'],
                          'Thumb': artist['image'][-1]['#text'],
                          'Listeners':artist.get('listeners',"")  }
                artists.append(artist)
    except:
        log("Error when handling LastFM TopArtists results")
    return artists
    
def GetEvents(id, pastevents = False):
    if pastevents:
        url = 'method=artist.getpastevents&mbid=%s' % (id)
    else:
        url = 'method=artist.getevents&mbid=%s' % (id)
    results = GetLastFMData(url)
    try:
        return HandleLastFMEventResult(results)
    except:
        log("Error in GetEvents()")
        return []

def GetLastFMData(url = "", cache_days = 14):
    from base64 import b64encode
    filename = b64encode(url).replace("/","XXXX")
    path = Addon_Data_Path + "/" + filename + ".txt"
    log("trying to load "  + path)
    if xbmcvfs.exists(path) and ((time.time() - os.path.getmtime(path)) < (cache_days * 86400)):
        return read_from_file(path)
    else:
        url = 'http://ws.audioscrobbler.com/2.0/?api_key=%s&format=json&%s' % (lastfm_apikey, url)
        response = GetStringFromUrl(url)
        results = simplejson.loads(response)
        save_to_file(results,filename,Addon_Data_Path)
        return results
                      
def GetTopArtists():
    results = GetLastFMData("method=chart.getTopArtists&limit=100")
    try:
        return HandleLastFMArtistResult(results['artists'])
    except Exception,e:
        log(e)
        log("Error when finding artist top-tracks from" + url)
        return []
    
def GetShouts(artistname, albumtitle):
    url = 'method=album.getshouts&artist=%s&album=%s' % (urllib.quote_plus(artistname),urllib.quote_plus(albumtitle))
    results = GetLastFMData(url)
    try:
        return HandleLastFMShoutResult(results)
    except Exception,e:
        log(e)
        log("Error when finding shouts from" + url)
        return []
    
def GetArtistTopAlbums(mbid):
    url = 'method=artist.gettopalbums&mbid=%s' % (mbid)
    results = GetLastFMData(url)
    try:
        return HandleLastFMAlbumResult(results)
    except Exception,e:
        log(e)
        log("Error when finding topalbums from" + url)
        return []
        
def GetSimilarById(m_id):
    url = 'method=artist.getsimilar&mbid=%s&limit=400' % (m_id)
    results = GetLastFMData(url)
    try:
        return HandleLastFMArtistResult(results['similarartists'])
    except Exception,e:
        log(e)
        log("Error when finding SimilarById from" + url)
        return []
        
def GetNearEvents(tag = False,festivalsonly = False, lat = "", lon = ""):
    if festivalsonly:
        festivalsonly = "1"
    else:
        festivalsonly = "0"
    url = 'method=geo.getevents&festivalsonly=%s&limit=40' % (festivalsonly)
    if tag:
        url = url + '&tag=%s' % (urllib.quote_plus(tag))  
    if lat:
        url = url + '&lat=%s&long=%s' % (lat,lon)  # &distance=60
    results = GetLastFMData(url)
    try:
        return HandleLastFMEventResult(results)
    except Exception,e:
        log(e)
        log("Error in GetNearEvents()")
        return []

           
def GetVenueEvents(id = ""):
    url = 'method=venue.getevents&venue=%s' % (id)
    log('GetVenueEvents request: %s' % url)
    results = GetLastFMData(url)
    try:
        return HandleLastFMEventResult(results)
    except:
        log("GetVenueEvents: error getting concert data from " + url)
        return []

def GetArtistNearEvents(Artists): # not possible with api 2.0
    ArtistStr = ''
    for art in Artists:
        if len(ArtistStr) > 0:
             ArtistStr = ArtistStr + '&'
        ArtistStr = ArtistStr + 'artists[]=' + urllib.quote(art['name'])     
    url = 'http://api.bandsintown.com/events/search?%sformat=json&location=use_geoip&api_version=2.0&app_id=%s' % (ArtistStr, bandsintown_apikey)
    try:
        response = GetStringFromUrl(url)
        results = simplejson.loads(response)
        return HandleBandsInTownResult(results)
    except:
        log("GetArtistNearEvents: error when getting artist data from " + url)
        return []
