import bottle
import requests

import datetime
import os
import sqlite3
import sys

import config

rootdir = os.path.dirname(os.path.realpath(__file__))

@bottle.route('/static/<filename:path>')
def send_static(filename):
    return bottle.static_file(filename, root=os.path.join(rootdir, 'static'))


@bottle.route('/')
def index():

    html = '''
    <html>
        <head>
            <title>WRMS Timeline</title>
            <link rel="stylesheet" type="text/css" href="/static/style.css" />
            <script src="http://code.jquery.com/jquery-1.9.1.min.js"></script>
            <script src="/static/jquery.timeago.js"></script>

            <script>
                jQuery.timeago.settings.strings = {
                    prefixAgo: null,
                    prefixFromNow: null,
                    suffixAgo: "ago",
                    suffixFromNow: "from now",
                    seconds: "Less than a minute",
                    minute: "About a minute",
                    minutes: "%d minutes",
                    hour: "About an hour",
                    hours: "About %d hours",
                    day: "About a day",
                    days: "%d days",
                    month: "About a month",
                    months: "%d months",
                    year: "About a year",
                    years: "%d years",
                    wordSeparator: " ",
                    numbers: []
                };

                jQuery(document).ready(function() {
                    jQuery("abbr.timeago").timeago();
                });
            </script>
        </head>
        <body>
            <a name="top"></a>
    '''

    html += '<ol>'
    data = get_data()
    status = {
        'I':    'In Progress',
        'L':    'Allocated',
        'B':    'Need Info',
        'N':    'New Request',
        'R':    'Reviewed',
        'H':    'On Hold',
        'C':    'Cancelled',
        'F':    'Finished',
        'K':    'Provide Feedback',
        'T':    'Testing/Signoff',
        'Q':    'Quoted',
        'A':    'Quote Approved',
        'D':    'Needs Documenting',
        'S':    'Ready for Staging',
        'P':    'Production Ready',
        'Z':    'Failed Testing',
        'U':    'Catalyst Testing',
        'V':    'QA Approved',
        'W':    'Pending QA',
        'O':    'Ongoing Maintenance',
        'E':    'Development Completed',
        'X':    'Blocked'
    }

    anchor_counts = {}

    request = None
    group = []
    i = 0

    while 1:
        g = None
        while i < len(data):
            g = data[i]
            i += 1
            # Do we add to group?
            if not request or request == g['request_id']:
                request = g['request_id']
                group.append(g)
            else:
                # Group has changed
                break

        first = True
        group.reverse()
        for d in group:
            html += '<li>';
            if first:
                # Generate anchor
                if d['request_id'] not in anchor_counts.keys():
                    anchor_counts[d['request_id']] = 1
                    anchor = '%d_%d' % (d['request_id'], 1)
                    anchor_count = 1
                else:
                    anchor_counts[d['request_id']] += 1
                    anchor_count = anchor_counts[d['request_id']]
                    anchor = '%d_%d' % (d['request_id'], anchor_count)

                html += '<h2>';
                html += '<a name="%s"></a>' % anchor
                html += '<a href="https://wrms.catalyst.net.nz/wr.php?request_id=%d">WR#%d</a> %s <em>(%s)</em>' % \
                            (d['request_id'], d['request_id'], d['brief'], d['status_desc'])

                html += ' <a href="#top" style="float: right;">Top</a>'
                html += ' <a href="#%d_%d" title="Newer WR changes">&uarr;</a>' % (d['request_id'], anchor_count - 1)
                html += ' <a href="#%d_%d" title="Older WR changed">&darr;</a>' % (d['request_id'], anchor_count + 1)

                html += '</h2>'
                first = False

            img_name = d['user'].lower().replace(' ', '_')

            timeoccured = datetime.datetime.fromtimestamp(d['timestamp']).strftime("%Y-%m-%d %H:%M:%S")

            if d['type'] == 'status':
                html += '<h3><abbr class="timeago" title="%s">%s</abbr> <strong>%s</strong> changed the status to "<strong>%s</strong>"</h3>' % \
                            (timeoccured, timeoccured, d['user'], status[d['note']])
            else:
                html += '<h3><abbr class="timeago" title="%s">%s</abbr> <strong>%s</strong> wrote:</h3>' % (timeoccured, timeoccured, d['user'])
                html += '<img alt="&nbsp;" src="http://directory.wgtn.cat-it.co.nz/staff_photos/%s.jpg" />' % img_name
                html += '<div class="content"><p>'+d['note'].replace('\n', '<br>')+'</p></div>'
            html += '</li>'

            last = d

        if not g:
            break

        group = []
        group.append(g)
        request = g['request_id']


    html += '</ol>'
    html += '</body></html>'
    return html


