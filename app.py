from wsgiref.handlers import format_date_time
import dateutil.parser
import babel
from flask import (
    Flask, 
    render_template, 
    request, 
    Response, 
    flash, 
    redirect, 
    url_for
)
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate
import sys
from forms import *
from models import  db, Venue, Artist, Show
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migration = Migrate(app, db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime
#----------------------------------------------------------------------------#
# Auxiliar methods.
#----------------------------------------------------------------------------#

def formatRightDate(date):
  return datetime.strptime(format_datetime(date), '%a %m, %d, %Y %H:%M%p')

def isUpcoming(date):
  return date > datetime.now()

def numOfUpcomingShows(shows):
  upComingShows=0
  for show in shows:
    if isUpcoming(show.start_time):
      upComingShows+=1
  return upComingShows

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data=[]
  venues_distinct_city_state = Venue.query.distinct(Venue.city, Venue.state).all()

  for city_state in venues_distinct_city_state:
    venue_dict={
      'city': city_state.city,
      'state': city_state.state,
      'venues': []
    }
    venues = Venue.query.filter_by(city=city_state.city, state= city_state.state).all()
    for venue in venues:
      upComingShows=numOfUpcomingShows(venue.shows)
      venue_dict['venues'].append({
        'id': venue.id,
        'name': venue.name,
        'num_upcoming_shows': upComingShows
      })

    data.append(venue_dict)
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  response={}
  search_term=request.form.get('search_term', '')
  
  venues = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()
  response['count'] = len(venues)
  response['data'] = []
  for venue in venues:
    venueDict={
     'id': venue.id,
     'name': venue.name,
     'num_upcoming_shows': numOfUpcomingShows(venue.shows)
    }
    response['data'].append(venueDict)
    
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  errorMessage=''
  data={}
  if(Venue.query.get(venue_id)) != None:
      venue = Venue.query.get(venue_id)

      data["id"] = venue.id
      data["name"] = venue.name
      data["genres"] = venue.genres
      data["city"] = venue.city
      data["state"] = venue.state
      data["address"] = venue.address
      data["phone"] = venue.phone
      data["website"] = venue.website_link
      data["facebook_link"] = venue.facebook_link
      data["seeking_talent"] = venue.seeking_talent
      data["seeking_description"] = venue.seeking_description
      data["image_link"] = venue.image_link

      data["past_shows"] = []
      data["upcoming_shows"] = []

      for show in venue.shows:
        temp_show = {
            'artist_id': show.artist_id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
        }
        if isUpcoming(show.start_time):
          data["upcoming_shows"].append(temp_show)
        else:
          data["past_shows"].append(temp_show)


      data["past_shows_count"] = len(data["past_shows"])
      data["upcoming_shows_count"] = len(data["upcoming_shows"])
        
  else:
    errorMessage += 'Show Not found'  
    flash(errorMessage)
    return render_template('pages/home.html')
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form)
  try:
    if form.validate_on_submit():
      venue = Venue()
      form.populate_obj(venue)
      db.session.add(venue)
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
      return render_template('pages/home.html')
    else:
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.' + 
      'Please, fill all the fields correctly')
    return render_template('forms/new_venue.html', form=form)
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    print(sys.exc_info())
    return render_template('forms/new_venue.html', form=form) 
  finally:
    db.session.close()

