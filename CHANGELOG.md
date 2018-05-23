# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project (loosely) adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).


## [Unreleased] - 2018-05-22 [LAST UPDATE]
### Added
- Emoji selector for status updates
- Emoticon selector for status updates
- @Mentions for status updates

### Changed
- Status update text boxes are now textareas (multiline) (shift+enter for line break)
- Caching member lookup for @mentions

### Deprecated
- Item

### Removed
- Item

### Fixed
- Item

### Security
- Item

## [Prerelease 6] - 2018-05-20
### Added
- Meta description and author as configurables
- Customizable smilies listing that can be used across the site (just use a : )
- A working swear filter
- Profile visitors are counted
- Re-added the old import scripts for ipb 3.x (they probably don't work, but they're likely a good example)
- Added emoji support throughout the site (just use a :: or an emoji keyboard)
- Celery is now used for background tasks (will need documentation on this)
- Working @ mentions

### Changed
- Recent posts now only shows one most recent post per thread
- Roles can be marked as "displaying inline" for certain users, giving logged in user styling (configurable)
- The name of the site is now configurable
- Email addresses can now be used to login
- Categories can be marked to automatically follow them for all new users
- Roles can be prioritized
- Messages left on profiles no longer alert all of a user's followers

### Deprecated
- We are now only compatible with Python 3.x
- Admin site is now at /staff/
- Updated all Flask-related and other Python dependencies

### Fixed
- Ban page now shows no images if there are no images to show (rather than a broken image)
- Restored all admin links
- Changed "says" to "said" for status comments
- Fixed the "initial setup" script so that it actually works

## [Prerelease 5] - 2018-05-09
### Added
- Topic creation via RSS feed reader
- Embeddable iframe view for RSS comments

### Changed
- Renamed woe module to lamia, finally

### Fixed
- Relinked moderation features to the frontend

### Security
- Minimum character limit added for searches
- Search frequency is now limited to 1 search per X minutes
- Hardcoded limit of 50K characters established for posts, etc

## [Prerelease 4] - 2018-04-15
### Added
- Full permissions system for categories
- Standard administrator panel
- Standard mod panel with reports
- Site configuration panel
- Drag and drop category ordering in admin interface
- Workflow for reports screen
- Tied in postgresql full text search for posts
- Import scripts for Burning Board posts, topics, users, signatures
- Added a theme to the admin interface and made other visual improvements

### Changed
- Dramatically improved bbcode parsing and compatibility
- Improved queries across the site, generally increasing performance
- Visual improvements to search page
- Subcategories on front page and improvements to category/subcategory hiding
- Notification grouping now works across the site and is a bit more aggressive on the dashboard
- Made themes configurable and template files overridable
- Improvement in category topic listing speed

### Deprecated
- Using user urls instead of login names for addresses (login name is now pretty useless)

### Removed
- Removed hard coded attributes and pages
- Nuked the old administration panel

### Fixed
- Numerous improvements and modifications to default theme

### Security
- Tweaked the key used for real time communications

## [Original Codebase] - 2017-08-15
### Added
- Forum features
- Blog features
- Forum roleplay features
- Status update features
- User profile features

-------

## [VERSION] - YYYY-MM-DD [TEMPLATE]
### Added
- Item

### Changed
- Item

### Deprecated
- Item

### Removed
- Item

### Fixed
- Item

### Security
- Item
