#!/usr/bin/python3
# Modified from code at:
# http://code.activestate.com/recipes/543270-disk-space-usage-displayed-as-a-tree/
"""
Disk space usage displayed as a tree - pydu.py
Copyright (C) 2010  Sol Jerome

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import getopt
import os
import sys

from os.path import isdir, islink

bool_strings = ['off', 'on']


class Options:
    """Holds program options as object attributes"""

    def __init__(self):
        # When adding a new option, initialize it here.
        self.max_depth = 2
        self.show_files = False
        self.indent_size = 2
        self.follow_links = False


def get_indent_str(depth, is_dir, options, last_item):
    s = ''
    depthlength = len(range(depth))
    for i, j in enumerate(range(depth)):
        if last_item and ((i+1) == depthlength):
            # last item in the directory list
            first_char = "`"
        else:
            first_char = "|"
        if is_dir and j == depth - 1:
            other_chars = "--"
        else:
            other_chars = "   "
        s += first_char + (other_chars * (options.indent_size - 1))
    return s


def print_path(path, bytes, pct, is_dir, depth, options, last_item):
    indent_str = get_indent_str(depth, is_dir, options, last_item)
    if path:
        print("%s%- 11.1f %3.0f%% %s" % \
             (indent_str, bytes / 1000, pct, path))
    else:
        print(indent_str)


def is_dir(item):
    """
    Directories have 3 entries (size, path, list of contents) while files
    have 2 (size, path).
    """
    return len(item) == 3


def print_dir(path, dsize, pct, items, depth, options, last_item=False):
    """Print entire tree starting with given directory"""
    print_path(path, dsize, pct, True, depth, options, last_item)
    dir = True
    dirsize = len(items)
    for index, item in enumerate(items):
        size = item[0]
        path = item[1]
        dir = is_dir(item)
        if dsize > 0:
            pct = size * 100.0 / dsize
        else:
            pct = 0.0
        if dir:
            dir_contents = item[2]
            if (index+1) == dirsize:
                # last item in the directory, use '`' character
                print_dir(path, size, pct, dir_contents, depth+1, options, True)
            else:
                print_dir(path, size, pct, dir_contents, depth+1, options)
        else:
            if (index+1) == dirsize:
                print_path(path, size, pct, False, depth+1, options, True)
            else:
                print_path(path, size, pct, False, depth+1, options, False)


def dir_size(dir_path, depth, options):
    """
    For given directory, returns the list [size, [entry-1, entry-2, ...]]
    """
    total = 0
    try:
        dir_list = os.listdir(dir_path)
    except:
        if isdir(dir_path):
            print("Cannot list directory %s" % dir_path)
        return 0
    item_list = []
    for item in dir_list:
        path = "%s/%s" % (dir_path, item)
        try:
            stats = os.stat(path)
        except:
            print("Cannot stat %s" % path)
            continue
        size = stats[6]
        if isdir(path) and (options.follow_links or \
           (not options.follow_links and not islink(path))):
            dsize, items = dir_size(path, depth+1, options)
            size += dsize
            if (options.max_depth == -1 or depth < options.max_depth):
                item_list.append([size, item, items])
        elif options.show_files:
            if (options.max_depth == -1 or depth < options.max_depth):
                item_list.append([size, item])
        total += size
    # Sort in descending order
    item_list.sort()
    item_list.reverse()

    # Keep only the items that will be displayed
    for i, v in enumerate(item_list):
        size = v[0]
        path = v[1]

    return [total, item_list]


def usage(name):
    """Print out usage information"""
    options = Options()
    print("""\
Usage: %s [-d depth] [-f on|off] [-i indent-size] [-l on|off] dir [dir...]
    -d    Max depth of directories. '-d any' => no limit. (default = %d)
    -f    Show files (default = %s)
    -i    Indent size (default = %d)
    -l    Follow symbolic links (Unix only. default = %s)
""" % (name, options.max_depth,
     bool_strings[options.show_files], options.indent_size,
     bool_strings[options.follow_links]))

# main program
if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "d:f:i:l:")
    except getopt.GetoptError:
        usage(sys.argv[0])
        sys.exit(1)

    options = Options()
    errmsg = ''
    for o, a in opts:
        if o == "-d":
            if a == "any":
                options.max_depth = -1
            else:
                try:
                    options.max_depth = int(a)
                except:
                    errmsg = "Invalid value for depth"
                else:
                    if options.max_depth < 0 and options.max_depth != -1:
                        errmsg = "Max depth must be >= 0 or -1"
        elif o == "-f":
            if a == "on":
                options.show_files = True
            elif a == "off":
                options.show_files = False
            else:
                errmsg = "Invalid value for -f"
        elif o == "-i":
            try:
                options.indent_size = int(a)
            except:
                errmsg = ("Invalid value for indent size (you said %s)" % \
                           options.indent_size)
            else:
                if options.indent_size < 2:
                    errmsg = "Indent size must be at least 2"
        elif o == "-l":
            if a == "on":
                options.follow_links = True
            elif a == "off":
                options.follow_links = False
            else:
                errmsg = "Invalid value for -l"

    if errmsg:
        print(errmsg)
        sys.exit(1)

    if len(args) < 1:
        usage(sys.argv[0])
        sys.exit(1)
    else:
        paths = args

    for path in paths:
        print("Disk usage for directory %s:" % path)
        if isdir(path):
            dsize, items = dir_size(path, 0, options)
            print_dir(path, dsize, 100.0, items, 0, options)
        else:
            print("Error:", path, "is not a directory")