@app.route('/venues/<venue_id>', methods=['POST'])
def delete_venue(venue_id):
  try:
    db.session.delete(Venue.query.get(venue_id))
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return render_template("pages/home.html")

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists', methods=['GET'])
def artists():
  data = Artist.query.with_entities(Artist.id, Artist.name).all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  response={}
  search_term=request.form.get('search_term', '')

  artists = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()
  response['count'] = len(artists)
  response['data'] = []
  for artist in artists:
    artistDict={
     'id': artist.id,
     'name': artist.name,
     'num_upcoming_shows': numOfUpcomingShows(artist.shows)
    }
    response['data'].append(artistDict)
    
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  errorMessage=''
  data={}
  if(Artist.query.get(artist_id)) != None:
      artist = Artist.query.get(artist_id)
      
      data["id"] = artist.id
      data["name"] = artist.name
      data["genres"] = artist.genres
      data["city"] = artist.city
      data["state"] = artist.state
      data["phone"] = artist.phone
      data["seeking_venue"] = artist.seeking_venue
      data["image_link"] = artist.image_link
      data["facebook_link"] = artist.facebook_link
      data["website"] = artist.website_link
      data["seeking_description"] = artist.seeking_description

      data["past_shows"] = []
      data["upcoming_shows"] = []
      for show in artist.shows:
        venue = show.venue
        venueDic ={
          "venue_id": venue.id,
          "venue_name": venue.name,
          "venue_image_link": venue.image_link,
          "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        }
        if isUpcoming(show.start_time):
          data["upcoming_shows"].append(venueDic)
        else:
          data["past_shows"].append(venueDic)

      data["past_shows_count"] = len(data["past_shows"])
      data["upcoming_shows_count"] = len(data["upcoming_shows"])
        
  else:
    errorMessage += 'Artist Not found'  
    flash(errorMessage)
    return render_template('pages/home.html')
  return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm()
  try:
    if form.validate_on_submit():
      artist = Artist.query.get(artist_id)
      form.populate_obj(artist)
      db.session.add(artist)
      
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully updated!')
      return redirect(url_for('show_artist', artist_id=artist_id))
    else:
       flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.' + 
       'Please, fill all the fields correctly')
    return render_template('pages/home.html')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
    print(sys.exc_info())
    return render_template('pages/home.html') 
  finally:
    db.session.close()
 

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm(request.form)

  try:
    if form.validate_on_submit():
      venue = Venue.query.get(venue_id)
      form.populate_obj(venue)
      db.session.add(venue)
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully updated!')
      return redirect(url_for('show_venue', venue_id=venue_id))
    else:
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.' + 
      'Please, fill all the fields correctly')
    return render_template('pages/home.html')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
    print(sys.exc_info())
    return render_template('pages/home.html')
  finally:
    db.session.close()

  

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm(request.form)
  try:
    if form.validate_on_submit():

      artist = Artist()
      form.populate_obj(artist)
      db.session.add(artist)

      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
      return render_template('pages/home.html', form=form)
    else:
       flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.' + 
       'Please, fill all the fields correctly')
    return render_template('forms/new_artist.html', form=form)
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    print(sys.exc_info())
    return render_template('forms/new_artist.html', form=form) 
  finally:
    db.session.close()

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data = []
  shows = Show.query.all()
  for show in shows:
    showDict={
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    }
    data.append(showDict)
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm(request.form)
  errorMessage=''
  try:
    error=False
    artist_id = form.artist_id.data
    venue_id = form.venue_id.data
    start_time= form.start_time.data
    
    if form.validate_on_submit():
      if Artist.query.get(artist_id) != None:
        if Venue.query.get(venue_id) != None:
           show = Show(artist_id = artist_id, venue_id=venue_id, start_time=start_time)
           db.session.add(show)
           db.session.commit()
           flash('Show was successfully listed!')
           return render_template('pages/home.html')
        else:
          error=True
          errorMessage += 'Venue does not exist'
      else:
        error=True
        errorMessage+='Artist does not exist'
    else:
       flash('Check the fields!')
       return render_template('forms/new_show.html', form=form)
  except:
    db.session.rollback()
    flash('An error occurred. Show for artist' + request.form['artist_id'] + ' could not be listed.')
    print(sys.exc_info())
    return render_template('pages/home.html')
  finally:
    db.session.close()
    if error:
      flash(errorMessage)
      return render_template('forms/new_show.html', form=form)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500

app.register_error_handler(404, not_found_error)
app.register_error_handler(500, server_error)


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
