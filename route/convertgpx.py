import argparse
import csv
import os.path
from haversine import haversine
from lxml import etree

parser = argparse.ArgumentParser()
parser.add_argument('day', type=int, help='The day to process')

def main():
    args = parser.parse_args()

    if os.path.exists(f'day{args.day}.gpx'):
        gpx = etree.parse(f'day{args.day}.gpx')
        trkpts = [(float(n.attrib['lat']), float(n.attrib['lon'])) for n in gpx.findall('.//{http://www.topografix.com/GPX/1/1}trkpt')]
    else:
        part = 1
        trkpts = []
        while os.path.exists(f'day{args.day}pt{part}.gpx'):
            gpx = etree.parse(f'day{args.day}pt{part}.gpx')
            trkpts.extend([(float(n.attrib['lat']), float(n.attrib['lon'])) for n in gpx.findall('.//{http://www.topografix.com/GPX/1/1}trkpt')])
            part += 1

    with open(f'day{args.day}.csv', 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['lat', 'lon', 'dist'])
        csvwriter.writerow([trkpts[0][0], trkpts[0][1], 0])
        total = 0
        for i in range(1, len(trkpts)):
            total += haversine(trkpts[i - 1], trkpts[i], unit='mi')
            csvwriter.writerow([trkpts[i][0], trkpts[i][1], total])

if __name__ == '__main__':
    main()