def wrms_load(reporturl):
    host = 'https://wrms.catalyst.net.nz/'
    cookies = {'wrms3_auth': config.secret}
    r = requests.get(host+reporturl, cookies=cookies)
    return r.json


def get_data():
    db_path = os.path.join(rootdir, 'data.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Check if needs setting up
    c.execute('SELECT name FROM sqlite_master WHERE type = ? AND name = ?', ['table', 'wr'])
    if not c.fetchone():
        print 'Setup database...'
        c.execute('''CREATE TABLE wr (request_id integer, brief text, system_code text, system_name text, last_activity integer, status_desc text)''')
        conn.commit()

        c.execute('''CREATE TABLE activity (request_id integer, type text, note text, user text, timestamp integer)''')
        conn.commit()

    # Load latest active WRs
    wrms = wrms_load('api2/report?report_type=request&interested_users=%d&display_fields=request_id,system_name,system_code,last_activity_epoch,status_desc,brief&order_by=last_activity_epoch&order_direction=desc' % config.userid)

    for wr in wrms['response']['results']:
        changed = False

        # Load from DB
        while 1:
            c.execute('SELECT * FROM wr WHERE request_id = ?', [wr['request_id']])
            result = c.fetchone()
            if result:
                wr_db = result
                break
            else:
                print 'Insert %d' % wr['request_id']
                c.execute('INSERT INTO wr VALUES (?, ?, ?, ?, ?, ?)',
                        [wr['request_id'], wr['brief'], wr['system_code'], wr['system_name'], wr['last_activity_epoch'], wr['status_desc']])
                conn.commit()
                changed = True

        # Check if brief changed
        if wr['brief'] != wr_db['brief']:
            changed = True

        if wr['last_activity_epoch'] != wr_db['last_activity']:
            changed = True

        if wr['status_desc'] != wr_db['status_desc']:
            changed = True

        # If changed, update and load activity
        if changed:
            print 'WR#%d %s: %s' % (wr['request_id'], wr['system_name'], wr['brief'])
            print 'Changed...'
            c.execute('UPDATE wr SET request_id = ?, brief = ?, system_code = ?, system_name = ?, last_activity =  ?, status_desc = ? WHERE request_id = ?',
                    [wr['request_id'], wr['brief'], wr['system_code'], wr['system_name'], wr['last_activity_epoch'], wr['status_desc'], wr['request_id']])
            conn.commit()

            # Get newest activity in DB
            c.execute('SELECT MAX(timestamp) FROM activity WHERE request_id = ?', [wr['request_id']])
            result = c.fetchone()
            latest_activity = result[0] if result else 0

            activity = wrms_load('api2/report?request_id=%d&source=note,status&report_type=activity&page_size=200&page_no=1&display_fields=source,request_id,fullname,note,date_epoch&order_by=date_epoch&order_direction=desc' % wr['request_id'])

            for a in activity['response']['results']:
                # Check if new
                if a['date_epoch'] <= latest_activity:
                    continue

                # Insert into DB
                print 'Insert activity for %d' % wr['request_id']
                c.execute('INSERT INTO activity VALUES (?, ?, ?, ?, ?)',
                        [a['request_id'], a['source'], a['note'], a['fullname'], a['date_epoch']])
                conn.commit()


    # Select latest activity
    c.execute('SELECT a.*, wr.* FROM activity a INNER JOIN wr ON a.request_id = wr.request_id ORDER BY a.timestamp DESC LIMIT 200')
    return c.fetchall()


# Seed data
print 'Seed data...'
print '(make take a while if there is significant new activity)'
get_data()
print

bottle.debug(True)
bottle.run(host='localhost', port=8080)
