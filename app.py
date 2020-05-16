# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import dateutil.parser
import babel
from flask import Flask, render_template, request
from flask import flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from forms import VenueForm, ArtistForm, ShowForm
from flask_migrate import Migrate
import sys
from datetime import datetime
# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


Shows = db.Table(
  'Shows',
  db.Column(
    'venue_id', db.Integer, db.ForeignKey('Venue.id'), primary_key=True
  ),
  db.Column(
    'artist_id', db.Integer, db.ForeignKey('Artist.id'), primary_key=True
  ),
  db.Column('dateshow', db.DateTime, primary_key=True)
)


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(120)))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    artists = db.relationship(
      'Artist',
      secondary=Shows,
      backref=db.backref('venues', lazy='dynamic')
    )

    # TODO: implement any missing fields, as a database migration using
    # Flask-Migrate


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(120)))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))

    # TODO: implement any missing fields, as a database migration
    # using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships
# and properties, as a database migration.

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming
    #       shows per venue.

    allData = db.session.query(Venue.state, Venue.city).group_by(Venue.state, Venue.city).order_by(Venue.state).all()

    data = []
    allvenues = []

    for d in allData:
        venueCity = Venue.query.filter(Venue.city == d.city, Venue.state == d.state).all()

        for v in venueCity:
            venue = {
                'id': v.id,
                'name': v.name,
                'num_upcoming_shows': db.session.query(Shows).filter(Shows.c.venue_id == v.id, Shows.c.dateshow > datetime.now()).count()
            }
            allvenues.append(venue)

        data.append({
            'city': d.city,
            'state': d.state,
            'venues': allvenues
        })
        allvenues = []

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search.
    # Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and
    # "Park Square Live Music & Coffee"

    data = []

    venues = Venue.query.filter(Venue.name.ilike('%' + request.form['search_term'] + '%')).all()
    for v in venues:
        data.append({
            'id': v.id,
            'name': v.name,
        })
    response = {
        "count": len(data),
        "data": data
    }

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id

    past_shows = []
    upcoming_shows = []

    allData = Venue.query.get(venue_id)
    subQ = db.session.query(Shows).filter(Shows.c.venue_id == venue_id).subquery('subQ')
    Quy = db.session.query(Artist, subQ).join(Artist).all()

    for sh in Quy:

        if sh.dateshow < datetime.now():
            past_shows.append({
                'artist_id': sh.Artist.id,
                'artist_name': sh.Artist.name,
                'artist_image_link': sh.Artist.image_link,
                'start_time': sh.dateshow.strftime("%Y-%m-%d %H:%M:%S")
            })
        else:
            upcoming_shows.append({
                'artist_id': sh.Artist.id,
                'artist_name': sh.Artist.name,
                'artist_image_link': sh.Artist.image_link,
                'start_time': sh.dateshow.strftime("%Y-%m-%d %H:%M:%S")
            })

    data = {
      'id': allData.id,
      'name': allData.name,
      'genres': allData.genres,
      'address': allData.address,
      'city': allData.city,
      'state': allData.state,
      'phone': allData.phone,
      'website': allData.website,
      'facebook_link': allData.facebook_link,
      'seeking_talent': allData.seeking_talent,
      'seeking_description': allData.seeking_description,
      'image_link': allData.image_link,
      'past_shows': past_shows,
      'upcoming_shows': upcoming_shows,
      'past_shows_count': len(past_shows),
      'upcoming_shows_count': len(upcoming_shows)
    }

    # data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    error = False
    try:
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        address = request.form['address']
        phone = request.form['phone']
        image_link = request.form['image_link']
        genres = request.form.getlist('genres')
        facebook_link = request.form['facebook_link']
        website = request.form['website']
        if request.form['seeking_talent'] == 'No':
            seeking_talent = False
        else:
            seeking_talent = True
        seeking_description = request.form['seeking_description']

        venue = Venue(
            name=name,
            city=city,
            state=state,
            address=address,
            phone=phone,
            image_link=image_link,
            genres=genres,
            facebook_link=facebook_link,
            website=website,
            seeking_talent=seeking_talent,
            seeking_description=seeking_description
        )

        db.session.add(venue)
        db.session.commit()
    except Exception:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    else:
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')

    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    error = False
    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
    except Exception:
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue could not be deleted.')
    else:
        # on successful db insert, flash success
        flash('Venue was successfully deleted!')

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return redirect('/')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

    allData = Artist.query.order_by(Artist.id).all()

    data = []

    for a in allData:

        data.append({
            'id': a.id,
            'name': a.name
        })

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    data = []

    artists = Artist.query.filter(Artist.name.ilike('%' + request.form['search_term'] + '%')).all()
    for a in artists:
        data.append({
            'id': a.id,
            'name': a.name,
        })
    response = {
        "count": len(data),
        "data": data
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id

    past_shows = []
    upcoming_shows = []

    allData = Artist.query.get(artist_id)
    subQ = db.session.query(Shows).filter(Shows.c.artist_id == artist_id).subquery('subQ')
    Quy = db.session.query(Venue, subQ).join(Venue).all()

    for sh in Quy:

        if sh.dateshow < datetime.now():
            past_shows.append({
                'venue_id': sh.Venue.id,
                'venue_name': sh.Venue.name,
                'venue_image_link': sh.Venue.image_link,
                'start_time': sh.dateshow.strftime("%Y-%m-%d %H:%M:%S")
            })
        else:
            upcoming_shows.append({
                'venue_id': sh.Venue.id,
                'venue_name': sh.Venue.name,
                'venue_image_link': sh.Venue.image_link,
                'start_time': sh.dateshow.strftime("%Y-%m-%d %H:%M:%S")
            })

    data = {
      'id': allData.id,
      'name': allData.name,
      'genres': allData.genres,
      'city': allData.city,
      'state': allData.state,
      'phone': allData.phone,
      'website': allData.website,
      'facebook_link': allData.facebook_link,
      'seeking_talent': allData.seeking_talent,
      'seeking_description': allData.seeking_description,
      'image_link': allData.image_link,
      'past_shows': past_shows,
      'upcoming_shows': upcoming_shows,
      'past_shows_count': len(past_shows),
      'upcoming_shows_count': len(upcoming_shows)
    }

    # data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    
    artistdetails = Artist.query.get(artist_id)
    form.name.data = artistdetails.name
    form.city.data = artistdetails.city
    form.state.data = artistdetails.state
    form.phone.data = artistdetails.phone
    form.genres.data = artistdetails.genres
    form.image_link.data = artistdetails.image_link
    form.facebook_link.data = artistdetails.facebook_link
    form.website.data = artistdetails.website
    if artistdetails.seeking_talent:
        form.seeking_talent.data = "Yes"
    else:
        form.seeking_talent.data = "No"
    form.seeking_description.data = artistdetails.seeking_description

    
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artistdetails)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    error = False
    try:
        artist = Artist.query.get(artist_id)
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        artist.image_link = request.form['image_link']
        artist.genres = request.form.getlist('genres')
        artist.facebook_link = request.form['facebook_link']
        artist.website = request.form['website']
        if request.form['seeking_talent'] == 'No':
            artist.seeking_talent = False
        else:
            artist.seeking_talent = True
        artist.seeking_description = request.form['seeking_description']
        
        db.session.commit()
    except Exception:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
    else:
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully updated!')


    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = {
        "id": 1,
        "name": "The Musical Hop",
        "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
        "address": "1015 Folsom Street",
        "city": "San Francisco",
        "state": "CA",
        "phone": "123-123-1234",
        "website": "https://www.themusicalhop.com",
        "facebook_link": "https://www.facebook.com/TheMusicalHop",
        "seeking_talent": True,
        "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
        "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
    }
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    error = False
    try:
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        phone = request.form['phone']
        image_link = request.form['image_link']
        genres = request.form.getlist('genres')
        facebook_link = request.form['facebook_link']
        website = request.form['website']
        if request.form['seeking_talent'] == 'No':
            seeking_talent = False
        else:
            seeking_talent = True
        seeking_description = request.form['seeking_description']

        artist = Artist(
            name=name,
            city=city,
            state=state,
            phone=phone,
            image_link=image_link,
            genres=genres,
            facebook_link=facebook_link,
            website=website,
            seeking_talent=seeking_talent,
            seeking_description=seeking_description
        )

        db.session.add(artist)
        db.session.commit()
    except Exception:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    else:
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')

    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.

    allData = db.session.query(Shows).all()
    data = []

    for s in allData:
        venueD = Venue.query.get(s.venue_id)
        artistD = Artist.query.get(s.artist_id)

        data.append({
            'venue_id': s.venue_id,
            'venue_name': venueD.name,
            'artist_id': s.artist_id,
            'artist_name': artistD.name,
            'artist_image_link': artistD.image_link,
            'start_time': s.dateshow.strftime("%Y-%m-%d %H:%M:%S")
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead

    error = False
    try:
        artist_id = request.form['artist_id']
        venue_id = request.form['venue_id']
        dateshow = request.form['start_time']

        show = Shows.insert().values(
            artist_id=artist_id,
            venue_id=venue_id,
            dateshow=dateshow
        )
        db.session.execute(show)
        db.session.commit()
    except Exception:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Show could not be listed.')
    else:
        # on successful db insert, flash success
        flash('Show was successfully listed!')

    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
