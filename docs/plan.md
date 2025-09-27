# FLBB Statistics

## Goal

Visualize data about:

- divison
- team
- player

Visualization has to be available through web browser.

## Next steps

completed - 1. Regenerate json output files (data records) - execute extract-games.ps1 - maybe refactor is required
2. Prepare csv file based on json files in Tableau Desktop - data source for Tableau
3. Prepare Tableau workbook to be published
4. Send combined csv to GDrive
5. Publish Tableau workbook for desktop users in Tableau Public (visualizations might not be displayed correctly on mobile)
6. Look for tasks

## Tasks

### Collect raw HTML for list of categories

All [categories](https://www.luxembourg.basketball/c/categorie/all) are defined

### Collect raw HTML for each category

Category have list of games associated (e.g. [Division 2](https://www.luxembourg.basketball/c/calendrier-resultat/160/division-2-hommes))

### Collect raw HTML for each game

Game have list of events/player associated (e.g. [Game 17003](https://www.luxembourg.basketball/match/17003/2023-09-30/telstar-hesperange-e/telstar-hesperange-b/division3-hommes))

### Scrap local raw HTML pages and transform to data records

Parse raw html pages for games and translate them into json files.
One json file represents one game.

### Create data source based on data records

Combine all json files to create a data source.

Tableau has a capability to use multiple json files and combine them all together as one data source.
Unfortunately, Tableau public do not accept files in other format than csv residing in Google Drive.

Q: How to combine json files into more friendly format?

A1: use sqlite
A2: create a big json file
A3: create db in other format
A4: use python
1. use pandas in python
2. load json file into dataframe
3. save as csv file 

### Create visualizations based on data source

### Publish visualizations to public

## Tools

### File storage

File are downloaded on machine which executes scraping of data.

Q: Where to store data source?

A1: process manually on local machine, use Tableau to combine them into csv file and upload to GDrive
A2: invoke scraping of data on GHA and upload them to GDrive or some other place which would be accessible for Tableau

### Visualizations

Visualizations can be done with Tableau Public.

Q: How to publish newly created report from Tableau Desktop?
Q: Is it possible to avoid recreating reports on Tableau web?
Q: Is it possible to design report on Tableau Desktop and publish it?
Q: What are the other tools which could be used?

### Scripts

Script are written in Powershell.

There are two main scripts:

1. download-controller.ps1 - use to manage to scrap data from flbb site
2. extract-game.ps1 - used for transformation html files into json files (data records)

Q: Any other better alternative? Python?

## Current state

1. Download-controller.ps1 script is able to:

    - download all html files
    - create two json databases with gamesDB.json and gameScheduleDB.json
    - compress all files into one zip file

2. extract-games.ps1:

    - parse all html files and create json file for each file

3. Tableau:

    - takes all json file as input and compile into Data Source for reports
    - reports are refreshed

4. Publishing:

    - take screenshot from Tableau visualizations
    - send to WhatsApp group

### what is missing

1. Refactor extract-games.ps1:

    - remove code related to download html
    - use of gamesDB.json and gamesScheduleDB.json for processing
    - try to add function to merging all json files into one json

2. Convert json file into csv (csv format can be used in Tableau+GDrive)

    - create multiple files (similar to relational database):
        - teams
        - players
        - games
        - events in game

3. Move visualization from Tableau Desktop to Tableau Web version

4. Create better version for published reports

5. Add logo of club to report
