# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project (loosely) adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- 

### Changed
- 

### Deprecated
- 

### Removed
- 

### Fixed
- 

### Security
- 

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
