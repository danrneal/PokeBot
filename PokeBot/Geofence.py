import re
import logging
import sys

log = logging.getLogger('Geofence')


def load_geofence_file(file_path):
    try:
        geofences = []
        name_pattern = re.compile("(?<=\[)([^]]+)(?=\])")
        coor_patter = re.compile(
            "[-+]?[0-9]*\.?[0-9]*" + "[ \t]*,[ \t]*" + "[-+]?[0-9]*\.?[0-9]*"
        )
        with open(file_path, 'r') as f:
            lines = f.read().splitlines()
        name = "geofence"
        points = []
        for line in lines:
            line = line.strip()
            match_name = name_pattern.search(line)
            if match_name:
                if len(points) > 0:
                    geofences.append(Geofence(name, points))
                    points = []
                name = match_name.group(0)
            elif coor_patter.match(line):
                lat, lng = map(float, line.split(","))
                points.append([lat, lng])
            else:
                log.critical((
                    "Geofence was unable to parse this line: {}"
                ).format(line))
                log.critical(
                    "All lines should be either '[name]' or 'lat,lng'."
                )
                sys.exit(1)
        geofences.append(Geofence(name, points))
        return geofences
    except IOError as e:
        log.critical((
            "IOError: Please make sure a file with read/write permissions " +
            "exsist at {}"
        ).format(file_path))
    except Exception as e:
        log.critical((
            "Encountered error while loading Geofence: {}: {}"
        ).format(type(e).__name__, e))
    sys.exit(1)


class Geofence(object):

    def __init__(self, name, points):
        self.__name = name
        self.__points = points
        self.__min_x = points[0][0]
        self.__max_x = points[0][0]
        self.__min_y = points[0][1]
        self.__max_y = points[0][1]
        for p in points:
            self.__min_x = min(p[0], self.__min_x)
            self.__max_x = max(p[0], self.__max_x)
            self.__min_y = min(p[1], self.__min_y)
            self.__max_y = max(p[1], self.__max_y)

    def contains(self, x, y):
        if (self.__max_x < x or
            x < self.__min_x or
            self.__max_y < y or
                y < self.__min_y):
            return False
        inside = False
        p1x, p1y = self.__points[0]
        n = len(self.__points)
        for i in range(1, n+1):
            p2x, p2y = self.__points[i % n]
            if min(p1y, p2y) < y <= max(p1y, p2y) and x <= max(p1x, p2x):
                if p1y != p2y:
                    xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                if p1x == p2x or x <= xinters:
                    inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def get_name(self):
        return self.__name
